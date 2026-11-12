"""Postgres reservations and settlement for boot-bound quota grants."""

from datetime import date

import asyncpg
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import QuotaGrant, QuotaUsage
from app.safety.admission import Allowance, DailyCapacity, SettledAllowance
from app.safety.boot_quota import QuotaStorageUnavailable

_DB_ERRORS = (OSError, SQLAlchemyError, asyncpg.PostgresError, asyncpg.InterfaceError)
_BUCKET = "shared"


async def _lock_day(
    session: AsyncSession, day: date, *, initialize: bool
) -> QuotaUsage | None:
    if initialize:
        await session.execute(
            insert(QuotaUsage)
            .values(budget_date=day, bucket=_BUCKET, requests=0, tokens=0)
            .on_conflict_do_nothing(
                index_elements=[QuotaUsage.budget_date, QuotaUsage.bucket]
            )
        )
    return await session.scalar(
        select(QuotaUsage)
        .where(QuotaUsage.budget_date == day, QuotaUsage.bucket == _BUCKET)
        .with_for_update()
    )


class PostgresQuotaStore:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def reserve(
        self,
        requested: Allowance,
        ceiling: DailyCapacity,
        *,
        exact: bool,
    ) -> Allowance | None:
        day = requested.verified_at.date()
        try:
            async with self._sessions.begin() as session:
                usage = await _lock_day(session, day, initialize=True)
                if usage is None:
                    raise QuotaStorageUnavailable
                existing = await session.get(QuotaGrant, requested.boot_id)
                if existing is not None:
                    return self._existing_grant(
                        existing, requested, ceiling, exact=exact
                    )

                requests = min(requested.requests, ceiling.requests - usage.requests)
                tokens = min(requested.tokens, ceiling.tokens - usage.tokens)
                if min(requests, tokens) <= 0:
                    return None
                if exact and (requests, tokens) != (
                    requested.requests,
                    requested.tokens,
                ):
                    return None

                session.add(
                    QuotaGrant(
                        boot_id=requested.boot_id,
                        budget_date=day,
                        expires_at=requested.expires_at,
                        requests=requests,
                        tokens=tokens,
                    )
                )
                usage.requests += requests
                usage.tokens += tokens
                return requested.model_copy(
                    update={"requests": requests, "tokens": tokens}
                )
        except _DB_ERRORS as exc:
            raise QuotaStorageUnavailable from exc

    @staticmethod
    def _existing_grant(
        existing: QuotaGrant,
        requested: Allowance,
        ceiling: DailyCapacity,
        *,
        exact: bool,
    ) -> Allowance | None:
        if (
            existing.budget_date != requested.verified_at.date()
            or existing.expires_at != requested.expires_at
            or existing.charged_requests is not None
            or existing.requests > min(requested.requests, ceiling.requests)
            or existing.tokens > min(requested.tokens, ceiling.tokens)
        ):
            return None
        if exact and (existing.requests, existing.tokens) != (
            requested.requests,
            requested.tokens,
        ):
            return None
        return requested.model_copy(
            update={"requests": existing.requests, "tokens": existing.tokens}
        )

    async def settle(self, settlement: SettledAllowance) -> bool:
        allowance = settlement.allowance
        day = allowance.verified_at.date()
        if not (
            0 <= settlement.requests <= allowance.requests
            and 0 <= settlement.tokens <= allowance.tokens
        ):
            return False
        refund_requests = allowance.requests - settlement.requests
        refund_tokens = allowance.tokens - settlement.tokens
        try:
            async with self._sessions.begin() as session:
                usage = await _lock_day(session, day, initialize=False)
                if usage is None:
                    return False
                grant = await session.get(QuotaGrant, allowance.boot_id)
                if (
                    grant is None
                    or grant.budget_date != day
                    or grant.expires_at != allowance.expires_at
                    or grant.charged_requests is not None
                    or (grant.requests, grant.tokens)
                    != (allowance.requests, allowance.tokens)
                    or usage.requests < refund_requests
                    or usage.tokens < refund_tokens
                ):
                    return False
                grant.charged_requests = settlement.requests
                grant.charged_tokens = settlement.tokens
                usage.requests -= refund_requests
                usage.tokens -= refund_tokens
                return True
        except _DB_ERRORS as exc:
            raise QuotaStorageUnavailable from exc
