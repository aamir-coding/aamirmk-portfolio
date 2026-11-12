"""Install the daily recruiter-data cleanup function.

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE FUNCTION portfolio.purge_expired_data() RETURNS void
        LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog
        AS $purge$
        DECLARE
            run_at timestamptz := statement_timestamp();
            cutoff timestamptz := run_at - interval '2160 hours';
            cutoff_day date := (cutoff AT TIME ZONE 'UTC')::date;
        BEGIN
            DELETE FROM portfolio.feedback WHERE created_at <= cutoff;
            DELETE FROM portfolio.messages WHERE created_at <= cutoff;
            DELETE FROM portfolio.fit_runs WHERE created_at <= cutoff;
            DELETE FROM portfolio.handoffs WHERE created_at <= cutoff;
            DELETE FROM portfolio.sessions WHERE last_seen_at <= cutoff;
            DELETE FROM portfolio.summaries WHERE expires_at <= run_at;
            DELETE FROM portfolio.quota_grants WHERE budget_date < cutoff_day;
            DELETE FROM portfolio.quota_usage WHERE budget_date < cutoff_day;
        END;
        $purge$;
    """)
    op.execute("REVOKE EXECUTE ON FUNCTION portfolio.purge_expired_data() FROM PUBLIC")


def downgrade() -> None:
    op.execute("DROP FUNCTION portfolio.purge_expired_data()")
