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
