"""Operator controls cannot spend, disclose or reuse capacity without authority."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.main import create_app
from app.safety.admission import Allowance
from app.settings import Settings

TOKEN = "test-operator-" + "x" * 43
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture
def ops() -> TestClient:
    return TestClient(create_app(Settings(_env_file=None, OPS_TOKEN=SecretStr(TOKEN))))


def grant(client: TestClient, **changes: object) -> dict[str, object]:
    now = datetime.now(UTC)
    return (
        Allowance(
            boot_id=client.app.state.llm.ledger.boot_id,
            verified_at=now,
            expires_at=min(
                now + timedelta(minutes=5), now.replace(hour=23, minute=59, second=59)
            ),
            requests=2,
            tokens=1000,
        ).model_dump(mode="json")
        | changes
    )


def test_operator_disabled_by_default(client: TestClient) -> None:
    assert client.get("/api/ops/inference", headers=AUTH).status_code == 404


def test_auth_and_origin_are_required_before_disclosure(ops: TestClient) -> None:
    for headers in (
        {},
        {"Authorization": "Bearer wrong"},
        AUTH | {"Origin": "https://portfolio.test"},
    ):
        response = ops.get("/api/ops/inference", headers=headers)
        assert response.status_code == 401
        assert ops.app.state.llm.ledger.boot_id not in response.text
    response = ops.get("/api/ops/inference", headers=AUTH)
    assert response.status_code == 200
    assert response.json()["boot_id"] == ops.app.state.llm.ledger.boot_id
    assert response.headers["cache-control"] == "no-store"
    assert TOKEN not in response.text


def test_fresh_one_shot_grant_preserves_cooldown(ops: TestClient) -> None:
    payload = grant(ops)
    response = ops.post("/api/ops/inference", headers=AUTH, json=payload)
    assert response.status_code == 200
    assert response.json()["reason"] == "minute_capacity"
    assert response.json()["attempts"] == 0
    assert ops.post("/api/ops/inference", headers=AUTH, json=payload).status_code == 409


@pytest.mark.parametrize(
    "changes",
    [
        {"boot_id": "another-process"},
        {"verified_at": (datetime.now(UTC) - timedelta(minutes=2)).isoformat()},
        {"requests": 10000000},
        {"tokens": 10000000},
    ],
)
def test_invalid_grant_does_not_open_ledger(
    ops: TestClient, changes: dict[str, object]
) -> None:
    response = ops.post("/api/ops/inference", headers=AUTH, json=grant(ops, **changes))
    assert response.status_code == 409
    assert ops.app.state.llm.ledger.snapshot().reason == "allowance_unknown"


def test_restart_cannot_reuse_prior_boot_grant(ops: TestClient) -> None:
    other = TestClient(create_app(Settings(_env_file=None, OPS_TOKEN=TOKEN)))
    assert (
        other.post("/api/ops/inference", headers=AUTH, json=grant(ops)).status_code
        == 409
    )


def test_ambiguous_auth_is_denied_and_attempts_are_bounded(ops: TestClient) -> None:
    assert (
        ops.get(
            "/api/ops/inference",
            headers=[
                ("Authorization", f"Bearer {TOKEN}"),
                ("Authorization", f"Bearer {TOKEN}"),
            ],
        ).status_code
        == 401
    )
    statuses = [ops.get("/api/ops/inference").status_code for _ in range(35)]
    assert 429 in statuses
    assert ops.get("/api/ops/inference", headers=AUTH).status_code == 200


def test_control_has_no_public_schema_or_cache(ops: TestClient) -> None:
    assert "/api/ops/inference" not in ops.get("/openapi.json").text
    assert ops.get("/api/ops/inference").headers["cache-control"] == "no-store"
    oversized = ops.post("/api/ops/inference", headers=AUTH, content=b"x" * 65537)
    assert oversized.status_code == 413
    assert oversized.headers["cache-control"] == "no-store"


def test_operator_token_validation_and_redaction() -> None:
    with pytest.raises(ValueError):
        Settings(_env_file=None, OPS_TOKEN="short")
    assert TOKEN not in repr(Settings(_env_file=None, OPS_TOKEN=TOKEN))


def test_invalid_operator_settings_do_not_print_credentials() -> None:
    for key, value in {
        "OPS_TOKEN": "short-private-sentinel",
        "ALERT_WEBHOOK_URL": "http://notify.invalid/private-webhook-sentinel",
    }.items():
        with pytest.raises(ValueError) as error:
            Settings(_env_file=None, **{key: value})
        assert value not in str(error.value)
