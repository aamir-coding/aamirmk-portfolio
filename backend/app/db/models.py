"""Postgres tables for the recruiter workflow."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    MetaData,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SCHEMA = "portfolio"


class Base(DeclarativeBase):
    metadata = MetaData(
        schema=SCHEMA,
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )


class RecruiterSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint(
            "device_class IN ('mobile', 'desktop', 'unknown')", name="device_class"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    ip_hash: Mapped[str] = mapped_column(String(64))
    device_class: Mapped[str] = mapped_column(String(8))
    company_slug: Mapped[str | None] = mapped_column(String(64), index=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class MessageRecord(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("latency_ms >= 0", name="latency"),
        CheckConstraint("input_tokens >= 0 AND output_tokens >= 0", name="tokens"),
        CheckConstraint(
            "(input_tokens IS NULL) = (output_tokens IS NULL)", name="usage_pair"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(String(2000))
    latency_ms: Mapped[float] = mapped_column(Float)
    input_tokens: Mapped[int | None]
    output_tokens: Mapped[int | None]
    handoff_offered: Mapped[bool | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class FeedbackRecord(Base):
    __tablename__ = "feedback"
    __table_args__ = (CheckConstraint("rating IN (-1, 1)", name="rating"),)

    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True
    )
    rating: Mapped[int]
    reason: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class FitRunRecord(Base):
    __tablename__ = "fit_runs"
    __table_args__ = (
        CheckConstraint("input_tokens >= 0 AND output_tokens >= 0", name="tokens"),
        CheckConstraint(
            "(input_tokens IS NULL) = (output_tokens IS NULL)", name="usage_pair"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    input_tokens: Mapped[int | None]
    output_tokens: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class HandoffRecord(Base):
    __tablename__ = "handoffs"
    __table_args__ = (
        CheckConstraint(
            "delivery_status IN ('pending', 'sent', 'failed')", name="delivery_status"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sessions.id", ondelete="SET NULL"), index=True
    )
    reply_email: Mapped[str | None] = mapped_column(String(254))
    transcript: Mapped[list[dict[str, str]]] = mapped_column(JSONB)
    delivery_status: Mapped[str] = mapped_column(String(8), server_default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class SummaryRecord(Base):
    __tablename__ = "summaries"
    __table_args__ = (CheckConstraint("expires_at > created_at", name="expiry"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    content: Mapped[dict[str, object]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class QuotaUsage(Base):
    __tablename__ = "quota_usage"
    __table_args__ = (
        CheckConstraint("requests >= 0 AND tokens >= 0", name="nonnegative"),
    )

    budget_date: Mapped[date] = mapped_column(primary_key=True)
    bucket: Mapped[str] = mapped_column(String(64), primary_key=True)
    requests: Mapped[int]
    tokens: Mapped[int]
