"""Record handoff classification and fit usage.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("handoff_offered", sa.Boolean(), nullable=True),
        schema="portfolio",
    )
    op.create_table(
        "fit_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fit_runs")),
        sa.CheckConstraint(
            "input_tokens >= 0 AND output_tokens >= 0", name=op.f("ck_fit_runs_tokens")
        ),
        sa.CheckConstraint(
            "(input_tokens IS NULL) = (output_tokens IS NULL)",
            name=op.f("ck_fit_runs_usage_pair"),
        ),
        schema="portfolio",
    )
    op.create_index(
        "ix_fit_runs_created_at", "fit_runs", ["created_at"], schema="portfolio"
    )


def downgrade() -> None:
    op.drop_table("fit_runs", schema="portfolio")
    op.drop_column("messages", "handoff_offered", schema="portfolio")
