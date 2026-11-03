"""Thin async LLM adapter — the seam between the app and Groq.

Interface: `complete(messages, tools=None) -> AssistantMessage`
           and `stream(messages, tools=None) -> AsyncIterator[str | ToolCall]`.
Implementation details hidden behind the seam: API key, model selection,
client lifecycle, timeouts, error mapping. Tests inject a FakeLLM that
satisfies the same protocol — no real Groq calls in CI.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol

from fastapi import Depends
from groq import AsyncGroq

from app.settings import Settings, get_settings

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


# ── LLM errors ─────────────────────────────────────────────────────────


class LLMError(Exception):
    """Base error for all LLM-related failures."""


class LLMRateLimitError(LLMError):
    """Groq rate limit (429) hit."""


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
    return text.replace("\u202f", " ").replace("\u00a0", " ").replace("\u200b", "")


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
    ) -> AsyncIterator[str | ToolCall]: ...


# ── Real adapter ───────────────────────────────────────────────────────


class GroqLLM:
    """Production adapter wrapping the Groq AsyncGroq client.

    Accepts dependencies via __init__ — never reads globals or env directly.
    """

    def __init__(self, settings: Settings) -> None:
        self._model = settings.LLM_MODEL_MAIN
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)

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

        try:
            response = await self._client.chat.completions.create(**kwargs)
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
            content=normalize_llm_text(choice.message.content or ""),
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            tool_calls=tool_calls,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str | ToolCall]:
        """Stream assistant response tokens and tool calls from Groq."""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": self._format_messages_for_groq(messages),
            "temperature": 0.4,
            "max_completion_tokens": 1024,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response_stream = await self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            self._map_error(exc)

        tool_call_buffers: dict[int, dict[str, str]] = {}

        try:
            async for chunk in response_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                if delta.content:
                    yield normalize_llm_text(delta.content)

                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index if tc_delta.index is not None else 0
                        if idx not in tool_call_buffers:
                            tool_call_buffers[idx] = {
                                "id": tc_delta.id or "",
                                "name": (
                                    tc_delta.function.name
                                    if tc_delta.function and tc_delta.function.name
                                    else ""
                                ),
                                "arguments": "",
                            }
                        else:
                            if tc_delta.id:
                                tool_call_buffers[idx]["id"] = tc_delta.id
                            if tc_delta.function and tc_delta.function.name:
                                tool_call_buffers[idx]["name"] = tc_delta.function.name

                        if tc_delta.function and tc_delta.function.arguments:
                            tool_call_buffers[idx]["arguments"] += (
                                tc_delta.function.arguments
                            )

            for tc_data in tool_call_buffers.values():
                if tc_data["name"]:
                    yield ToolCall(
                        id=tc_data["id"] or "call_unknown",
                        name=tc_data["name"],
                        arguments=tc_data["arguments"],
                    )
        except Exception as exc:
            self._map_error(exc)

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


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Dependency provider returning production LLM client."""
    return GroqLLM(settings)
