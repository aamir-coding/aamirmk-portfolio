"""Global daily quota guard to protect Groq account limits (RPD and TPD)."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time

from fastapi import Depends, HTTPException, status

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QuotaStatus:
    """Current state of daily quota usage."""

    date: str
    requests_used: int
    requests_limit: int
    tokens_used: int
    tokens_limit: int
    is_exhausted: bool
    seconds_until_reset: int


def _seconds_until_midnight_utc() -> int:
    """Calculate remaining seconds until 00:00:00 UTC."""
    now_utc = datetime.now(UTC)
    tomorrow_utc = (now_utc + timedelta(days=1)).date()
    midnight_utc = datetime.combine(tomorrow_utc, dt_time.min, tzinfo=UTC)
    return max(1, int((midnight_utc - now_utc).total_seconds()))


class DailyQuotaGuard:
    """Tracks daily global LLM requests and token consumption against free-tier caps."""

    def __init__(
        self,
        max_requests_per_day: int = 800,
        max_tokens_per_day: int = 180000,
    ) -> None:
        self.max_requests_per_day = max_requests_per_day
        self.max_tokens_per_day = max_tokens_per_day
        self._current_date = datetime.now(UTC).date()
        self._requests_count = 0
        self._tokens_count = 0
        self._lock = asyncio.Lock()

    def _rollover_if_needed(self) -> None:
        """Reset counters if UTC calendar day has rolled over."""
        today = datetime.now(UTC).date()
        if today != self._current_date:
            logger.info("Resetting daily quota counters for new UTC day: %s", today)
            self._current_date = today
            self._requests_count = 0
            self._tokens_count = 0

    async def check(self) -> None:
        """Check if daily quota is available.

        Raises HTTPException(429) if daily requests or tokens limit reached.
        """
        async with self._lock:
            self._rollover_if_needed()
            if self._requests_count >= self.max_requests_per_day:
                seconds_left = _seconds_until_midnight_utc()
                logger.warning(
                    "Daily request quota reached: %d/%d",
                    self._requests_count,
                    self.max_requests_per_day,
                )
                msg = (
                    "Daily assistant conversation capacity reached. "
                    "Quota resets at 00:00 UTC. "
                    "Feel free to connect directly with Aamir."
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=msg,
                    headers={
                        "Retry-After": str(seconds_left),
                        "X-Quota-Daily-Limit": str(self.max_requests_per_day),
                        "X-Quota-Daily-Remaining": "0",
                    },
                )

            if self._tokens_count >= self.max_tokens_per_day:
                seconds_left = _seconds_until_midnight_utc()
                logger.warning(
                    "Daily token quota reached: %d/%d",
                    self._tokens_count,
                    self.max_tokens_per_day,
                )
                msg = (
                    "Daily token processing capacity reached. "
                    "Quota resets at 00:00 UTC. "
                    "Feel free to connect directly with Aamir."
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=msg,
                    headers={
                        "Retry-After": str(seconds_left),
                        "X-Quota-Daily-Limit": str(self.max_tokens_per_day),
                        "X-Quota-Daily-Remaining": "0",
                    },
                )

    async def record_usage(self, tokens: int = 0) -> None:
        """Increment daily request and token counters."""
        async with self._lock:
            self._rollover_if_needed()
            self._requests_count += 1
            if tokens > 0:
                self._tokens_count += tokens

    async def get_status(self) -> QuotaStatus:
        """Retrieve current daily quota snapshot."""
        async with self._lock:
            self._rollover_if_needed()
            is_exhausted = (
                self._requests_count >= self.max_requests_per_day
                or self._tokens_count >= self.max_tokens_per_day
            )
            return QuotaStatus(
                date=self._current_date.isoformat(),
                requests_used=self._requests_count,
                requests_limit=self.max_requests_per_day,
                tokens_used=self._tokens_count,
                tokens_limit=self.max_tokens_per_day,
                is_exhausted=is_exhausted,
                seconds_until_reset=_seconds_until_midnight_utc(),
            )

    def reset(self) -> None:
        """Reset tracking state immediately (for testing)."""
        self._requests_count = 0
        self._tokens_count = 0
        self._current_date = datetime.now(UTC).date()


_quota_guard_instance: DailyQuotaGuard | None = None


def get_quota_guard(
    settings: Settings = Depends(get_settings),
) -> DailyQuotaGuard:
    """Dependency provider returning singleton DailyQuotaGuard."""
    global _quota_guard_instance
    if _quota_guard_instance is None:
        _quota_guard_instance = DailyQuotaGuard(
            max_requests_per_day=settings.QUOTA_DAILY_REQUEST_LIMIT,
            max_tokens_per_day=settings.QUOTA_DAILY_TOKEN_LIMIT,
        )
    return _quota_guard_instance


async def check_daily_quota(
    guard: DailyQuotaGuard = Depends(get_quota_guard),
) -> None:
    """FastAPI dependency verifying global daily quota before servicing request."""
    await guard.check()
