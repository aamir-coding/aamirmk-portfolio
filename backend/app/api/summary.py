"""Create and open time-limited, public-by-link summaries."""

import hashlib
import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import SummaryRecord
from app.safety.rate_limiter import check_summary_rate_limit
from app.summary import ForwardableSummary, SummaryRequest, build_summary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/summary", tags=["summary"])
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")
LIFETIME = timedelta(days=30)


class SummaryCreated(BaseModel):
    token: str
    expires_at: datetime


class SummaryView(BaseModel):
    summary: ForwardableSummary
    expires_at: datetime


async def summary_sessions(request: Request) -> async_sessionmaker[AsyncSession] | None:
    return request.app.state.db_sessions


SummarySessions = Annotated[
    async_sessionmaker[AsyncSession] | None, Depends(summary_sessions)
]


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _storage_unavailable() -> HTTPException:
    return HTTPException(503, "Summary storage is temporarily unavailable.")


def _not_found() -> HTTPException:
    return HTTPException(404, "This summary link is unavailable or expired.")


@router.post("", status_code=201)
async def create_summary(
    request: Request, payload: SummaryRequest, sessions: SummarySessions
) -> SummaryCreated:
    if sessions is None:
        raise _storage_unavailable()
    await check_summary_rate_limit(request)
    token = secrets.token_urlsafe(32)
    created_at = datetime.now(UTC)
    expires_at = created_at + LIFETIME
    try:
        async with sessions.begin() as session:
            session.add(
                SummaryRecord(
                    token_hash=_token_hash(token),
                    content=build_summary(payload).model_dump(mode="json"),
                    created_at=created_at,
                    expires_at=expires_at,
                )
            )
    except (
        OSError,
        SQLAlchemyError,
        asyncpg.PostgresError,
        asyncpg.InterfaceError,
    ) as exc:
        logger.warning(
            "[%s] Summary write unavailable: %s",
            request.state.request_id,
            type(exc).__name__,
        )
        raise _storage_unavailable() from None
    return SummaryCreated(token=token, expires_at=expires_at)


@router.get("/{token}")
async def read_summary(
    request: Request, token: str, sessions: SummarySessions
) -> SummaryView:
    if not TOKEN_PATTERN.fullmatch(token):
        raise _not_found()
    if sessions is None:
        raise _storage_unavailable()
    try:
        async with sessions() as session:
            row = (
                await session.execute(
                    select(SummaryRecord.content, SummaryRecord.expires_at).where(
                        SummaryRecord.token_hash == _token_hash(token),
                        SummaryRecord.expires_at > func.now(),
                    )
                )
            ).one_or_none()
        if row is not None:
            return SummaryView(
                summary=ForwardableSummary.model_validate(row.content),
                expires_at=row.expires_at,
            )
    except (
        OSError,
        SQLAlchemyError,
        asyncpg.PostgresError,
        asyncpg.InterfaceError,
        ValidationError,
    ) as exc:
        logger.warning(
            "[%s] Summary read unavailable: %s",
            request.state.request_id,
            type(exc).__name__,
        )
        raise _storage_unavailable() from None
    raise _not_found()
