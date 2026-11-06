"""Single-event-loop inference accounting, independent of HTTP and provider SDKs.

All accounting transitions are synchronous, with no await between admission and
reservation. Only bounded waiting yields. Own one ledger per app lifespan; do not
share it between threads, workers or standalone eval processes.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdmissionModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


class CapacityLimits(AdmissionModel):
    rpm: int = Field(gt=0, strict=True)
    tpm: int = Field(gt=0, strict=True)
    rpd: int = Field(gt=0, strict=True)
    tpd: int = Field(gt=0, strict=True)


class Allowance(AdmissionModel):
    """Operator-confirmed *remaining* capacity for this one process boot."""

    boot_id: str = Field(min_length=1, max_length=64)
    verified_at: datetime
    expires_at: datetime
    requests: int = Field(gt=0, strict=True)
    tokens: int = Field(gt=0, strict=True)

    @model_validator(mode="after")
    def utc_window(self) -> Self:
        for value in (self.verified_at, self.expires_at):
            if value.utcoffset() != timedelta(0):
                raise ValueError("Allowance timestamps must be UTC-aware")
        midnight = datetime.combine(
            self.verified_at.date() + timedelta(days=1), datetime.min.time(), UTC
        )
        if not self.verified_at < self.expires_at <= midnight:
            raise ValueError("Allowance must expire by the next UTC midnight")
        return self


class AttemptCost(AdmissionModel):
    model: str = Field(min_length=1, max_length=128)
    input_tokens: int = Field(gt=0, strict=True)
    output_tokens: int = Field(gt=0, strict=True)

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


class ProviderUsage(AdmissionModel):
    input_tokens: int = Field(ge=0, strict=True)
    output_tokens: int = Field(ge=0, strict=True)
    total_tokens: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def reconciles(self) -> Self:
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("Reported usage does not reconcile")
        return self


class LedgerSnapshot(AdmissionModel):
    attempts: int
    charged_tokens: int
    active: int
    waiting: int
    reason: str | None


class QuotaDenied(Exception):
    """Safe machine-readable reason; retry delay is only for transient capacity."""

    def __init__(self, reason: str, retry_after: float | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.retry_after = retry_after


def reserve_input_tokens(payload: Mapping[str, object]) -> int:
    """UTF-8 request bytes plus framing headroom, not an exact tokenizer.

    Include the actual messages, tools and response schema sent to the provider.
    Byte-level reservation deliberately overestimates ordinary text. Provider chat
    framing is not public, so an observed overrun stops all subsequent admission.
    """
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    messages = payload.get("messages", [])
    count = len(messages) if isinstance(messages, list) else 0
    return len(encoded.encode("utf-8")) + 512 + 32 * count


@dataclass
class _Attempt:
    cost: AttemptCost
    reserved_at: float
    dispatched_at: float | None = None
    usage: ProviderUsage | None = None
    closed: bool = False

    @property
    def charged(self) -> int:
        if self.usage is None:
            return self.cost.total
        if (
            self.usage.input_tokens > self.cost.input_tokens
            or self.usage.output_tokens > self.cost.output_tokens
        ):
            return max(self.cost.total, self.usage.total_tokens)
        return self.usage.total_tokens


class AttemptPermit:
    """An attempt's lifecycle: dispatch immediately before I/O, then settle once."""

    def __init__(self, ledger: InferenceLedger, record: _Attempt) -> None:
        self._ledger = ledger
        self._record = record

    def dispatch(self) -> None:
        record = self._record
        if record.closed:
            raise ValueError("Attempt is closed")
        if record.dispatched_at is not None:
            raise ValueError("Attempt already dispatched")
        self._ledger._check_allowance()
        record.dispatched_at = self._ledger.monotonic()

    def settle(self, usage: ProviderUsage) -> None:
        record = self._record
        if record.closed or record.dispatched_at is None:
            raise ValueError("Attempt is closed or not dispatched")
        if record.usage is not None:
            if record.usage != usage:
                raise ValueError("Attempt already settled with different usage")
            return
        record.usage = usage
        if (
            usage.input_tokens > record.cost.input_tokens
            or usage.output_tokens > record.cost.output_tokens
        ):
            self._ledger._fault = "usage_overrun"


class InferenceLedger:
    """Atomic shared/model admission; no automatic allowance renewal or failover."""

    def __init__(
        self,
        *,
        shared: CapacityLimits,
        models: Mapping[str, CapacityLimits],
        max_active: int = 2,
        max_waiters: int = 8,
        monotonic: Callable[[], float] = time.monotonic,
        utcnow: Callable[[], datetime] = lambda: datetime.now(UTC),
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if not models or max_active < 1 or max_waiters < 0:
            raise ValueError("Models and bounded concurrency are required")
        self.boot_id = uuid.uuid4().hex
        self._shared = shared
        self._models = dict(models)
        self.monotonic = monotonic
        self.utcnow = utcnow
        self.sleep = sleep
        self._max_active = max_active
        self._max_waiters = max_waiters
        self._allowance: Allowance | None = None
        self._expires = 0.0
        self._ready = 0.0
        self._fault: str | None = None
        self._records: list[_Attempt] = []
        self._active = 0
        self._waiting = 0

    def authorize(self, allowance: Allowance) -> None:
        """One-shot boot-local activation; never load a reusable env allowance."""
        if self._allowance is not None:
            raise ValueError("Ledger already authorized")
        if allowance.boot_id != self.boot_id:
            raise ValueError("Allowance belongs to a different boot")
        now = self.utcnow()
        age = (now - allowance.verified_at).total_seconds()
        if not 0 <= age <= 60 or allowance.expires_at <= now:
            raise ValueError("Allowance verification is stale or in the future")
        self._allowance = allowance
        self._expires = self.monotonic() + (allowance.expires_at - now).total_seconds()
        # Previous provider-minute traffic is unknown even with verified daily use.
        self._ready = self.monotonic() + 60

    def _check_allowance(self) -> None:
        if self._fault is not None:
            raise QuotaDenied(self._fault)
        grant = self._allowance
        if grant is None:
            raise QuotaDenied("allowance_unknown")
        if (
            self.monotonic() >= self._expires
            or self.utcnow() >= grant.expires_at
            or self.utcnow() < grant.verified_at
        ):
            raise QuotaDenied("allowance_expired")

    def _reserve(self, cost: AttemptCost) -> _Attempt:
        self._check_allowance()
        grant = self._allowance
        assert grant is not None
        model_limit = self._models.get(cost.model)
        if model_limit is None:
            raise QuotaDenied("model_not_allowed")
        groups = (
            (self._shared, self._records),
            (model_limit, [r for r in self._records if r.cost.model == cost.model]),
        )
        for caps, records in groups:
            if cost.total > min(caps.tpm, caps.tpd):
                raise QuotaDenied("request_too_large")
            if len(records) >= min(caps.rpd, grant.requests) or (
                sum(r.charged for r in records) + cost.total
                > min(caps.tpd, grant.tokens)
            ):
                raise QuotaDenied("daily_capacity")
        now = self.monotonic()
        if now < self._ready:
            raise QuotaDenied("minute_capacity", self._ready - now)
        delays: list[float] = []
        for caps, records in groups:
            recent = [
                r
                for r in records
                if not r.closed
                or (r.dispatched_at is not None and r.dispatched_at > now - 60)
            ]
            if len(recent) >= caps.rpm or (
                sum(r.cost.total for r in recent) + cost.total > caps.tpm
            ):
                delays.extend(
                    max(0.05, (r.dispatched_at or r.reserved_at) + 60 - now)
                    for r in recent
                )
        if delays:
            raise QuotaDenied("minute_capacity", min(delays))
        if self._active >= self._max_active:
            raise QuotaDenied("concurrency_capacity", 0.05)
        record = _Attempt(cost=cost, reserved_at=now)
        self._records.append(record)
        self._active += 1
        return record

    @asynccontextmanager
    async def attempt(
        self, cost: AttemptCost, *, wait_seconds: float = 0
    ) -> AsyncIterator[AttemptPermit]:
        """Reserve atomically; cancellation releases only undispatched capacity."""
        if not math.isfinite(wait_seconds) or not 0 <= wait_seconds <= 60:
            raise ValueError("Wait must be finite and between zero and 60 seconds")
        deadline = self.monotonic() + wait_seconds
        queued = False
        try:
            while True:
                if queued and self.monotonic() > deadline:
                    raise QuotaDenied("wait_expired")
                try:
                    record = self._reserve(cost)
                    break
                except QuotaDenied as denial:
                    remaining = deadline - self.monotonic()
                    if denial.retry_after is None or remaining <= 0:
                        raise
                    if not queued:
                        if self._waiting >= self._max_waiters:
                            raise QuotaDenied("queue_full") from None
                        self._waiting += 1
                        queued = True
                    await self.sleep(min(denial.retry_after, remaining))
        finally:
            if queued:
                self._waiting -= 1
        try:
            yield AttemptPermit(self, record)
        finally:
            record.closed = True
            self._active -= 1
            if record.dispatched_at is None:
                self._records.remove(record)

    def snapshot(self) -> LedgerSnapshot:
        reason: str | None = None
        try:
            self._check_allowance()
        except QuotaDenied as denial:
            reason = denial.reason
        return LedgerSnapshot(
            attempts=sum(r.dispatched_at is not None for r in self._records),
            charged_tokens=sum(r.charged for r in self._records),
            active=self._active,
            waiting=self._waiting,
            reason=reason,
        )

    def stop(self, reason: Literal["model_mismatch", "provider_contract"]) -> None:
        """An invalid provider contract makes further local accounting unsafe."""
        self._fault = reason
