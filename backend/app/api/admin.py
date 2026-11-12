"""Read-only recruiter analytics gated by the dedicated admin bearer."""

import logging
import secrets
from datetime import UTC, datetime
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.dashboard import Dashboard, load_dashboard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", include_in_schema=False)


async def require_admin(request: Request) -> async_sessionmaker[AsyncSession]:
    token = request.app.state.settings.ADMIN_TOKEN.get_secret_value()
    if not token:
        raise HTTPException(404, "Not Found")
    values = request.headers.getlist("authorization")
    supplied = values[0] if len(values) == 1 else ""
    valid = len(supplied) <= 135 and secrets.compare_digest(
        supplied.encode(), f"Bearer {token}".encode()
    )
    decision = await request.app.state.admin_rate_limiter.check(
        "valid" if valid else "invalid"
    )
    if not decision.allowed:
        raise HTTPException(
            429,
            "Admin request limit reached.",
            headers={"Retry-After": str(decision.reset_seconds)},
        )
    if not valid:
        raise HTTPException(
            401,
            "Admin authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sessions: async_sessionmaker[AsyncSession] | None = request.app.state.db_sessions
    if sessions is None:
        raise HTTPException(503, "Admin storage is unavailable.")
    return sessions


@router.get("/dashboard")
async def get_dashboard(
    request: Request,
    sessions: Annotated[async_sessionmaker[AsyncSession], Depends(require_admin)],
) -> Dashboard:
    try:
        async with sessions.begin() as session:
            await session.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            )
            return await load_dashboard(
                session,
                daily_token_ceiling=request.app.state.settings.INFERENCE_SHARED_LIMITS.tpd,
                now=datetime.now(UTC),
            )
    except (
        OSError,
        SQLAlchemyError,
        asyncpg.PostgresError,
        asyncpg.InterfaceError,
    ) as exc:
        logger.warning(
            "[%s] Admin storage unavailable: %s",
            request.state.request_id,
            type(exc).__name__,
        )
        raise HTTPException(503, "Admin storage is unavailable.") from None
