import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration."""

    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS configuration - accepts comma-separated string or list of origins
    CORS_ORIGINS: str | list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Groq API configuration
    GROQ_API_KEY: str = ""
    LLM_MODEL_MAIN: str = "openai/gpt-oss-120b"
    LLM_MODEL_UTILITY: str = "openai/gpt-oss-20b"

    # Safety, Rate Limiting & Quota Guards (Phase 7)
    TRUST_PROXY_HEADERS: bool = True
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 10
    RATE_LIMIT_BURST: int = 15
    QUOTA_DAILY_REQUEST_LIMIT: int = 800
    QUOTA_DAILY_TOKEN_LIMIT: int = 180000

    model_config = SettingsConfigDict(
        # Try backend/.env first, then repo-root .env (for monorepo layout)
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            clean_str = v.strip()
            if clean_str.startswith("[") and clean_str.endswith("]"):
                try:
                    parsed = json.loads(clean_str)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in clean_str.split(",") if origin.strip()]
        if isinstance(v, list | tuple | set):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return []


@lru_cache
def get_settings() -> Settings:
    """Dependency provider returning cached Settings instance."""
    return Settings()
