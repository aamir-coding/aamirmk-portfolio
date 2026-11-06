from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.safety.quota import get_quota_guard
from app.settings import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing isolated settings for test runs."""
    return Settings(
        ENVIRONMENT="test",
        DEBUG=True,
        CORS_ORIGINS=["http://localhost:5173", "https://portfolio.test"],
    )


@pytest.fixture(autouse=True)
def reset_safety_state(test_settings: Settings) -> Generator[None]:
    """Ensure in-memory safety rate limits and quotas are clean for each test."""
    quota = get_quota_guard(settings=test_settings)
    quota.reset()
    yield
    quota.reset()


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient]:
    """Synchronous test client fixture bound to fresh app instance."""
    app = create_app(settings=test_settings)
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
