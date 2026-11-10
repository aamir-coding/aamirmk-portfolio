import ipaddress
import json
import re
from functools import lru_cache
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.safety.admission import CapacityLimits


class Settings(BaseSettings):
    """Application runtime configuration."""

    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    OPS_TOKEN: SecretStr = SecretStr("")
    ALERT_WEBHOOK_URL: SecretStr = SecretStr("")
    ALERT_WEBHOOK_FORMAT: Literal["generic", "discord"] = "generic"
    ENABLE_DEBUG_RETRIEVAL: bool = False

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
    TRUST_PROXY_HEADERS: bool = False
    TRUSTED_PROXY_CIDRS: list[str] = Field(default_factory=list, max_length=16)
    MAX_REQUEST_BYTES: int = Field(default=65536, ge=64, le=262144)
    RATE_LIMIT_MAX_KEYS: int = Field(default=4096, ge=2, le=16384)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 10
    RATE_LIMIT_BURST: int = 15
    FIT_RATE_LIMIT_DAILY: int = 5
    QUOTA_DAILY_REQUEST_LIMIT: int = 800
    QUOTA_DAILY_TOKEN_LIMIT: int = 180000

    # A ledger remains closed until a fresh, boot-bound allowance is authorized.
    INFERENCE_SHARED_LIMITS: CapacityLimits = Field(
        default_factory=lambda: CapacityLimits(rpm=24, tpm=6400, rpd=800, tpd=160000)
    )
    INFERENCE_MODEL_LIMITS: dict[str, CapacityLimits] = Field(
        default_factory=lambda: {
            model: CapacityLimits(rpm=24, tpm=6400, rpd=800, tpd=160000)
            for model in ("openai/gpt-oss-120b", "openai/gpt-oss-20b")
        },
        min_length=1,
        max_length=2,
    )
    INFERENCE_MAX_ACTIVE: int = Field(default=2, ge=1, le=16, strict=True)
    INFERENCE_MAX_WAITERS: int = Field(default=8, ge=0, le=64, strict=True)

    model_config = SettingsConfigDict(
        # Try backend/.env first, then repo-root .env (for monorepo layout)
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @field_validator("OPS_TOKEN")
    @classmethod
    def validate_ops_token(cls, value: SecretStr) -> SecretStr:
        token = value.get_secret_value()
        if token and not re.fullmatch(r"[A-Za-z0-9_-]{43,128}", token):
            raise ValueError("Operator credential must be 43-128 URL-safe characters")
        return value

    @field_validator("ALERT_WEBHOOK_URL")
    @classmethod
    def validate_alert_url(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not raw:
            return value
        try:
            url = urlsplit(raw)
            valid = (
                len(raw) <= 2048
                and url.scheme == "https"
                and url.hostname
                and url.username is None
                and url.password is None
                and not url.fragment
            )
        except ValueError:
            valid = False
        if not valid:
            raise ValueError(
                "Alert destination must be an HTTPS webhook without userinfo"
            )
        return value

    @field_validator("INFERENCE_MAX_ACTIVE", "INFERENCE_MAX_WAITERS", mode="before")
    @classmethod
    def parse_inference_integer(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.isascii() and stripped.isdecimal():
                return int(stripped)
        return value

    @field_validator("TRUSTED_PROXY_CIDRS")
    @classmethod
    def validate_proxy_networks(cls, values: list[str]) -> list[str]:
        networks = [ipaddress.ip_network(value) for value in values]
        if any(network.prefixlen == 0 for network in networks):
            raise ValueError("Trust-all proxy networks are not allowed")
        return [str(network) for network in networks]

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
