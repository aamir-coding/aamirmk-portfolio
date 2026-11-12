"""Bind a durable daily reservation to the boot-local inference ledger."""

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, time, timedelta
from typing import Protocol

from app.safety.admission import (
    Allowance,
    DailyCapacity,
    InferenceLedger,
    SettledAllowance,
)

logger = logging.getLogger(__name__)


class QuotaStorageUnavailable(Exception):
    """The reservation could not be confirmed in storage."""


class DurableCapacityUnavailable(Exception):
    """No durable grant fits the available capacity."""


class QuotaStore(Protocol):
    async def reserve(
        self, requested: Allowance, ceiling: DailyCapacity, *, exact: bool
    ) -> Allowance | None: ...

    async def settle(self, settlement: SettledAllowance) -> bool: ...


class BootQuota:
    def __init__(
        self,
        ledger: InferenceLedger,
        store: QuotaStore,
        ceiling: DailyCapacity,
        boot_allowance: DailyCapacity,
    ) -> None:
        self._ledger = ledger
        self._store = store
        self._ceiling = ceiling
        self._boot_allowance = boot_allowance
        self._lock = asyncio.Lock()
        self._automatic: asyncio.Task[None] | None = None

    async def authorize(self, requested: Allowance | None = None) -> Allowance:
        async with self._lock:
            exact = requested is not None
            if requested is None:
                now = self._ledger.utcnow()
                midnight = datetime.combine(
                    now.date() + timedelta(days=1), time.min, UTC
                )
                requested = Allowance(
                    boot_id=self._ledger.boot_id,
                    verified_at=now,
                    expires_at=midnight,
                    requests=self._boot_allowance.requests,
                    tokens=self._boot_allowance.tokens,
                )
            self._ledger.validate_allowance(requested)
            granted = await self._store.reserve(requested, self._ceiling, exact=exact)
            if granted is None:
                raise DurableCapacityUnavailable
            if not exact and self._ledger.utcnow() >= granted.expires_at:
                raise DurableCapacityUnavailable
            self._ledger.authorize(granted)
            return granted

    def start(self) -> None:
        self._automatic = asyncio.create_task(self._authorize_when_available())

    async def _authorize_when_available(self) -> None:
        previous: str | None = None
        while True:
            try:
                await self.authorize()
            except QuotaStorageUnavailable:
                reason = "storage unavailable"
            except DurableCapacityUnavailable:
                reason = "daily capacity unavailable"
            except ValueError:
                # A manual activation or a closed ledger ends automatic admission.
                return
            else:
                logger.info("Durable inference grant activated for this boot")
                return
            if reason != previous:
                logger.warning("Durable inference grant pending: %s", reason)
                previous = reason
            await asyncio.sleep(30)

    async def close(self) -> None:
        if self._automatic is not None:
            self._automatic.cancel()
            with suppress(asyncio.CancelledError):
                await self._automatic
        async with self._lock:
            settlement = self._ledger.seal()
            if settlement is not None:
                try:
                    await self._store.settle(settlement)
                except QuotaStorageUnavailable:
                    logger.warning(
                        "Durable grant settlement unavailable; capacity held"
                    )
