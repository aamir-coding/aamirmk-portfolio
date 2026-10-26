"""Tests for API schema models and validation."""

import pytest
from pydantic import ValidationError

from app.models import ChatRequest, ChatResponse, TokenUsage


class TestChatRequest:
    def test_valid_chat_request(self) -> None:
        req = ChatRequest(
            message="What is Aamir's experience?", conversation_id="conv-123"
        )
        assert req.message == "What is Aamir's experience?"
        assert req.conversation_id == "conv-123"

    def test_whitespace_is_trimmed(self) -> None:
        req = ChatRequest(message="  Tell me about his projects   ")
        assert req.message == "Tell me about his projects"

    def test_empty_message_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_whitespace_only_message_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ChatRequest(message="    \n   ")

    def test_message_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ChatRequest(message="a" * 2001)

    def test_conversation_id_optional(self) -> None:
        req = ChatRequest(message="Hello")
        assert req.conversation_id is None


class TestChatResponse:
    def test_valid_chat_response(self) -> None:
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        res = ChatResponse(
            reply="Aamir is a full-stack engineer.",
            conversation_id="conv-1",
            model="openai/gpt-oss-120b",
            usage=usage,
        )
        assert res.reply == "Aamir is a full-stack engineer."
        assert res.conversation_id == "conv-1"
        assert res.model == "openai/gpt-oss-120b"
        assert res.usage.total_tokens == 150

    def test_models_are_immutable(self) -> None:
        usage = TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20)
        res = ChatResponse(
            reply="Hi",
            conversation_id="c1",
            model="m1",
            usage=usage,
        )
        with pytest.raises(ValidationError):
            res.reply = "new reply"  # type: ignore[misc]
        with pytest.raises(ValidationError):
            usage.total_tokens = 30  # type: ignore[misc]
