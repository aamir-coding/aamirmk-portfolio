import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings


@pytest.fixture
def summary_client() -> TestClient:
    return TestClient(
        create_app(Settings(_env_file=None, ENVIRONMENT="test", DATABASE_URL=""))
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"project_ids": ["invalid-project"]},
        {"messages": [{"content": "PRIVATE-MESSAGE"}]},
        {"jd_text": "PRIVATE-JD"},
        {"project_ids": ["entropy-oj"] * 5},
    ],
)
def test_summary_rejects_unapproved_input(
    summary_client: TestClient,
    payload: dict[str, object],
) -> None:
    response = summary_client.post("/api/summary", json=payload)
    assert response.status_code == 422
    assert "PRIVATE-" not in response.text
    assert response.headers["Cache-Control"] == "no-store"


def test_summary_requires_storage(summary_client: TestClient) -> None:
    response = summary_client.post("/api/summary", json={"project_ids": []})
    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"


def test_invalid_summary_link_is_uncached_and_not_indexable(
    summary_client: TestClient,
) -> None:
    response = summary_client.get("/api/summary/not-a-share-token")
    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Robots-Tag"] == "noindex, nofollow"
    assert response.headers["Referrer-Policy"] == "no-referrer"
