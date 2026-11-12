"""In-memory sliding-window rate limiter with per-IP tracking and cleanup."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from app.safety.ip import get_client_ip


@dataclass(frozen=True)
class RateLimitResult:
    """Immutable result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int


class SlidingWindowRateLimiter:
    """Single-event-loop bounded in-memory sliding window rate limiter."""

    def __init__(
        self,
        requests_per_window: int = 10,
        window_seconds: float = 60.0,
        enabled: bool = True,
        max_keys: int = 4096,
    ) -> None:
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.enabled = enabled
        self.max_keys = max_keys
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

            if key not in self._records and len(self._records) >= self.max_keys:
                self._cleanup_stale(now)
                if len(self._records) >= self.max_keys:
                    return RateLimitResult(
                        False, self.requests_per_window, 0, int(self.window_seconds)
                    )
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


def get_rate_limiter(request: Request) -> SlidingWindowRateLimiter:
    return request.app.state.chat_rate_limiter


def get_fit_rate_limiter(request: Request) -> SlidingWindowRateLimiter:
    return request.app.state.fit_rate_limiter


async def _enforce(
    request: Request, limiter: SlidingWindowRateLimiter, message: str
) -> RateLimitResult:
    client_ip = get_client_ip(request)
    result = await limiter.check(f"ip:{client_ip}")
    session = request.headers.get("x-session-id")
    if result.allowed and session:
        session_result = await limiter.check(f"session:{session}")
        if session_result.remaining < result.remaining or not session_result.allowed:
            result = session_result
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"{message}. Please wait {result.reset_seconds} seconds "
                "or contact Aamir."
            ),
            headers={
                "Retry-After": str(result.reset_seconds),
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_seconds),
            },
        )
    return result


async def check_rate_limit(
    request: Request,
    limiter: SlidingWindowRateLimiter = Depends(get_rate_limiter),
) -> RateLimitResult:
    return await _enforce(request, limiter, "Rate limit reached")


async def check_fit_rate_limit(
    request: Request,
    limiter: SlidingWindowRateLimiter = Depends(get_fit_rate_limiter),
) -> RateLimitResult:
    return await _enforce(request, limiter, "Daily JD Fit Report limit reached")


async def check_handoff_rate_limit(request: Request) -> None:
    await _enforce(
        request, request.app.state.handoff_rate_limiter, "Handoff limit reached"
    )
    shared = await request.app.state.handoff_global_limiter.check("handoff")
    if not shared.allowed:
        raise HTTPException(
            status_code=429,
            detail="Handoff limit reached. Please try again later.",
            headers={"Retry-After": str(shared.reset_seconds)},
        )


async def check_feedback_rate_limit(request: Request) -> None:
    await _enforce(
        request, request.app.state.feedback_rate_limiter, "Feedback limit reached"
    )
