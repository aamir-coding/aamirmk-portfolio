"""Tests for app.llm — verifies the LLM adapter seam using FakeLLM."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.llm import (
    AssistantMessage,
    FakeLLM,
    GroqLLM,
    LLMAuthError,
    LLMError,
    LLMRateLimitError,
    LLMUnavailableError,
    Message,
    ToolCall,
    normalize_llm_text,
)


@pytest.mark.asyncio
async def test_json_mode_preserves_raw_structured_response() -> None:
    payload = '{"text": "Python3. Strong API skills"}'
    create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[
                SimpleNamespace(message=SimpleNamespace(content=payload, tool_calls=[]))
            ],
            usage=None,
            model="fake",
        )
    )
    llm = GroqLLM.__new__(GroqLLM)
    llm._model = "fake"
    llm._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    reply = await llm.complete([], response_format={"type": "json_object"})
    assert reply.content == payload


# ── Value object tests ────────────────────────────────────────────────


class TestMessage:
    def test_message_creation(self) -> None:
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_is_frozen(self) -> None:
        msg = Message(role="system", content="prompt")
        with pytest.raises(AttributeError):
            msg.role = "user"  # type: ignore[misc]

    def test_message_with_tool_metadata(self) -> None:
        tc = ToolCall(id="call_1", name="show_project_card", arguments='{"id":"test"}')
        msg = Message(role="assistant", content="", tool_calls=[tc])
        assert msg.tool_calls == [tc]

        tool_resp = Message(
            role="tool", content="ok", tool_call_id="call_1", name="show_project_card"
        )
        assert tool_resp.tool_call_id == "call_1"


class TestAssistantMessage:
    def test_assistant_message_fields(self) -> None:
        reply = AssistantMessage(
            content="Hi there",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )
        assert reply.content == "Hi there"
        assert reply.model == "test-model"
        assert reply.total_tokens == 15
        assert reply.tool_calls == []


# ── FakeLLM tests ─────────────────────────────────────────────────────


class TestFakeLLM:
    @pytest.mark.asyncio
    async def test_returns_canned_reply(self) -> None:
        fake = FakeLLM(reply="I know about Aamir")
        result = await fake.complete([Message(role="user", content="Who is Aamir?")])

        assert isinstance(result, AssistantMessage)
        assert result.content == "I know about Aamir"
        assert result.model == "fake-model"

    @pytest.mark.asyncio
    async def test_captures_messages(self) -> None:
        fake = FakeLLM()
        messages = [
            Message(role="system", content="You are helpful"),
            Message(role="user", content="Tell me about Aamir"),
        ]
        await fake.complete(messages)

        assert len(fake.last_messages) == 2
        assert fake.last_messages[0].role == "system"
        assert fake.last_messages[1].content == "Tell me about Aamir"

    @pytest.mark.asyncio
    async def test_returns_usage_metadata(self) -> None:
        fake = FakeLLM()
        result = await fake.complete([Message(role="user", content="hi")])

        assert result.prompt_tokens == 10
        assert result.completion_tokens == 5
        assert result.total_tokens == 15

    @pytest.mark.asyncio
    async def test_custom_model_name(self) -> None:
        fake = FakeLLM(model="custom-model-v2")
        result = await fake.complete([Message(role="user", content="hi")])
        assert result.model == "custom-model-v2"

    @pytest.mark.asyncio
    async def test_stream_default_chunks(self) -> None:
        fake = FakeLLM(reply="Aamir is an engineer")
        messages = [Message(role="user", content="Who is Aamir?")]
        chunks: list[str] = []
        async for chunk in fake.stream(messages):
            if isinstance(chunk, str):
                chunks.append(chunk)

        assert "".join(chunks) == "Aamir is an engineer"
        assert len(fake.last_messages) == 1
        assert fake.last_messages[0].content == "Who is Aamir?"

    @pytest.mark.asyncio
    async def test_stream_custom_chunks(self) -> None:
        fake = FakeLLM(stream_chunks=["Hel", "lo ", "world"])
        chunks: list[str] = [
            chunk
            async for chunk in fake.stream([Message(role="user", content="hi")])
            if isinstance(chunk, str)
        ]
        assert chunks == ["Hel", "lo ", "world"]

    @pytest.mark.asyncio
    async def test_stream_raises_configured_error(self) -> None:
        fake = FakeLLM(error_to_raise=LLMRateLimitError("Rate limit exceeded"))
        with pytest.raises(LLMRateLimitError, match="Rate limit"):
            async for _ in fake.stream([Message(role="user", content="hi")]):
                pass

    @pytest.mark.asyncio
    async def test_complete_raises_configured_error(self) -> None:
        fake = FakeLLM(error_to_raise=LLMAuthError("Invalid API key"))
        with pytest.raises(LLMAuthError, match="Invalid API key"):
            await fake.complete([Message(role="user", content="hi")])

    @pytest.mark.asyncio
    async def test_complete_with_simulated_tool_call(self) -> None:
        tc = ToolCall(
            id="tc-1",
            name="show_project_card",
            arguments='{"project_id": "entropy-oj"}',
        )
        fake = FakeLLM(reply="Here is Entropy", tool_calls=[tc])

        tools = [{"type": "function", "function": {"name": "show_project_card"}}]
        result = await fake.complete(
            [Message(role="user", content="Show entropy")], tools=tools
        )

        assert result.tool_calls == [tc]
        assert fake.last_tools == tools

    @pytest.mark.asyncio
    async def test_stream_with_simulated_tool_call(self) -> None:
        tc = ToolCall(
            id="tc-1",
            name="show_project_card",
            arguments='{"project_id": "entropy-oj"}',
        )
        fake = FakeLLM(reply="Here is Entropy", tool_calls=[tc])

        tools = [{"type": "function", "function": {"name": "show_project_card"}}]
        items = [
            item
            async for item in fake.stream(
                [Message(role="user", content="Show entropy")], tools=tools
            )
        ]

        assert items == [tc]
        assert fake.last_tools == tools


# ── Error hierarchy tests ─────────────────────────────────────────────


class TestErrorHierarchy:
    def test_rate_limit_is_llm_error(self) -> None:
        assert issubclass(LLMRateLimitError, LLMError)

    def test_auth_is_llm_error(self) -> None:
        assert issubclass(LLMAuthError, LLMError)

    def test_unavailable_is_llm_error(self) -> None:
        assert issubclass(LLMUnavailableError, LLMError)


# ── Text normalization tests ──────────────────────────────────────────


class TestNormalizeLLMText:
    def test_replaces_narrow_and_non_breaking_spaces(self) -> None:
        raw = "Aamir\u202fs\u00a0contact:\u200bdetails"
        normalized = normalize_llm_text(raw)
        assert normalized == "Aamir s contact:details"

    def test_handles_empty_or_normal_string(self) -> None:
        assert normalize_llm_text("") == ""
        assert normalize_llm_text("Clean text") == "Clean text"

    def test_separates_glued_numbered_list_items(self) -> None:
        raw = "His strengths are1. AI-Assisted Implementation"
        assert (
            normalize_llm_text(raw)
            == "His strengths are\n\n1. AI-Assisted Implementation"
        )

    def test_replaces_non_breaking_hyphen(self) -> None:
        raw = "Entropy\u2011OJ"
        assert normalize_llm_text(raw) == "Entropy-OJ"
