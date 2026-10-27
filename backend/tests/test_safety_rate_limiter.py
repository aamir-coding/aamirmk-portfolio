"""Tests for sliding window rate limiter and FastAPI dependency."""

import asyncio

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.requests import Request

from app.safety.rate_limiter import (
    SlidingWindowRateLimiter,
    check_rate_limit,
)


@pytest.mark.asyncio
async def test_sliding_window_allows_under_limit():
    """Verify limiter allows requests up to window limit and decrements remaining."""
    limiter = SlidingWindowRateLimiter(requests_per_window=3, window_seconds=60.0)

    res1 = await limiter.check("1.1.1.1")
    assert res1.allowed is True
    assert res1.remaining == 2

    res2 = await limiter.check("1.1.1.1")
    assert res2.allowed is True
    assert res2.remaining == 1

    res3 = await limiter.check("1.1.1.1")
    assert res3.allowed is True
    assert res3.remaining == 0


@pytest.mark.asyncio
async def test_sliding_window_rejects_exceeded_limit():
    """Verify limiter rejects requests exceeding limit with valid reset_seconds."""
    limiter = SlidingWindowRateLimiter(requests_per_window=2, window_seconds=10.0)

    await limiter.check("1.1.1.1")
    await limiter.check("1.1.1.1")

    rejected = await limiter.check("1.1.1.1")
    assert rejected.allowed is False
    assert rejected.remaining == 0
    assert 1 <= rejected.reset_seconds <= 10


@pytest.mark.asyncio
async def test_sliding_window_isolates_different_ips():
    """Verify distinct IPs have independent rate limiting buckets."""
    limiter = SlidingWindowRateLimiter(requests_per_window=1, window_seconds=60.0)

    res_a1 = await limiter.check("ip-a")
    assert res_a1.allowed is True

    res_a2 = await limiter.check("ip-a")
    assert res_a2.allowed is False

    # IP B should still be allowed
    res_b = await limiter.check("ip-b")
    assert res_b.allowed is True


@pytest.mark.asyncio
async def test_sliding_window_slides_and_resets():
    """Verify timestamps older than window are pruned to allow new requests."""
    limiter = SlidingWindowRateLimiter(requests_per_window=2, window_seconds=1.0)

    await limiter.check("1.1.1.1")
    await limiter.check("1.1.1.1")
    assert (await limiter.check("1.1.1.1")).allowed is False

    # Wait for window to expire
    await asyncio.sleep(1.05)

    res_after = await limiter.check("1.1.1.1")
    assert res_after.allowed is True
    assert res_after.remaining == 1


@pytest.mark.asyncio
async def test_sliding_window_disabled():
    """Verify disabled limiter always permits requests."""
    limiter = SlidingWindowRateLimiter(
        requests_per_window=1, window_seconds=60.0, enabled=False
    )
    for _ in range(5):
        res = await limiter.check("1.1.1.1")
        assert res.allowed is True


@pytest.mark.asyncio
async def test_sliding_window_stale_cleanup():
    """Verify stale keys are pruned during cleanup."""
    limiter = SlidingWindowRateLimiter(requests_per_window=2, window_seconds=1.0)
    await limiter.check("old-ip")
    assert "old-ip" in limiter._records

    # Simulate time advancing 10 seconds and trigger cleanup
    limiter._cleanup_stale(now=limiter._records["old-ip"][0] + 10.0)
    assert "old-ip" not in limiter._records


@pytest.mark.asyncio
async def test_check_rate_limit_dependency_exceeded():
    """Verify check_rate_limit raises 429 with standard headers when limit tripped."""
    limiter = SlidingWindowRateLimiter(requests_per_window=1, window_seconds=30.0)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/chat",
        "headers": Headers({"x-forwarded-for": "10.0.0.99"}).raw,
        "client": ("10.0.0.99", 54321),
    }
    request = Request(scope)

    # First request passes
    first = await check_rate_limit(request, limiter=limiter)
    assert first.allowed is True

    # Second request raises HTTPException 429
    with pytest.raises(HTTPException) as exc_info:
        await check_rate_limit(request, limiter=limiter)

    assert exc_info.value.status_code == 429
    assert "Rate limit reached" in exc_info.value.detail
    headers = exc_info.value.headers
    assert headers is not None
    assert "Retry-After" in headers
    assert headers["X-RateLimit-Limit"] == "1"
    assert headers["X-RateLimit-Remaining"] == "0"
