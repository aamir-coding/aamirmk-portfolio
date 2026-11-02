"""In-memory sliding-window rate limiter with per-IP tracking and cleanup."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from app.safety.ip import get_client_ip
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    """Immutable result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int


class SlidingWindowRateLimiter:
    """Thread-safe, async in-memory sliding window rate limiter."""

    def __init__(
        self,
        requests_per_window: int = 10,
        window_seconds: float = 60.0,
        enabled: bool = True,
    ) -> None:
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.enabled = enabled
        self._records: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = 300.0

    async def check(self, key: str) -> RateLimitResult:
        """Check whether a request for key is allowed under the sliding window."""
        if not self.enabled:
            return RateLimitResult(
                allowed=True,
                limit=self.requests_per_window,
                remaining=self.requests_per_window,
                reset_seconds=0,
            )

        now = time.monotonic()

        async with self._lock:
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup_stale(now)
                self._last_cleanup = now

            timestamps = self._records[key]
            cutoff = now - self.window_seconds

            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.requests_per_window:
                oldest = timestamps[0]
                reset_seconds = max(1, int(oldest + self.window_seconds - now))
                return RateLimitResult(
                    allowed=False,
                    limit=self.requests_per_window,
                    remaining=0,
                    reset_seconds=reset_seconds,
                )

            timestamps.append(now)
            remaining = self.requests_per_window - len(timestamps)
            return RateLimitResult(
                allowed=True,
                limit=self.requests_per_window,
                remaining=remaining,
                reset_seconds=int(self.window_seconds),
            )

    def _cleanup_stale(self, now: float) -> None:
        """Remove keys with no activity in the current sliding window."""
        cutoff = now - self.window_seconds
        stale_keys = [
            k
            for k, timestamps in self._records.items()
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for k in stale_keys:
            del self._records[k]

    def reset(self) -> None:
        """Clear all active records (useful for test isolation)."""
        self._records.clear()


_limiter_instance: SlidingWindowRateLimiter | None = None


def get_rate_limiter(
    settings: Settings = Depends(get_settings),
) -> SlidingWindowRateLimiter:
    """Dependency provider returning singleton SlidingWindowRateLimiter."""
    global _limiter_instance
    if _limiter_instance is None:
        cfg = settings if isinstance(settings, Settings) else get_settings()
        _limiter_instance = SlidingWindowRateLimiter(
            requests_per_window=cfg.RATE_LIMIT_REQUESTS_PER_MINUTE,
            window_seconds=60.0,
            enabled=cfg.RATE_LIMIT_ENABLED,
        )
    return _limiter_instance


async def check_rate_limit(
    request: Request,
    limiter: SlidingWindowRateLimiter = Depends(get_rate_limiter),
) -> RateLimitResult:
    """FastAPI dependency enforcing sliding-window rate limit per client IP."""
    client_ip = get_client_ip(request)
    result = await limiter.check(client_ip)

    if not result.allowed:
        logger.warning(
            "Rate limit exceeded for IP %s: %d reqs in window",
            client_ip,
            result.limit,
        )
        msg = (
            f"Rate limit reached. Please wait {result.reset_seconds} "
            "seconds before sending another message."
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg,
            headers={
                "Retry-After": str(result.reset_seconds),
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_seconds),
            },
        )
    return result


_fit_limiter_instance: SlidingWindowRateLimiter | None = None


def get_fit_rate_limiter(
    settings: Settings = Depends(get_settings),
) -> SlidingWindowRateLimiter:
    """Dependency provider returning singleton rate limiter for JD Fit reports."""
    global _fit_limiter_instance
    if _fit_limiter_instance is None:
        cfg = settings if isinstance(settings, Settings) else get_settings()
        _fit_limiter_instance = SlidingWindowRateLimiter(
            requests_per_window=cfg.FIT_RATE_LIMIT_DAILY,
            window_seconds=86400.0,
            enabled=cfg.RATE_LIMIT_ENABLED,
        )
    return _fit_limiter_instance


async def check_fit_rate_limit(
    request: Request,
    limiter: SlidingWindowRateLimiter = Depends(get_fit_rate_limiter),
) -> RateLimitResult:
    """FastAPI dependency enforcing daily fit report rate limits per client IP."""
    client_ip = get_client_ip(request)
    result = await limiter.check(client_ip)

    if not result.allowed:
        logger.warning(
            "Fit rate limit exceeded for IP %s: %d reports in 24h",
            client_ip,
            result.limit,
        )
        msg = (
            f"Daily JD Fit Report limit reached ({result.limit} reports per 24 hours). "
            f"Please wait {result.reset_seconds} seconds or contact Aamir directly."
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg,
            headers={
                "Retry-After": str(result.reset_seconds),
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_seconds),
            },
        )
    return result
