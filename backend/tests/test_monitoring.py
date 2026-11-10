"""A deterministic monitor must not equate healthy HTTP with live capacity."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.monitoring import MonitorState, acknowledge, observe, probe, send_alert

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
