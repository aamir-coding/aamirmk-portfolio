"""create recruiter workflow tables

Revision ID: 0001
Revises: None
Create Date: 2026-11-12 08:44:11.662061
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA portfolio")
    op.execute("REVOKE ALL ON SCHEMA portfolio FROM PUBLIC")
    op.create_table(
        "quota_usage",
        sa.Column("budget_date", sa.Date(), nullable=False),
        sa.Column("bucket", sa.String(length=64), nullable=False),
        sa.Column("requests", sa.Integer(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "requests >= 0 AND tokens >= 0", name=op.f("ck_quota_usage_nonnegative")
        ),
        sa.PrimaryKeyConstraint("budget_date", "bucket", name=op.f("pk_quota_usage")),
        schema="portfolio",
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=False),
        sa.Column("device_class", sa.String(length=8), nullable=False),
        sa.Column("company_slug", sa.String(length=64), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "device_class IN ('mobile', 'desktop', 'unknown')",
            name=op.f("ck_sessions_device_class"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        schema="portfolio",
    )
    op.create_index(
        op.f("ix_sessions_company_slug"),
        "sessions",
        ["company_slug"],
        unique=False,
        schema="portfolio",
    )
    op.create_index(
        op.f("ix_sessions_last_seen_at"),
        "sessions",
        ["last_seen_at"],
        unique=False,
        schema="portfolio",
    )
    op.create_table(
        "summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expires_at > created_at", name=op.f("ck_summaries_expiry")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_summaries")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_summaries_token_hash")),
        schema="portfolio",
    )
    op.create_index(
        op.f("ix_summaries_expires_at"),
        "summaries",
        ["expires_at"],
        unique=False,
        schema="portfolio",
    )
    op.create_table(
        "handoffs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("reply_email", sa.String(length=254), nullable=True),
        sa.Column(
            "transcript", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "delivery_status",
            sa.String(length=8),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "delivery_status IN ('pending', 'sent', 'failed')",
            name=op.f("ck_handoffs_delivery_status"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["portfolio.sessions.id"],
            name=op.f("fk_handoffs_session_id_sessions"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_handoffs")),
        schema="portfolio",
    )
    op.create_index(
        op.f("ix_handoffs_created_at"),
        "handoffs",
        ["created_at"],
        unique=False,
        schema="portfolio",
    )
    op.create_index(
        op.f("ix_handoffs_session_id"),
        "handoffs",
        ["session_id"],
        unique=False,
        schema="portfolio",
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.String(length=2000), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(input_tokens IS NULL) = (output_tokens IS NULL)",
            name=op.f("ck_messages_usage_pair"),
        ),
        sa.CheckConstraint(
            "input_tokens >= 0 AND output_tokens >= 0", name=op.f("ck_messages_tokens")
        ),
        sa.CheckConstraint("latency_ms >= 0", name=op.f("ck_messages_latency")),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["portfolio.sessions.id"],
            name=op.f("fk_messages_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        schema="portfolio",
    )
    op.create_index(
        op.f("ix_messages_created_at"),
        "messages",
        ["created_at"],
        unique=False,
        schema="portfolio",
    )
    op.create_index(
        op.f("ix_messages_session_id"),
        "messages",
        ["session_id"],
        unique=False,
        schema="portfolio",
    )
    op.create_table(
        "feedback",
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("rating IN (-1, 1)", name=op.f("ck_feedback_rating")),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["portfolio.messages.id"],
            name=op.f("fk_feedback_message_id_messages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("message_id", name=op.f("pk_feedback")),
        schema="portfolio",
    )
    op.create_index(
        op.f("ix_feedback_created_at"),
        "feedback",
        ["created_at"],
        unique=False,
        schema="portfolio",
    )


def downgrade() -> None:
    op.drop_table("feedback", schema="portfolio")
    op.drop_table("messages", schema="portfolio")
    op.drop_table("handoffs", schema="portfolio")
    op.drop_table("summaries", schema="portfolio")
    op.drop_table("sessions", schema="portfolio")
    op.drop_table("quota_usage", schema="portfolio")
    op.execute("DROP SCHEMA portfolio")
