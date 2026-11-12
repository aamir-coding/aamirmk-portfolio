import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app
from app.settings import Settings

TOKEN = "a" * 43


def test_admin_cannot_reuse_operator_credential() -> None:
    with pytest.raises(ValidationError, match="credentials must be distinct"):
        Settings(_env_file=None, ADMIN_TOKEN=TOKEN, OPS_TOKEN=TOKEN)


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [("Authorization", "Bearer wrong")],
        [("Authorization", f"Bearer {TOKEN}")] * 2,
    ],
)
def test_admin_requires_one_valid_bearer(headers: list[tuple[str, str]]) -> None:
    app = create_app(Settings(_env_file=None, ENVIRONMENT="test", ADMIN_TOKEN=TOKEN))
    response = TestClient(app).get("/api/admin/dashboard", headers=headers)
    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_admin_requires_storage_even_with_authorization() -> None:
    app = create_app(
        Settings(_env_file=None, ENVIRONMENT="test", ADMIN_TOKEN=TOKEN, DATABASE_URL="")
    )
    response = TestClient(app).get(
        "/api/admin/dashboard", headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"


def test_unconfigured_admin_is_disabled() -> None:
    app = create_app(Settings(_env_file=None, ENVIRONMENT="test", ADMIN_TOKEN=""))
    response = TestClient(app).get("/api/admin/dashboard")
    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"
