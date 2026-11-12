"""Add durable boot grant records.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quota_grants",
        sa.Column("boot_id", sa.String(length=64), nullable=False),
        sa.Column("budget_date", sa.Date(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requests", sa.Integer(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.Column("charged_requests", sa.Integer(), nullable=True),
        sa.Column("charged_tokens", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("boot_id", name=op.f("pk_quota_grants")),
        sa.CheckConstraint(
            "requests > 0 AND tokens > 0", name=op.f("ck_quota_grants_positive")
        ),
        sa.CheckConstraint(
            "(charged_requests IS NULL AND charged_tokens IS NULL) OR "
            "(charged_requests IS NOT NULL AND charged_tokens IS NOT NULL AND "
            "charged_requests BETWEEN 0 AND requests AND "
            "charged_tokens BETWEEN 0 AND tokens)",
            name=op.f("ck_quota_grants_settlement"),
        ),
        schema="portfolio",
    )
    op.create_index(
        "ix_quota_grants_budget_date",
        "quota_grants",
        ["budget_date"],
        schema="portfolio",
    )


def downgrade() -> None:
    op.drop_table("quota_grants", schema="portfolio")
