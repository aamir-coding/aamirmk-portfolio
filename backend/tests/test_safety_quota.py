"""Tests for daily quota guard (requests and token limits)."""

from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.safety.quota import DailyQuotaGuard, check_daily_quota


@pytest.mark.asyncio
async def test_quota_guard_under_limits():
    """Verify guard permits requests when usage is below daily caps."""
    guard = DailyQuotaGuard(max_requests_per_day=5, max_tokens_per_day=1000)

    # Initial check passes
    await guard.check()

    # Record some usage
    await guard.record_usage(tokens=200)
    status = await guard.get_status()
    assert status.requests_used == 1
    assert status.tokens_used == 200
    assert status.is_exhausted is False

    # Should still pass
    await guard.check()


@pytest.mark.asyncio
async def test_quota_guard_reaches_request_limit():
    """Verify guard raises 429 when daily request limit is reached."""
    guard = DailyQuotaGuard(max_requests_per_day=2, max_tokens_per_day=1000)

    await guard.record_usage(tokens=10)
    await guard.record_usage(tokens=10)

    status = await guard.get_status()
    assert status.requests_used == 2
    assert status.is_exhausted is True

    with pytest.raises(HTTPException) as exc_info:
        await guard.check()

    assert exc_info.value.status_code == 429
    assert "Daily assistant conversation capacity reached" in exc_info.value.detail
    headers = exc_info.value.headers
    assert headers is not None
    assert "Retry-After" in headers
    assert headers["X-Quota-Daily-Limit"] == "2"
    assert headers["X-Quota-Daily-Remaining"] == "0"


@pytest.mark.asyncio
async def test_quota_guard_reaches_token_limit():
    """Verify guard raises 429 when daily token limit is reached."""
    guard = DailyQuotaGuard(max_requests_per_day=100, max_tokens_per_day=500)

    await guard.record_usage(tokens=500)

    status = await guard.get_status()
    assert status.tokens_used == 500
    assert status.is_exhausted is True

    with pytest.raises(HTTPException) as exc_info:
        await guard.check()

    assert exc_info.value.status_code == 429
    assert "Daily token processing capacity reached" in exc_info.value.detail


@pytest.mark.asyncio
async def test_quota_guard_midnight_rollover():
    """Verify counters reset when calendar date rolls over."""
    guard = DailyQuotaGuard(max_requests_per_day=2, max_tokens_per_day=100)
    await guard.record_usage(tokens=100)

    status = await guard.get_status()
    assert status.requests_used == 1
    assert status.tokens_used == 100

    # Simulate previous day
    yesterday = date.today() - timedelta(days=1)
    guard._current_date = yesterday

    # Next check should detect rollover and reset
    await guard.check()
    new_status = await guard.get_status()
    assert new_status.requests_used == 0
    assert new_status.tokens_used == 0


@pytest.mark.asyncio
async def test_check_daily_quota_dependency():
    """Verify check_daily_quota dependency integrates with guard."""
    guard = DailyQuotaGuard(max_requests_per_day=1, max_tokens_per_day=100)
    await check_daily_quota(guard=guard)

    await guard.record_usage(tokens=50)

    with pytest.raises(HTTPException) as exc_info:
        await check_daily_quota(guard=guard)

    assert exc_info.value.status_code == 429
