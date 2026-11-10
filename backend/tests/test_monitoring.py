"""A deterministic monitor must not equate healthy HTTP with live capacity."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.monitoring import MonitorState, acknowledge, observe, probe, send_alert
from app.settings import Settings

NOW = datetime(2026, 11, 10, tzinfo=UTC)


def test_resting_is_expected_unless_live_capacity_is_required() -> None:
    state, alert = observe(MonitorState(), "resting", NOW, expect_inference=False)
    assert alert is None
    state, alert = observe(state, "resting", NOW, expect_inference=True)
    assert alert is None
    state, alert = observe(state, "resting", NOW, expect_inference=True)
    assert alert is not None and alert.event == "resting"


def test_outage_debounce_delivery_dedup_recovery_and_cooldown() -> None:
    state, alert = observe(MonitorState(), "unavailable", NOW)
    assert alert is None
    state, alert = observe(state, "unavailable", NOW + timedelta(seconds=1))
    assert alert is not None
    # Failed notifier is not acknowledged: next check must retry the pending alert.
    retry_state, retry = observe(state, "unavailable", NOW + timedelta(seconds=2))
    assert retry is not None
    state = acknowledge(retry_state, retry)
    state, alert = observe(state, "unavailable", NOW + timedelta(minutes=20))
    assert alert is None
    state, alert = observe(state, "ready", NOW + timedelta(minutes=21))
    assert alert is not None and alert.event == "recovered"
    state = acknowledge(state, alert)
    state, _ = observe(state, "unavailable", NOW + timedelta(minutes=22))
    state, alert = observe(state, "unavailable", NOW + timedelta(minutes=23))
    assert alert is None
    _, alert = observe(state, "unavailable", NOW + timedelta(minutes=40))
    assert alert is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,body,expected",
    [
        (200, {"status": "ok", "ready": True, "assistant_state": "resting"}, "resting"),
        (200, {"status": "ok", "ready": True, "assistant_state": "ready"}, "ready"),
        (
            200,
            {"status": "ok", "ready": False, "assistant_state": "ready"},
            "unavailable",
        ),
        (200, {"status": "ok", "ready": True}, "unavailable"),
        (503, {}, "unavailable"),
    ],
)
async def test_probe_uses_http_and_schema(
    status: int, body: dict[str, object], expected: str
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(status, json=body))
    ) as client:
        assert await probe(client, "https://portfolio.test/api/health") == expected


@pytest.mark.asyncio
async def test_probe_bounds_body_and_does_not_echo_errors() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, content=b"private-secret" * 1000)
        )
    ) as client:
        assert await probe(client, "https://portfolio.test/api/health") == "unavailable"
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                302, headers={"location": "https://private.invalid"}
            )
        )
    ) as client:
        assert await probe(client, "https://portfolio.test/api/health") == "unavailable"


@pytest.mark.asyncio
async def test_webhook_payload_is_fixed_metadata_and_failures_propagate() -> None:
    _, alert = observe(
        MonitorState(consecutive=1, observed="unavailable"), "unavailable", NOW
    )
    assert alert is not None
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await send_alert(client, "https://notify.test/secret-path", alert)
    assert len(requests) == 1
    assert b"secret-path" not in requests[0].content
    assert set(__import__("json").loads(requests[0].content)) == {
        "service",
        "event",
        "at",
    }


@pytest.mark.asyncio
async def test_discord_adapter_sends_safe_content_without_mentions() -> None:
    import json

    _, alert = observe(
        MonitorState(consecutive=1, observed="unavailable"), "unavailable", NOW
    )
    assert alert is not None
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(204)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await send_alert(client, "https://discord.test/secret", alert, format="discord")
    payload = json.loads(requests[0].content)
    assert payload["allowed_mentions"] == {"parse": []}
    assert (
        payload["content"]
        == "Portfolio assistant: unavailable at 2026-11-10T00:00:00+00:00."
    )
    assert "secret" not in payload["content"]


def test_optional_alert_settings_are_validated_and_secret() -> None:
    assert Settings(_env_file=None).ALERT_WEBHOOK_URL.get_secret_value() == ""
    with pytest.raises(ValueError):
        Settings(_env_file=None, ALERT_WEBHOOK_URL="http://unsafe.test/token")
    configured = Settings(
        _env_file=None, ALERT_WEBHOOK_URL="https://notify.test/private-token"
    )
    assert "private-token" not in repr(configured)


def test_naive_monitor_checkpoint_fails_validation() -> None:
    with pytest.raises(ValueError):
        MonitorState(last_sent=datetime(2026, 11, 10))


@pytest.mark.asyncio
async def test_cli_persists_failed_delivery_then_retries_without_secret_output(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    import argparse

    from app import monitoring

    original_client = httpx.AsyncClient
    posts: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            posts.append(request)
            return httpx.Response(503 if len(posts) == 1 else 204)
        return httpx.Response(503, text="private-response-sentinel")

    monkeypatch.setattr(
        monitoring.httpx,
        "AsyncClient",
        lambda **kw: original_client(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setattr(
        monitoring,
        "get_settings",
        lambda: Settings(
            _env_file=None, ALERT_WEBHOOK_URL="https://notify.test/private-webhook"
        ),
    )
    path = tmp_path / "monitor.json"
    args = argparse.Namespace(
        url="https://portfolio.test/api/health",
        state=path,
        send=True,
        expect_inference=False,
    )
    assert await monitoring.run(args) == 1
    assert await monitoring.run(args) == 2
    assert MonitorState.model_validate_json(path.read_text()).last_sent is None
    assert await monitoring.run(args) == 1
    assert MonitorState.model_validate_json(path.read_text()).last_sent is not None
    assert len(posts) == 2
    assert not path.with_suffix(".lock").exists()
    output = capsys.readouterr().out
    assert "private-" not in output
