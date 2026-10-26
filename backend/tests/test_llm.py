"""Tests for app.llm — verifies the LLM adapter seam using FakeLLM."""

import pytest

from app.llm import (
    AssistantMessage,
    FakeLLM,
    LLMAuthError,
    LLMError,
    LLMRateLimitError,
    LLMUnavailableError,
    Message,
)

# asyncio_mode = "auto" in pyproject.toml — no @pytest.mark.asyncio needed


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


# ── FakeLLM tests ─────────────────────────────────────────────────────


class TestFakeLLM:
    async def test_returns_canned_reply(self) -> None:
        fake = FakeLLM(reply="I know about Aamir")
        result = await fake.complete([Message(role="user", content="Who is Aamir?")])

        assert isinstance(result, AssistantMessage)
        assert result.content == "I know about Aamir"
        assert result.model == "fake-model"

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

    async def test_returns_usage_metadata(self) -> None:
        fake = FakeLLM()
        result = await fake.complete([Message(role="user", content="hi")])

        assert result.prompt_tokens == 10
        assert result.completion_tokens == 5
        assert result.total_tokens == 15

    async def test_custom_model_name(self) -> None:
        fake = FakeLLM(model="custom-model-v2")
        result = await fake.complete([Message(role="user", content="hi")])
        assert result.model == "custom-model-v2"


# ── Error hierarchy tests ─────────────────────────────────────────────


class TestErrorHierarchy:
    def test_rate_limit_is_llm_error(self) -> None:
        assert issubclass(LLMRateLimitError, LLMError)

    def test_auth_is_llm_error(self) -> None:
        assert issubclass(LLMAuthError, LLMError)

    def test_unavailable_is_llm_error(self) -> None:
        assert issubclass(LLMUnavailableError, LLMError)
