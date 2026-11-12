"""Construct an app-owned Postgres engine without dialing until first use."""

from ipaddress import ip_address

import asyncpg
from pydantic import SecretStr
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool


def _connection_url(secret: SecretStr) -> URL:
    try:
        url = make_url(secret.get_secret_value())
        if url.drivername not in {"postgresql", "postgresql+asyncpg"} or not (
            url.host and url.username and url.database
        ):
            raise ValueError
    except (ArgumentError, ValueError):
        raise ValueError(
            "Expected a PostgreSQL URL with a host, user and database"
        ) from None

    mode = url.query.get("sslmode", "verify-full")
    if mode == "disable":
        try:
            loopback = ip_address(url.host).is_loopback
        except ValueError:
            loopback = url.host == "localhost"
        if not loopback:
            raise ValueError("Plaintext Postgres is limited to local development")
    elif mode not in ("require", "verify-ca", "verify-full"):
        raise ValueError("Choose a Postgres SSL mode that requires encryption")
    return url.set(drivername="postgresql").update_query_dict({"sslmode": mode})


def create_database_engine(secret: SecretStr, *, pooled: bool = True) -> AsyncEngine:
    dsn = _connection_url(secret).render_as_string(hide_password=False)

    async def connect() -> asyncpg.Connection:
        return await asyncpg.connect(
            dsn=dsn, timeout=3, command_timeout=5 if pooled else 30
        )

    pool_options = (
        {"pool_size": 2, "max_overflow": 0, "pool_timeout": 3, "pool_pre_ping": True}
        if pooled
        else {"poolclass": NullPool}
    )
    return create_async_engine(
        "postgresql+asyncpg://",
        async_creator=connect,
        hide_parameters=True,
        **pool_options,
    )
