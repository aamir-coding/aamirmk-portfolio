import pytest
from pydantic import ValidationError

from app.settings import Settings


def test_cors_origins_parses_comma_separated_env_string(monkeypatch) -> None:
    """Settings correctly parses comma-separated string from environment."""
    env_value = "http://localhost:5173,https://aamirmk-portfolio.vercel.app"
    monkeypatch.setenv("CORS_ORIGINS", env_value)

    settings = Settings()
    assert isinstance(settings.CORS_ORIGINS, list)
    assert settings.CORS_ORIGINS == [
        "http://localhost:5173",
        "https://aamirmk-portfolio.vercel.app",
    ]


def test_cors_origins_parses_json_array_env_string(monkeypatch) -> None:
    """Settings correctly parses JSON array formatted string from environment."""
    env_value = '["http://localhost:5173", "https://custom-domain.com"]'
    monkeypatch.setenv("CORS_ORIGINS", env_value)

    settings = Settings()
    assert isinstance(settings.CORS_ORIGINS, list)
    assert settings.CORS_ORIGINS == [
        "http://localhost:5173",
        "https://custom-domain.com",
    ]


def test_cors_origins_defaults_when_unset(monkeypatch) -> None:
    """Settings uses default list when CORS_ORIGINS is not set in env."""
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    settings = Settings()
    assert isinstance(settings.CORS_ORIGINS, list)
    assert "http://localhost:5173" in settings.CORS_ORIGINS


def test_inference_limits_are_conservative_and_do_not_include_an_allowance() -> None:
    settings = Settings(_env_file=None)
    assert settings.INFERENCE_SHARED_LIMITS.rpm == 24
    assert settings.INFERENCE_SHARED_LIMITS.tpm == 6400
    assert settings.INFERENCE_SHARED_LIMITS.tpd == 160000
    assert len(settings.INFERENCE_MODEL_LIMITS) == 2


@pytest.mark.parametrize(
    "options",
    [
        {"INFERENCE_MAX_ACTIVE": 0},
        {"INFERENCE_MAX_WAITERS": -1},
        {"INFERENCE_MODEL_LIMITS": {}},
        {"INFERENCE_SHARED_LIMITS": {"rpm": 1, "tpm": 0, "rpd": 1, "tpd": 100}},
    ],
)
def test_invalid_inference_capacity_is_rejected(options: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **options)


def test_inference_concurrency_accepts_documented_env_values(monkeypatch) -> None:
    monkeypatch.setenv("INFERENCE_MAX_ACTIVE", "2")
    monkeypatch.setenv("INFERENCE_MAX_WAITERS", "8")
    settings = Settings(_env_file=None)
    assert settings.INFERENCE_MAX_ACTIVE == 2
    assert settings.INFERENCE_MAX_WAITERS == 8
