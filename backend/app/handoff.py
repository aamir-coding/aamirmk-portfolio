"""Validate, persist, and deliver a visitor-approved handoff."""

import asyncio
import logging
import re
from contextlib import suppress
from typing import Literal, Protocol

import httpx
from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import HandoffRecord
from app.safety.guardrails import valid_unicode

logger = logging.getLogger(__name__)


class HandoffMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("Messages must contain valid text")
        return valid_unicode(value)


class HandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    consent: StrictBool
    website: Literal[""] = ""
    reply_email: str | None = Field(default=None, max_length=254)
    transcript: list[HandoffMessage] = Field(min_length=1, max_length=10)

    @field_validator("reply_email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not re.fullmatch(
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}"
            r"@(?:[A-Za-z0-9-]+\.)+[A-Za-z0-9-]{2,63}",
            value,
        ):
            raise ValueError("Enter a valid reply email")
        return value

    @model_validator(mode="after")
    def validate_consent(self) -> "HandoffRequest":
        if not self.consent:
            raise ValueError("Consent is required to share a transcript")
        if all(message.role != "user" for message in self.transcript):
            raise ValueError("Include at least one visitor message")
        return self


class HandoffConflict(Exception):
    """A submission ID is already associated with different content."""


class HandoffNotifier(Protocol):
    async def send(self, handoff: HandoffRecord) -> None: ...


class TelegramNotifier:
    def __init__(self, client: httpx.AsyncClient, token: str, chat_id: str) -> None:
        self._client = client
        self._url = f"https://api.telegram.org/bot{token}"
        self._chat_id = chat_id

    async def send(self, handoff: HandoffRecord) -> None:
        lines = [f"Portfolio handoff {handoff.id}", "Visitor-provided transcript"]
        if handoff.reply_email:
            lines.append(f"Reply email: {handoff.reply_email}")
        for message in handoff.transcript:
            label = "Visitor" if message["role"] == "user" else "Assistant"
            lines.append(f"{label}: {message['content']}")
        text = "\n\n".join(lines)
        if len(text.encode("utf-16-le")) <= 8192:
            response = await self._client.post(
                f"{self._url}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "link_preview_options": {"is_disabled": True},
                },
            )
        else:
            response = await self._client.post(
                f"{self._url}/sendDocument",
                data={"chat_id": self._chat_id, "caption": lines[0]},
                files={
                    "document": ("transcript.txt", text.encode("utf-8"), "text/plain")
                },
            )
        if not response.is_success or response.json().get("ok") is not True:
            raise RuntimeError("Telegram did not accept the handoff")


class Handoffs:
    """Use committed pending rows as the delivery queue."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        notifier: HandoffNotifier,
    ) -> None:
        self._sessions = sessions
        self._notifier = notifier
        self._wake = asyncio.Event()
        self._worker = asyncio.create_task(self._run())

    async def accept(self, payload: HandoffRequest) -> None:
        transcript = [message.model_dump() for message in payload.transcript]
        statement = (
            insert(HandoffRecord)
            .values(
                id=payload.id, reply_email=payload.reply_email, transcript=transcript
            )
            .on_conflict_do_nothing(index_elements=[HandoffRecord.id])
            .returning(HandoffRecord.id)
        )
        async with self._sessions.begin() as session:
            if await session.scalar(statement) is None:
                existing = await session.get(HandoffRecord, payload.id)
                if (
                    existing is None
                    or existing.reply_email != payload.reply_email
                    or existing.transcript != transcript
                ):
                    raise HandoffConflict
        self._wake.set()

    async def _run(self) -> None:
        unavailable = False
        while True:
            self._wake.clear()
            try:
                while await self._deliver_one():
                    pass
                unavailable = False
            except Exception as exc:
                if not unavailable:
                    logger.warning("Handoff queue unavailable: %s", type(exc).__name__)
                unavailable = True
            with suppress(TimeoutError):
                await asyncio.wait_for(self._wake.wait(), timeout=30)

    async def _deliver_one(self) -> bool:
        async with self._sessions.begin() as session:
            handoff = await session.scalar(
                select(HandoffRecord)
                .where(HandoffRecord.delivery_status == "pending")
                .order_by(HandoffRecord.created_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if handoff is None:
                return False
            try:
                async with asyncio.timeout(12):
                    await self._notifier.send(handoff)
            except Exception as exc:
                logger.warning(
                    "Handoff %s delivery failed: %s", handoff.id, type(exc).__name__
                )
                handoff.delivery_status = "failed"
            else:
                handoff.delivery_status = "sent"
        return True

    async def close(self) -> None:
        self._worker.cancel()
        with suppress(asyncio.CancelledError):
            await self._worker
