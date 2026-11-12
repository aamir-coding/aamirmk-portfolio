"""Bounded admin views over the last seven UTC days of stored activity."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Date, cast, func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    FeedbackRecord,
    FitRunRecord,
    HandoffRecord,
    MessageRecord,
    RecruiterSession,
)

DETAIL_LIMIT = 20
WINDOW_DAYS = 7


class TopQuestion(BaseModel):
    question: str
    count: int


class CompanyOpens(BaseModel):
    slug: str
    count: int


class RecentQuestion(BaseModel):
    id: UUID
    question: str
    created_at: datetime


class FeedbackDetail(RecentQuestion):
    rating: Literal["up", "down"]
    reason: str | None


class HandoffDetail(BaseModel):
    id: UUID
    question: str | None
    reply_email: str | None
    delivery_status: Literal["pending", "sent", "failed"]
    created_at: datetime


class UsageDay(BaseModel):
    day: date
    known_tokens: int = 0
    unknown_runs: int = 0
    fit_reports: int = 0


class Dashboard(BaseModel):
    start_date: date
    end_date: date
    question_count: int
    classified_questions: int
    unanswered_count: int
    average_latency_ms: float | None
    fit_reports: int
    handoff_count: int
    candidate_count: int
    daily_token_ceiling: int
    usage: list[UsageDay]
    company_opens: list[CompanyOpens]
    top_questions: list[TopQuestion]
    unanswered: list[RecentQuestion]
    handoffs: list[HandoffDetail]
    feedback: list[FeedbackDetail]
    candidates: list[FeedbackDetail]


async def _usage_by_day(
    session: AsyncSession, start: datetime, now: datetime
) -> list[UsageDay]:
    usage = union_all(
        select(
            MessageRecord.created_at,
            MessageRecord.input_tokens,
            MessageRecord.output_tokens,
            literal(False).label("is_fit"),
        ).where(MessageRecord.created_at.between(start, now)),
        select(
            FitRunRecord.created_at,
            FitRunRecord.input_tokens,
            FitRunRecord.output_tokens,
            literal(True),
        ).where(FitRunRecord.created_at.between(start, now)),
    ).subquery()
    utc_day = cast(func.timezone("UTC", usage.c.created_at), Date)
    rows = await session.execute(
        select(
            utc_day.label("day"),
            func.coalesce(
                func.sum(usage.c.input_tokens + usage.c.output_tokens), 0
            ).label("known_tokens"),
            func.count().filter(usage.c.input_tokens.is_(None)).label("unknown_runs"),
            func.count().filter(usage.c.is_fit).label("fit_reports"),
        ).group_by(utc_day)
    )
    by_day = {row.day: UsageDay.model_validate(row._mapping) for row in rows}
    days = [start.date() + timedelta(days=offset) for offset in range(WINDOW_DAYS)]
    return [by_day.get(day) or UsageDay(day=day) for day in days]


async def load_dashboard(
    session: AsyncSession,
    *,
    daily_token_ceiling: int,
    now: datetime,
) -> Dashboard:
    start_date = now.date() - timedelta(days=WINDOW_DAYS - 1)
    start = datetime.combine(start_date, time.min, UTC)
    question_window = MessageRecord.created_at.between(start, now)
    offered = MessageRecord.handoff_offered.is_(True)
    count = func.count()
    totals = (
        await session.execute(
            select(
                count.label("question_count"),
                func.count(MessageRecord.handoff_offered).label("classified_questions"),
                count.filter(offered).label("unanswered_count"),
                func.avg(MessageRecord.latency_ms).label("average_latency_ms"),
            ).where(question_window)
        )
    ).one()
    top = await session.execute(
        select(MessageRecord.question, count.label("count"))
        .where(question_window)
        .group_by(MessageRecord.question)
        .order_by(count.desc(), MessageRecord.question)
        .limit(DETAIL_LIMIT)
    )
    unanswered = await session.execute(
        select(MessageRecord.id, MessageRecord.question, MessageRecord.created_at)
        .where(question_window, offered)
        .order_by(MessageRecord.created_at.desc(), MessageRecord.id)
        .limit(DETAIL_LIMIT)
    )
    company_opens = await session.execute(
        select(RecruiterSession.company_slug.label("slug"), count.label("count"))
        .where(
            RecruiterSession.opened_at.between(start, now),
            RecruiterSession.company_slug.is_not(None),
        )
        .group_by(RecruiterSession.company_slug)
        .order_by(count.desc(), RecruiterSession.company_slug)
        .limit(DETAIL_LIMIT)
    )
    feedback_window = FeedbackRecord.created_at.between(start, now)
    downvote = FeedbackRecord.rating == -1
    feedback_query = (
        select(
            FeedbackRecord.message_id.label("id"),
            MessageRecord.question,
            FeedbackRecord.rating,
            FeedbackRecord.reason,
            FeedbackRecord.created_at,
        )
        .join(MessageRecord, MessageRecord.id == FeedbackRecord.message_id)
        .where(feedback_window)
        .order_by(FeedbackRecord.created_at.desc(), FeedbackRecord.message_id)
        .limit(DETAIL_LIMIT)
    )
    feedback = await session.execute(feedback_query)
    candidates = await session.execute(feedback_query.where(downvote))
    candidate_count = await session.scalar(
        select(count).where(feedback_window, downvote)
    )
    handoff_window = HandoffRecord.created_at.between(start, now)
    handoff_count = await session.scalar(select(count).where(handoff_window))
    handoffs = await session.scalars(
        select(HandoffRecord)
        .where(handoff_window)
        .order_by(HandoffRecord.created_at.desc(), HandoffRecord.id)
        .limit(DETAIL_LIMIT)
    )
    usage = await _usage_by_day(session, start, now)
    return Dashboard(
        start_date=start_date,
        end_date=now.date(),
        **totals._mapping,
        fit_reports=sum(day.fit_reports for day in usage),
        handoff_count=handoff_count or 0,
        candidate_count=candidate_count or 0,
        daily_token_ceiling=daily_token_ceiling,
        usage=usage,
        company_opens=[
            CompanyOpens.model_validate(row._mapping) for row in company_opens
        ],
        top_questions=[TopQuestion.model_validate(row._mapping) for row in top],
        unanswered=[RecentQuestion.model_validate(row._mapping) for row in unanswered],
        handoffs=[
            HandoffDetail(
                id=row.id,
                question=next(
                    (
                        message["content"][:500]
                        for message in reversed(row.transcript)
                        if message["role"] == "user"
                    ),
                    None,
                ),
                reply_email=row.reply_email,
                delivery_status=row.delivery_status,
                created_at=row.created_at,
            )
            for row in handoffs
        ],
        feedback=[
            FeedbackDetail(
                **{**row._mapping, "rating": "up" if row.rating == 1 else "down"}
            )
            for row in feedback
        ],
        candidates=[
            FeedbackDetail(**{**row._mapping, "rating": "down"}) for row in candidates
        ],
    )
