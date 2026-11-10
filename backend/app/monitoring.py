"""External, provider-free health monitor. Dry run unless --send is explicit."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError

from app.settings import get_settings

State = Literal["ready", "resting", "unavailable"]


class HealthProbe(BaseModel):
    status: Literal["ok"]
    ready: Literal[True]
    assistant_state: Literal["ready", "resting"]


class MonitorState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target: str = ""
    observed: State = "ready"
    consecutive: int = Field(default=0, ge=0, le=2)
    notified: State = "ready"
    last_sent: AwareDatetime | None = None


class Alert(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: Literal["portfolio-assistant"] = "portfolio-assistant"
    event: Literal["unavailable", "resting", "recovered"]
    at: datetime


def observe(
    state: MonitorState,
    observation: State,
    now: datetime,
    *,
    expect_inference: bool = False,
) -> tuple[MonitorState, Alert | None]:
    """Debounce incidents twice, deduplicate delivered state, recover immediately."""
    effective: State = (
        "ready" if observation == "resting" and not expect_inference else observation
    )
    count = min(2, state.consecutive + 1) if state.observed == effective else 1
    updated = state.model_copy(update={"observed": effective, "consecutive": count})
    if effective == state.notified or (effective != "ready" and count < 2):
        return updated, None
    if effective != "ready" and state.last_sent is not None:
        if (now - state.last_sent).total_seconds() < 900:
            return updated, None
    return updated, Alert(
        event="recovered" if effective == "ready" else effective, at=now
    )


def acknowledge(state: MonitorState, alert: Alert) -> MonitorState:
    return state.model_copy(
        update={
            "notified": "ready" if alert.event == "recovered" else alert.event,
            "last_sent": alert.at,
        }
    )


async def probe(client: httpx.AsyncClient, url: str) -> State:
    try:
        async with asyncio.timeout(90):
            async with client.stream("GET", url, follow_redirects=False) as response:
                if response.status_code != 200:
                    return "unavailable"
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(body) + len(chunk) > 8192:
                        return "unavailable"
                    body.extend(chunk)
                health = HealthProbe.model_validate_json(bytes(body))
                return health.assistant_state
    except (httpx.HTTPError, TimeoutError, ValueError):
        return "unavailable"


def https_url(value: str) -> str:
    url = urlsplit(value)
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username is not None
        or url.password is not None
        or url.fragment
    ):
        raise ValueError("An HTTPS URL without userinfo or fragment is required")
    return value


async def send_alert(
    client: httpx.AsyncClient,
    url: str,
    alert: Alert,
    *,
    format: Literal["generic", "discord"] = "generic",
) -> None:
    payload = (
        {
            "content": f"Portfolio assistant: {alert.event} at {alert.at.isoformat()}.",
            "allowed_mentions": {"parse": []},
        }
        if format == "discord"
        else alert.model_dump(mode="json")
    )
    async with asyncio.timeout(10):
        async with client.stream(
            "POST",
            https_url(url),
            json=payload,
            follow_redirects=False,
            timeout=10,
        ) as response:
            response.raise_for_status()


async def run(args: argparse.Namespace) -> int:
    url = https_url(args.url)
    if urlsplit(url).query:
        raise ValueError("Health URLs must not contain query parameters")
    target = hashlib.sha256(f"{url}|{args.expect_inference}".encode()).hexdigest()
    path: Path = args.state
    # A crashed/concurrent monitor never silently resets delivery state.
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(".lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        state = (
            MonitorState.model_validate_json(path.read_text(encoding="utf-8"))
            if path.exists()
            else MonitorState(target=target)
        )
        if state.target != target:
            raise ValueError("Monitor state belongs to a different target or policy")
        async with httpx.AsyncClient(timeout=90, trust_env=False) as client:
            observation = await probe(client, url)
            state, alert = observe(
                state,
                observation,
                datetime.now(UTC),
                expect_inference=args.expect_inference,
            )
            failed = False
            if alert is not None and args.send:
                settings = get_settings()
                webhook = settings.ALERT_WEBHOOK_URL.get_secret_value()
                try:
                    await send_alert(
                        client, webhook, alert, format=settings.ALERT_WEBHOOK_FORMAT
                    )
                except (httpx.HTTPError, TimeoutError, ValueError):
                    failed = True
                else:
                    state = acknowledge(state, alert)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(state.model_dump_json() + "\n", encoding="utf-8")
            temporary.replace(path)
            # No remote body, URL, exception message or credential is ever printed.
            print(
                {
                    "observation": observation,
                    "event": alert.event if alert else None,
                    "delivery": "failed"
                    if failed
                    else "sent"
                    if alert and args.send
                    else "dry-run",
                }
            )
            return (
                2
                if failed
                else int(
                    observation == "unavailable"
                    or (args.expect_inference and observation == "resting")
                )
            )
    finally:
        os.close(descriptor)
        lock.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--expect-inference", action="store_true")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    try:
        code = asyncio.run(run(args))
    except (OSError, ValueError, ValidationError):
        print("Monitor configuration/state unavailable; no delivery acknowledged.")
        code = 2
    raise SystemExit(code)


if __name__ == "__main__":
    main()
