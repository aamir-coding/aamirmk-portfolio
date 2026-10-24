from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing isolated settings for test runs."""
    return Settings(
        ENVIRONMENT="test",
        DEBUG=True,
        CORS_ORIGINS=["http://localhost:5173", "https://portfolio.test"],
    )


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient]:
    """Synchronous test client fixture bound to fresh app instance."""
    app = create_app(settings=test_settings)
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
