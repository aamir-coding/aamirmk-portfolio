"""Write minimal recruiter analytics without waiting for Postgres in a response."""

import asyncio
import hmac
import logging
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, Request
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import MessageRecord, RecruiterSession
from app.safety.ip import get_client_ip
from app.telemetry import RequestTelemetry

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _Event:
    session_id: UUID
    ip_hash: str
    device_class: str
    company_slug: str | None
    at: datetime
    question: str | None
    latency_ms: float | None
    input_tokens: int | None
    output_tokens: int | None


class AnalyticsWriter:
    def __init__(self, sessions: async_sessionmaker[AsyncSession], key: bytes) -> None:
        self.sessions = sessions
        self.key = key
        self._queue: asyncio.Queue[_Event] = asyncio.Queue(maxsize=128)
        self._worker = asyncio.create_task(self._run())

    def enqueue(self, event: _Event) -> None:
        with suppress(asyncio.QueueFull):
            self._queue.put_nowait(event)

    async def _run(self) -> None:
        failed = False
        while True:
            event = await self._queue.get()
            try:
                await self._write(event)
                failed = False
            except Exception as exc:
                if not failed:
                    logger.warning(
                        "Analytics write unavailable: %s", type(exc).__name__
                    )
                failed = True
            finally:
                self._queue.task_done()

    async def _write(self, event: _Event) -> None:
        visit = insert(RecruiterSession).values(
            id=event.session_id,
            ip_hash=event.ip_hash,
            device_class=event.device_class,
            company_slug=event.company_slug,
            opened_at=event.at if event.question is None else None,
            last_seen_at=event.at,
        )
        async with self.sessions.begin() as session:
            await session.execute(
                visit.on_conflict_do_update(
                    index_elements=[RecruiterSession.id],
                    set_={
                        "opened_at": func.coalesce(
                            RecruiterSession.opened_at, visit.excluded.opened_at
                        ),
                        "last_seen_at": func.greatest(
                            RecruiterSession.last_seen_at, visit.excluded.last_seen_at
                        ),
                    },
                )
            )
            if event.question is not None:
                session.add(
                    MessageRecord(
                        session_id=event.session_id,
                        question=event.question,
                        latency_ms=event.latency_ms,
                        input_tokens=event.input_tokens,
                        output_tokens=event.output_tokens,
                        created_at=event.at,
                    )
                )

    async def close(self) -> None:
        try:
            with suppress(TimeoutError):
                await asyncio.wait_for(self._queue.join(), timeout=3)
        finally:
            self._worker.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker


@dataclass(frozen=True, slots=True)
class AnalyticsRequest:
    writer: AnalyticsWriter
    tab_id: str
    ip_hash: str
    device_class: str

    def record(
        self,
        company_slug: str | None,
        *,
        question: str | None = None,
        telemetry: RequestTelemetry | None = None,
    ) -> None:
        session_key = f"session\n{self.ip_hash}\n{self.tab_id}\n{company_slug or ''}"
        session_id = UUID(
            bytes=hmac.digest(self.writer.key, session_key.encode(), "sha256")[:16]
        )
        self.writer.enqueue(
            _Event(
                session_id=session_id,
                ip_hash=self.ip_hash,
                device_class=self.device_class,
                company_slug=company_slug,
                at=datetime.now(UTC),
                question=question.replace("\x00", " ")
                if question is not None
                else None,
                latency_ms=telemetry.total_ms if telemetry else None,
                input_tokens=telemetry.input_tokens if telemetry else None,
                output_tokens=telemetry.output_tokens if telemetry else None,
            )
        )


def _device_class(agent: str) -> str:
    agent = agent[:512].lower()
    if any(term in agent for term in ("android", "iphone", "ipad", "mobile")):
        return "mobile"
    if any(term in agent for term in ("windows", "macintosh", "linux", "x11")):
        return "desktop"
    return "unknown"


async def get_analytics(request: Request) -> AnalyticsRequest | None:
    writer: AnalyticsWriter | None = request.app.state.analytics
    if writer is None:
        return None
    ip = get_client_ip(request)
    ip_hash = hmac.digest(writer.key, f"ip\n{ip}".encode(), "sha256").hex()
    return AnalyticsRequest(
        writer=writer,
        tab_id=request.headers.get("X-Session-ID") or uuid4().hex,
        ip_hash=ip_hash,
        device_class=_device_class(request.headers.get("User-Agent", "")),
    )


Analytics = Annotated[AnalyticsRequest | None, Depends(get_analytics)]
