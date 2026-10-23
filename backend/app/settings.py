from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration."""

    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS configuration - default to local dev origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Groq API configuration
    GROQ_API_KEY: str = ""
    LLM_MODEL_MAIN: str = "openai/gpt-oss-120b"
    LLM_MODEL_UTILITY: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list | tuple | set):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return []


@lru_cache
def get_settings() -> Settings:
    """Dependency provider returning cached Settings instance."""
    return Settings()
