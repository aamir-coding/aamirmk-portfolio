"""Behavioral contracts for per-attempt inference admission; no provider calls."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.safety.admission import (
    Allowance,
    AttemptCost,
    CapacityLimits,
    DailyCapacity,
    InferenceLedger,
    ProviderUsage,
    QuotaDenied,
    SettledAllowance,
    reserve_input_tokens,
)
from app.safety.boot_quota import BootQuota, QuotaStorageUnavailable

MAIN = "openai/gpt-oss-120b"
UTILITY = "openai/gpt-oss-20b"


class Clock:
    def __init__(self) -> None:
        self.elapsed = 0.0
        self.start = datetime(2026, 11, 6, 12, tzinfo=UTC)

    def monotonic(self) -> float:
        return self.elapsed

    def utcnow(self) -> datetime:
        return self.start + timedelta(seconds=self.elapsed)

    async def sleep(self, seconds: float) -> None:
        self.elapsed += seconds
        await asyncio.sleep(0)


def limits(**changes: int) -> CapacityLimits:
    values = {"rpm": 10, "tpm": 1000, "rpd": 100, "tpd": 10000}
    return CapacityLimits(**(values | changes))


async def test_sealed_ledger_accounts_for_unknown_attempt_and_stops_dispatch() -> None:
    clock = Clock()
    book = ledger(clock)
    cost = AttemptCost(model=MAIN, input_tokens=100, output_tokens=20)
    async with book.attempt(cost) as permit:
        permit.dispatch()
    settlement = book.seal()
    assert settlement is not None
    assert (settlement.requests, settlement.tokens) == (1, 120)
    assert book.seal() is None
    with pytest.raises(QuotaDenied, match="allowance_closed"):
        async with book.attempt(cost):
            pytest.fail("The sealed grant is still usable")


async def test_sealing_an_active_grant_keeps_the_full_reservation() -> None:
    clock = Clock()
    book = ledger(clock)
    cost = AttemptCost(model=MAIN, input_tokens=100, output_tokens=20)
    async with book.attempt(cost) as permit:
        assert book.seal() is None
        with pytest.raises(QuotaDenied, match="allowance_closed"):
            permit.dispatch()


async def test_active_grant_survives_storage_failure_until_utc_midnight() -> None:
    class Store:
        available = False
        reservations = 0
        settlement: SettledAllowance | None = None

        async def reserve(
            self, requested: Allowance, ceiling: DailyCapacity, *, exact: bool
        ) -> Allowance:
            self.reservations += 1
            if not self.available:
                raise QuotaStorageUnavailable
            assert exact and requested.tokens <= ceiling.tokens
            return requested

        async def settle(self, settlement: SettledAllowance) -> bool:
            self.settlement = settlement
            raise QuotaStorageUnavailable

    clock = Clock()
    book = ledger(clock, authorize=False)
    store = Store()
    daily = DailyCapacity(requests=2, tokens=1000)
    quota = BootQuota(book, store, daily, daily)
    midnight = clock.start.replace(hour=0) + timedelta(days=1)
    requested = Allowance(
        **daily.model_dump(),
        boot_id=book.boot_id,
        verified_at=clock.utcnow(),
        expires_at=midnight,
    )
    with pytest.raises(QuotaStorageUnavailable):
        await quota.authorize(requested)
    assert book.snapshot().reason == "allowance_unknown"
    store.available = True
    assert await quota.authorize(requested) == requested
    clock.elapsed += 60
    store.available = False
    cost = AttemptCost(model=MAIN, input_tokens=100, output_tokens=20)
    async with book.attempt(cost) as permit:
        permit.dispatch()
    assert book.snapshot().charged_tokens == 120
    assert store.reservations == 2
    clock.elapsed = (midnight - clock.start).total_seconds()
    with pytest.raises(QuotaDenied, match="allowance_expired"):
        async with book.attempt(cost):
            pytest.fail("The expired grant is still usable")
    await quota.close()
    assert store.settlement == SettledAllowance(requested, 1, 120)


def ledger(
    clock: Clock,
    *,
    shared: CapacityLimits | None = None,
    model: CapacityLimits | None = None,
    authorize: bool = True,
    max_active: int = 10,
    max_waiters: int = 4,
) -> InferenceLedger:
    result = InferenceLedger(
        shared=shared or limits(),
        models={MAIN: model or limits(), UTILITY: model or limits()},
        monotonic=clock.monotonic,
        utcnow=clock.utcnow,
        sleep=clock.sleep,
        max_active=max_active,
        max_waiters=max_waiters,
    )
    if authorize:
        result.authorize(
            Allowance(
                boot_id=result.boot_id,
                verified_at=clock.utcnow(),
                expires_at=clock.utcnow() + timedelta(hours=1),
                requests=100,
                tokens=10000,
            )
        )
        clock.elapsed += 60  # Unknown provider minute usage must drain first.
    return result


def cost(model: str = MAIN, input_tokens: int = 60) -> AttemptCost:
    return AttemptCost(model=model, input_tokens=input_tokens, output_tokens=40)


async def spend(subject: InferenceLedger, request: AttemptCost) -> None:
    async with subject.attempt(request) as permit:
        permit.dispatch()


@pytest.mark.asyncio
async def test_unknown_startup_and_restart_do_not_mint_capacity() -> None:
    clock = Clock()
    first = ledger(clock)
    restarted = ledger(clock, authorize=False)
    with pytest.raises(QuotaDenied, match="allowance_unknown"):
        await spend(restarted, cost())
    with pytest.raises(ValueError, match="boot"):
        restarted.authorize(
            Allowance(
                boot_id=first.boot_id,
                verified_at=clock.utcnow(),
                expires_at=clock.utcnow() + timedelta(minutes=10),
                requests=5,
                tokens=500,
            )
        )


@pytest.mark.asyncio
async def test_concurrent_attempts_cannot_oversubscribe_shared_or_model_budget() -> (
    None
):
    clock = Clock()
    subject = ledger(clock, shared=limits(tpd=150))
    start = asyncio.Event()

    async def compete(model: str) -> bool:
        await start.wait()
        try:
            await spend(subject, cost(model))
        except QuotaDenied:
            return False
        return True

    tasks = [asyncio.create_task(compete(m)) for m in [MAIN, UTILITY] * 8]
    start.set()
    assert sum(await asyncio.gather(*tasks)) == 1
    assert subject.snapshot().charged_tokens == 100
    assert subject.snapshot().attempts == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("cap", ["rpm", "tpm", "rpd", "tpd"])
async def test_each_model_limit_is_enforced_even_with_shared_headroom(cap: str) -> None:
    clock = Clock()
    subject = ledger(clock, model=limits(**{cap: 1 if "r" in cap else 100}))
    await spend(subject, cost())
    with pytest.raises(QuotaDenied):
        await spend(subject, cost())
    await spend(subject, cost(UTILITY))


@pytest.mark.asyncio
async def test_full_usage_reconciles_once_and_preserves_request_charge() -> None:
    clock = Clock()
    subject = ledger(clock, shared=limits(tpd=150))
    async with subject.attempt(cost()) as permit:
        permit.dispatch()
        usage = ProviderUsage(input_tokens=10, output_tokens=10, total_tokens=20)
        permit.settle(usage)
        permit.settle(usage)
        with pytest.raises(ValueError, match="settled"):
            permit.settle(
                ProviderUsage(input_tokens=1, output_tokens=1, total_tokens=2)
            )
    await spend(subject, cost())
    assert subject.snapshot().charged_tokens == 120
    assert subject.snapshot().attempts == 2


@pytest.mark.asyncio
async def test_pre_dispatch_cancellation_releases_hold_but_unknown_call_keeps_it() -> (
    None
):
    clock = Clock()
    subject = ledger(clock, shared=limits(tpd=100))
    with pytest.raises(asyncio.CancelledError):
        async with subject.attempt(cost()):
            raise asyncio.CancelledError
    assert subject.snapshot().charged_tokens == 0
    assert subject.snapshot().attempts == 0
    with pytest.raises(asyncio.CancelledError):
        async with subject.attempt(cost()) as permit:
            permit.dispatch()
            raise asyncio.CancelledError
    assert subject.snapshot().charged_tokens == 100
    assert subject.snapshot().active == 0
    with pytest.raises(QuotaDenied):
        await spend(subject, cost())


@pytest.mark.asyncio
async def test_reported_overrun_stops_admission_and_keeps_actual_usage() -> None:
    clock = Clock()
    subject = ledger(clock)
    async with subject.attempt(cost()) as permit:
        permit.dispatch()
        permit.settle(
            ProviderUsage(input_tokens=70, output_tokens=50, total_tokens=120)
        )
    assert subject.snapshot().charged_tokens == 120
    with pytest.raises(QuotaDenied, match="usage_overrun"):
        await spend(subject, cost())


@pytest.mark.asyncio
async def test_impossible_prompt_is_rejected_without_wait_or_charge() -> None:
    clock = Clock()
    subject = ledger(clock)
    before = clock.elapsed
    with pytest.raises(QuotaDenied, match="request_too_large"):
        async with subject.attempt(cost(input_tokens=1000), wait_seconds=60):
            pytest.fail("must not dispatch")
    assert clock.elapsed == before
    assert subject.snapshot().charged_tokens == 0


@pytest.mark.asyncio
async def test_rolling_minute_waits_then_expires_but_daily_spending_remains() -> None:
    clock = Clock()
    subject = ledger(clock, shared=limits(rpm=1))
    await spend(subject, cost())
    with pytest.raises(QuotaDenied, match="minute_capacity"):
        async with subject.attempt(cost(), wait_seconds=59):
            pytest.fail("deadline must expire")
    assert subject.snapshot().attempts == 1
    async with subject.attempt(cost(), wait_seconds=1) as permit:
        permit.dispatch()
    assert subject.snapshot().attempts == 2
    assert subject.snapshot().charged_tokens == 200


@pytest.mark.asyncio
async def test_allowance_expires_at_midnight_without_resetting_daily_charges() -> None:
    clock = Clock()
    clock.start = datetime(2026, 11, 6, 23, 58, tzinfo=UTC)
    subject = ledger(clock, authorize=False)
    subject.authorize(
        Allowance(
            boot_id=subject.boot_id,
            verified_at=clock.utcnow(),
            expires_at=datetime(2026, 11, 7, tzinfo=UTC),
            requests=5,
            tokens=500,
        )
    )
    clock.elapsed = 60
    await spend(subject, cost())
    clock.elapsed = 120
    with pytest.raises(QuotaDenied, match="allowance_expired"):
        await spend(subject, cost())
    assert subject.snapshot().charged_tokens == 100


@pytest.mark.asyncio
async def test_queue_is_bounded_and_cancelled_waiter_leaves_no_hold() -> None:
    clock = Clock()
    subject = ledger(clock, max_active=1, max_waiters=1)
    sleeping = asyncio.Event()
    release = asyncio.Event()

    async def blocked_sleep(seconds: float) -> None:
        sleeping.set()
        await release.wait()

    subject.sleep = blocked_sleep
    async with subject.attempt(cost()) as permit:
        permit.dispatch()
        queued = asyncio.create_task(spend_waiting(subject))
        await sleeping.wait()
        with pytest.raises(QuotaDenied, match="queue_full"):
            async with subject.attempt(cost(), wait_seconds=1):
                pytest.fail("queue must be full")
        queued.cancel()
        with pytest.raises(asyncio.CancelledError):
            await queued
        assert subject.snapshot().waiting == 0
        assert subject.snapshot().charged_tokens == 100


async def spend_waiting(subject: InferenceLedger) -> None:
    async with subject.attempt(cost(), wait_seconds=10) as permit:
        permit.dispatch()


@pytest.mark.asyncio
async def test_dispatch_rechecks_expiry_and_cannot_reuse_closed_permit() -> None:
    clock = Clock()
    subject = ledger(clock)
    async with subject.attempt(cost()) as permit:
        clock.elapsed = 3600
        with pytest.raises(QuotaDenied, match="allowance_expired"):
            permit.dispatch()
    with pytest.raises(ValueError, match="closed"):
        permit.dispatch()
    assert subject.snapshot().charged_tokens == 0


def test_invalid_usage_and_limits_fail_closed() -> None:
    with pytest.raises(ValidationError):
        ProviderUsage(input_tokens=1, output_tokens=2, total_tokens=4)
    with pytest.raises(ValidationError):
        cost(input_tokens=-1)
    with pytest.raises(ValidationError):
        limits(rpm=True)


def test_input_reservation_includes_utf8_tools_and_message_overhead() -> None:
    payload = {
        "messages": [{"role": "user", "content": "\u4f60\u597d"}],
        "tools": [{"x": "y"}],
    }
    assert reserve_input_tokens(payload) > len(str(payload).encode("utf-8"))
    assert reserve_input_tokens(payload) > reserve_input_tokens({"messages": []})


def test_allowance_is_fresh_boot_bound_and_cannot_be_reopened() -> None:
    clock = Clock()
    subject = ledger(clock)
    with pytest.raises(ValueError, match="already"):
        subject.authorize(
            Allowance(
                boot_id=subject.boot_id,
                verified_at=clock.utcnow(),
                expires_at=clock.utcnow() + timedelta(minutes=10),
                requests=100,
                tokens=10000,
            )
        )


@pytest.mark.asyncio
async def test_initial_provider_minute_is_unknown_even_after_daily_authorization() -> (
    None
):
    clock = Clock()
    subject = ledger(clock)
    clock.elapsed = 0
    with pytest.raises(QuotaDenied, match="minute_capacity"):
        await spend(subject, cost())
    async with subject.attempt(cost(), wait_seconds=60) as permit:
        permit.dispatch()
    assert clock.elapsed == 60


@pytest.mark.asyncio
async def test_two_identical_holds_cancel_independently() -> None:
    clock = Clock()
    subject = ledger(clock, shared=limits(rpd=2))
    async with subject.attempt(cost()) as first:
        async with subject.attempt(cost()):
            pass
        first.dispatch()
        assert subject.snapshot().attempts == 1
    await spend(subject, cost())
    assert subject.snapshot().attempts == 2


@pytest.mark.parametrize("seconds", [-1, 61, float("inf"), float("nan")])
@pytest.mark.asyncio
async def test_invalid_wait_bounds_fail_without_admission(seconds: float) -> None:
    subject = ledger(Clock())
    with pytest.raises(ValueError, match="Wait"):
        async with subject.attempt(cost(), wait_seconds=seconds):
            pytest.fail("invalid wait")
    assert subject.snapshot().charged_tokens == 0


def test_allowance_rejects_naive_dates_and_cross_day_expiry() -> None:
    now = datetime(2026, 11, 6, 12, tzinfo=UTC)
    for verified, expiry in [
        (now.replace(tzinfo=None), now + timedelta(minutes=5)),
        (now, now + timedelta(days=1)),
    ]:
        with pytest.raises(ValidationError):
            Allowance(
                boot_id="test",
                verified_at=verified,
                expires_at=expiry,
                requests=1,
                tokens=100,
            )


@pytest.mark.asyncio
async def test_unsupported_model_cannot_spend_capacity() -> None:
    subject = ledger(Clock())
    with pytest.raises(QuotaDenied, match="model_not_allowed"):
        await spend(subject, cost("unknown"))
    assert subject.snapshot().charged_tokens == 0


@pytest.mark.asyncio
async def test_late_queue_wakeup_cannot_admit_after_deadline() -> None:
    clock = Clock()
    subject = ledger(clock, shared=limits(rpm=1))
    await spend(subject, cost())

    async def delayed_sleep(seconds: float) -> None:
        clock.elapsed += 65

    subject.sleep = delayed_sleep
    with pytest.raises(QuotaDenied, match="wait_expired"):
        async with subject.attempt(cost(), wait_seconds=1):
            pytest.fail("late wake admitted a provider call")
    assert subject.snapshot().attempts == 1
    assert subject.snapshot().waiting == 0
