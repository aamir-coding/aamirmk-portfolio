"""Thin async LLM adapter — the seam between the app and Groq.

Interface: `complete(messages, tools=None) -> AssistantMessage`
           and `stream(messages, tools=None) -> AsyncIterator[str | ToolCall]`.
Implementation details hidden behind the seam: API key, model selection,
client lifecycle, timeouts, error mapping. Tests inject a FakeLLM that
satisfies the same protocol — no real Groq calls in CI.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol

from fastapi import Request
from groq import AsyncGroq
from pydantic import ValidationError

from app.safety.admission import (
    AttemptCost,
    InferenceLedger,
    ProviderUsage,
    QuotaDenied,
    reserve_input_tokens,
)
from app.settings import Settings

logger = logging.getLogger(__name__)


# ── Value objects ──────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool call requested by the LLM."""

    id: str
    name: str
    arguments: str  # JSON-encoded arguments string


@dataclass(frozen=True, slots=True)
class Message:
    """A single chat message (role + content + optional tool metadata)."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call_id: str | None = None
    name: str | None = None
    tool_calls: list[ToolCall] | None = None


@dataclass(frozen=True, slots=True)
class AssistantMessage:
    """The reply from the LLM, plus lightweight usage metadata."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage_reported: bool = True
    attempts: int = 1
    unknown_attempts: int = 0


@dataclass(frozen=True, slots=True)
class StreamUsage:
    model: str
    input_tokens: int
    output_tokens: int


# ── LLM errors ─────────────────────────────────────────────────────────


class LLMError(Exception):
    """Base error for all LLM-related failures."""


class LLMRateLimitError(LLMError):
    """Groq rate limit (429) hit."""


class LLMCapacityError(LLMRateLimitError):
    """Local capacity is unavailable; reason contains no recruiter/provider text."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class LLMAuthError(LLMError):
    """Invalid or missing API key (401)."""


class LLMUnavailableError(LLMError):
    """Upstream service unavailable (503/500/connection)."""


# ── Domain functions ───────────────────────────────────────────────────


def normalize_llm_text(text: str) -> str:
    """Normalize non-standard Unicode whitespace and tokenizer artifacts."""
    if not text:
        return text
    # Replace narrow no-break space (\u202f), non-breaking space (\u00a0),
    # and zero-width space (\u200b) with standard ASCII space.
    cleaned = (
        text.replace("\u202f", " ")
        .replace("\u00a0", " ")
        .replace("\u200b", "")
        .replace("\u2011", "-")
    )
    # Normalize glued list numerals (e.g. "are1. " -> "are\n\n1. ")
    return re.sub(r"([a-zA-Z,:]|[\u2019\']s)(\d+\.\s+)", r"\1\n\n\2", cleaned)


# ── Protocol (the seam) ───────────────────────────────────────────────


class LLMClient(Protocol):
    """Protocol that both GroqLLM and FakeLLM satisfy."""

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> AssistantMessage: ...

    async def stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str | ToolCall | StreamUsage]: ...


# ── Real adapter ───────────────────────────────────────────────────────


class GroqLLM:
    """Production adapter wrapping the Groq AsyncGroq client.

    Accepts dependencies via __init__ — never reads globals or env directly.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        ledger: InferenceLedger | None = None,
        client: AsyncGroq | None = None,
    ) -> None:
        self._model = settings.LLM_MODEL_MAIN
        self._settings = settings
        self.ledger = ledger or InferenceLedger(
            shared=settings.INFERENCE_SHARED_LIMITS,
            models=settings.INFERENCE_MODEL_LIMITS,
            max_active=settings.INFERENCE_MAX_ACTIVE,
            max_waiters=settings.INFERENCE_MAX_WAITERS,
        )
        if client is not None and client.max_retries != 0:
            raise ValueError("Injected SDK client must disable implicit retries")
        self._client = client
        self.timeout_seconds = 30.0
        self._closed = False

    def _sdk(self) -> AsyncGroq:
        if self._closed:
            raise LLMUnavailableError("Inference client is closed")
        if self._client is None:
            if not self._settings.GROQ_API_KEY:
                raise LLMAuthError("Inference credentials unavailable")
            self._client = AsyncGroq(
                api_key=self._settings.GROQ_API_KEY,
                base_url="https://api.groq.com",
                max_retries=0,
                timeout=self.timeout_seconds,
            )
        return self._client

    async def aclose(self) -> None:
        self._closed = True
        if self._client is not None:
            await self._client.close()

    def _cost(self, kwargs: dict[str, Any]) -> AttemptCost:
        return AttemptCost(
            model=kwargs["model"],
            input_tokens=reserve_input_tokens(kwargs),
            output_tokens=kwargs["max_completion_tokens"],
        )

    @staticmethod
    def _retry_delay(exc: Exception) -> float | None:
        from groq import RateLimitError

        if not isinstance(exc, RateLimitError):
            return None
        try:
            delay = float(exc.response.headers.get("retry-after", "1"))
        except ValueError:
            return None
        return delay if math.isfinite(delay) and 0 <= delay <= 5 else None

    def _format_messages_for_groq(
        self, messages: list[Message]
    ) -> list[dict[str, Any]]:
        """Convert domain Message value objects to Groq API dicts."""
        formatted: list[dict[str, Any]] = []
        for m in messages:
            entry: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.role == "assistant" and m.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        },
                    }
                    for tc in m.tool_calls
                ]
            elif m.role == "tool":
                if m.tool_call_id:
                    entry["tool_call_id"] = m.tool_call_id
                if m.name:
                    entry["name"] = m.name
            formatted.append(entry)
        return formatted

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> AssistantMessage:
        """Send messages to Groq and return the assistant reply."""
        target_model = model or self._model
        kwargs: dict[str, Any] = {
            "model": target_model,
            "messages": self._format_messages_for_groq(messages),
            "temperature": 0.2 if response_format else 0.4,
            "max_completion_tokens": 1024,
        }
        if response_format:
            kwargs["response_format"] = response_format
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        deadline = time.monotonic() + self.timeout_seconds
        try:
            for attempt in range(2):
                try:
                    async with self.ledger.attempt(
                        self._cost(kwargs),
                        wait_seconds=max(0, min(5, deadline - time.monotonic())),
                    ) as p:
                        sdk = self._sdk()
                        if time.monotonic() >= deadline:
                            raise TimeoutError
                        p.dispatch()
                        response = await asyncio.wait_for(
                            sdk.chat.completions.create(**kwargs),
                            timeout=max(0, deadline - time.monotonic()),
                        )
                        if response.model != target_model:
                            self.ledger.stop("model_mismatch")
                            raise LLMUnavailableError("Inference model mismatch")
                        if response.usage is not None:
                            p.settle(
                                ProviderUsage(
                                    input_tokens=response.usage.prompt_tokens,
                                    output_tokens=response.usage.completion_tokens,
                                    total_tokens=response.usage.total_tokens,
                                )
                            )
                    break
                except Exception as exc:
                    delay = self._retry_delay(exc)
                    if attempt or delay is None or time.monotonic() + delay >= deadline:
                        raise
                    await asyncio.sleep(delay)
        except QuotaDenied as exc:
            raise LLMCapacityError(exc.reason) from None
        except Exception as exc:
            self._map_error(exc)

        choice = response.choices[0]
        usage = response.usage

        tool_calls: list[ToolCall] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=tc.function.arguments,
                    )
                )

        return AssistantMessage(
            content=(
                choice.message.content or ""
                if response_format
                else normalize_llm_text(choice.message.content or "")
            ),
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            tool_calls=tool_calls,
            usage_reported=usage is not None and attempt == 0,
            attempts=attempt + 1,
            unknown_attempts=attempt + (usage is None),
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str | ToolCall | StreamUsage]:
        """Stream assistant response tokens and tool calls from Groq."""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._format_messages_for_groq(messages),
            "temperature": 0.4,
            "max_completion_tokens": 1024,
            "stream": True,
            # groq 1.7.0 exposes this API option through extra_body.
            "extra_body": {"stream_options": {"include_usage": True}},
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        tool_call_buffers: dict[int, dict[str, str]] = {}
        final_usage: ProviderUsage | None = None
        deadline = time.monotonic() + self.timeout_seconds
        try:
            async with self.ledger.attempt(
                self._cost(kwargs),
                wait_seconds=max(0, min(5, deadline - time.monotonic())),
            ) as p:
                sdk = self._sdk()
                if time.monotonic() >= deadline:
                    raise TimeoutError
                p.dispatch()
                response_stream = await asyncio.wait_for(
                    sdk.chat.completions.create(**kwargs),
                    timeout=max(0, deadline - time.monotonic()),
                )
                try:
                    iterator = aiter(response_stream)
                    while True:
                        try:
                            chunk = await asyncio.wait_for(
                                anext(iterator),
                                timeout=max(0, deadline - time.monotonic()),
                            )
                        except StopAsyncIteration:
                            break
                        if chunk.model != self._model:
                            self.ledger.stop("model_mismatch")
                            raise LLMUnavailableError("Inference model mismatch")
                        usage = chunk.usage or (
                            chunk.x_groq.usage if chunk.x_groq else None
                        )
                        if usage is not None:
                            reported_usage = ProviderUsage(
                                input_tokens=usage.prompt_tokens,
                                output_tokens=usage.completion_tokens,
                                total_tokens=usage.total_tokens,
                            )
                            if (
                                final_usage is not None
                                and final_usage != reported_usage
                            ):
                                self.ledger.stop("provider_contract")
                                raise LLMUnavailableError(
                                    "Inconsistent inference usage"
                                )
                            final_usage = reported_usage
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        if delta.content:
                            yield normalize_llm_text(delta.content)
                        if delta.tool_calls:
                            for tc in delta.tool_calls:
                                idx = tc.index if tc.index is not None else 0
                                buffer = tool_call_buffers.setdefault(
                                    idx, {"id": "", "name": "", "arguments": ""}
                                )
                                if tc.id:
                                    buffer["id"] = tc.id
                                if tc.function:
                                    if tc.function.name:
                                        buffer["name"] = tc.function.name
                                    buffer["arguments"] += tc.function.arguments or ""
                    if final_usage is not None:
                        p.settle(final_usage)
                        yield StreamUsage(
                            model=self._model,
                            input_tokens=final_usage.input_tokens,
                            output_tokens=final_usage.output_tokens,
                        )
                    for buffer in tool_call_buffers.values():
                        if buffer["name"]:
                            yield ToolCall(
                                id=buffer["id"] or "call_unknown",
                                name=buffer["name"],
                                arguments=buffer["arguments"],
                            )
                finally:
                    await response_stream.close()
        except QuotaDenied as exc:
            raise LLMCapacityError(exc.reason) from None
        except Exception as exc:
            self._map_error(exc)

    def _map_error(self, exc: Exception) -> None:
        """Translate Groq SDK exceptions into our domain errors."""
        from groq import AuthenticationError, RateLimitError

        if isinstance(exc, ValidationError):
            self.ledger.stop("provider_contract")
            raise LLMUnavailableError("Invalid inference usage") from None
        if isinstance(exc, LLMError):
            raise exc
        if isinstance(exc, RateLimitError):
            raise LLMRateLimitError("Provider capacity unavailable") from None
        if isinstance(exc, AuthenticationError):
            raise LLMAuthError("Inference credentials unavailable") from None
        raise LLMUnavailableError("Inference service unavailable") from None


# ── Fake adapter (for tests) ──────────────────────────────────────────


class FakeLLM:
    """In-memory fake satisfying LLMClient for deterministic tests.

    Instantiate with a canned reply; optionally inspect captured messages.
    """

    def __init__(
        self,
        reply: str = "Fake reply",
        model: str = "fake-model",
        stream_chunks: list[str] | None = None,
        tool_calls: list[ToolCall] | None = None,
        error_to_raise: Exception | None = None,
        canned_replies: list[str] | None = None,
    ) -> None:
        self.reply = reply
        self.model = model
        self.stream_chunks = stream_chunks
        self.tool_calls = tool_calls or []
        self.error_to_raise = error_to_raise
        self.canned_replies = list(canned_replies) if canned_replies else None
        self.last_messages: list[Message] = []
        self.last_tools: list[dict[str, Any]] | None = None
        self.last_model: str | None = None
        self.last_response_format: dict[str, Any] | None = None
        self.call_count: int = 0

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> AssistantMessage:
        self.last_messages = list(messages)
        self.last_tools = tools
        self.last_model = model
        self.last_response_format = response_format
        if self.error_to_raise is not None:
            raise self.error_to_raise

        # If tools provided and canned tool_calls configured, simulate tool call
        if tools and self.tool_calls:
            return AssistantMessage(
                content="",
                model=self.model,
                prompt_tokens=15,
                completion_tokens=10,
                total_tokens=25,
                tool_calls=list(self.tool_calls),
            )

        reply_content = self.reply
        if self.canned_replies:
            idx = min(self.call_count, len(self.canned_replies) - 1)
            reply_content = self.canned_replies[idx]
        self.call_count += 1

        return AssistantMessage(
            content=reply_content,
            model=model or self.model,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str | ToolCall]:
        self.last_messages = list(messages)
        self.last_tools = tools
        if self.error_to_raise is not None:
            raise self.error_to_raise

        # If tools provided and canned tool_calls configured, yield tool call
        if tools and self.tool_calls:
            for tc in self.tool_calls:
                yield tc
            return

        if self.stream_chunks is not None:
            for chunk in self.stream_chunks:
                yield chunk
        else:
            words = self.reply.split(" ")
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")


def get_llm_client(request: Request) -> LLMClient:
    """One lazy provider client and quota ledger owned by the application lifespan."""
    return request.app.state.llm
