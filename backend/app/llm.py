"""Thin async LLM adapter — the seam between the app and Groq.

Interface: a single `complete(messages) → AssistantMessage` method.
Implementation details hidden behind the seam: API key, model selection,
client lifecycle, timeouts, error mapping. Tests inject a FakeLLM that
satisfies the same protocol — no real Groq calls in CI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from fastapi import Depends
from groq import AsyncGroq

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


# ── Value objects ──────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Message:
    """A single chat message (role + content)."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True, slots=True)
class AssistantMessage:
    """The reply from the LLM, plus lightweight usage metadata."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# ── LLM errors ─────────────────────────────────────────────────────────


class LLMError(Exception):
    """Base error for all LLM-related failures."""


class LLMRateLimitError(LLMError):
    """Groq rate limit (429) hit."""


class LLMAuthError(LLMError):
    """Invalid or missing API key (401)."""


class LLMUnavailableError(LLMError):
    """Upstream service unavailable (503/500/connection)."""


# ── Protocol (the seam) ───────────────────────────────────────────────


class LLMClient(Protocol):
    """Protocol that both GroqLLM and FakeLLM satisfy."""

    async def complete(self, messages: list[Message]) -> AssistantMessage: ...


# ── Real adapter ───────────────────────────────────────────────────────


class GroqLLM:
    """Production adapter wrapping the Groq AsyncGroq client.

    Accepts dependencies via __init__ — never reads globals or env directly.
    """

    def __init__(self, settings: Settings) -> None:
        self._model = settings.LLM_MODEL_MAIN
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def complete(self, messages: list[Message]) -> AssistantMessage:
        """Send messages to Groq and return the assistant reply."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=0.4,
                max_completion_tokens=1024,
            )
        except Exception as exc:
            self._map_error(exc)

        choice = response.choices[0]
        usage = response.usage

        return AssistantMessage(
            content=choice.message.content or "",
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )

    def _map_error(self, exc: Exception) -> None:
        """Translate Groq SDK exceptions into our domain errors."""
        from groq import AuthenticationError, RateLimitError

        if isinstance(exc, RateLimitError):
            raise LLMRateLimitError(str(exc)) from exc
        if isinstance(exc, AuthenticationError):
            raise LLMAuthError(str(exc)) from exc
        raise LLMUnavailableError(str(exc)) from exc


# ── Fake adapter (for tests) ──────────────────────────────────────────


class FakeLLM:
    """In-memory fake satisfying LLMClient for deterministic tests.

    Instantiate with a canned reply; optionally inspect captured messages.
    """

    def __init__(
        self,
        reply: str = "Fake reply",
        model: str = "fake-model",
    ) -> None:
        self.reply = reply
        self.model = model
        self.last_messages: list[Message] = []

    async def complete(self, messages: list[Message]) -> AssistantMessage:
        self.last_messages = list(messages)
        return AssistantMessage(
            content=self.reply,
            model=self.model,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Dependency provider returning production LLM client."""
    return GroqLLM(settings)
