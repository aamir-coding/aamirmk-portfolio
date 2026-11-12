"""Store one rating for a saved answer."""

import logging
from typing import Literal

import asyncpg
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.analytics import AnalyticsWriter
from app.db.models import FeedbackRecord, MessageRecord
from app.safety.guardrails import valid_unicode
from app.safety.rate_limiter import check_feedback_rate_limit

router = APIRouter(tags=["feedback"])
logger = logging.getLogger(__name__)

FeedbackRating = Literal["up", "down"]


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_id: UUID4
    rating: FeedbackRating
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("Reason must be valid text")
        return valid_unicode(value).strip() or None


class FeedbackSaved(BaseModel):
    rating: FeedbackRating


@router.post("/feedback")
async def submit_feedback(
    request: Request,
    response: Response,
    payload: FeedbackRequest,
) -> FeedbackSaved:
    sessions: async_sessionmaker[AsyncSession] | None = request.app.state.db_sessions
    if sessions is None:
        raise HTTPException(503, "Feedback is temporarily unavailable.")
    await check_feedback_rate_limit(request)
    writer: AnalyticsWriter | None = request.app.state.analytics
    try:
        if writer is not None:
            await writer.wait_for_answer(payload.answer_id)
        rating = 1 if payload.rating == "up" else -1
        async with sessions.begin() as session:
            await session.execute(
                insert(FeedbackRecord)
                .from_select(
                    ["message_id", "rating", "reason"],
                    select(
                        MessageRecord.id, literal(rating), literal(payload.reason)
                    ).where(MessageRecord.id == payload.answer_id),
                )
                .on_conflict_do_nothing(index_elements=[FeedbackRecord.message_id])
            )
            saved = await session.get(FeedbackRecord, payload.answer_id)
    except (
        OSError,
        SQLAlchemyError,
        asyncpg.PostgresError,
        asyncpg.InterfaceError,
    ) as exc:
        logger.warning(
            "[%s] Feedback write unavailable: %s",
            request.state.request_id,
            type(exc).__name__,
        )
        raise HTTPException(503, "Feedback is temporarily unavailable.") from None
    if saved is None:
        raise HTTPException(404, "Feedback is unavailable for this answer.")
    response.headers["Cache-Control"] = "no-store"
    return FeedbackSaved(rating="up" if saved.rating == 1 else "down")
