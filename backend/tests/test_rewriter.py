"""Tests for app.retrieval.rewriter — follow-up query rewriting."""

import pytest

from app.llm import FakeLLM
from app.models import ChatHistoryMessage
from app.retrieval.rewriter import (
    is_likely_follow_up,
    rewrite_follow_up_query,
)


class TestIsLikelyFollowUp:
    def test_no_history_returns_false(self) -> None:
        assert not is_likely_follow_up("tell me more", [])

    def test_short_query_with_history_is_follow_up(self) -> None:
        history = [
            ChatHistoryMessage(role="user", content="What is Entropy?"),
            ChatHistoryMessage(role="assistant", content="Entropy is an online judge."),
        ]
        assert is_likely_follow_up("tell me more", history)
        assert is_likely_follow_up("expand on that", history)
        assert is_likely_follow_up("why?", history)

    def test_query_with_pronouns_is_follow_up(self) -> None:
        history = [
            ChatHistoryMessage(role="user", content="Tell me about HealthTracker"),
            ChatHistoryMessage(
                role="assistant", content="It is a full stack health PWA."
            ),
        ]
        assert is_likely_follow_up("What tech stack did he use for it?", history)
        assert is_likely_follow_up("What was the hardest bug in that project?", history)

    def test_self_contained_query_is_not_follow_up(self) -> None:
        history = [
            ChatHistoryMessage(role="user", content="Hi"),
            ChatHistoryMessage(role="assistant", content="Hello! How can I help?"),
        ]
        assert not is_likely_follow_up(
            "What is Aamir's cumulative CGPA across his university semesters?",
            history,
        )


class TestRewriteFollowUpQuery:
    @pytest.mark.asyncio
    async def test_rewrites_when_follow_up(self) -> None:
        history = [
            ChatHistoryMessage(role="user", content="Tell me about Entropy-OJ"),
            ChatHistoryMessage(
                role="assistant",
                content="Entropy-OJ is a full-stack online judge platform.",
            ),
        ]
        fake_llm = FakeLLM(reply="Entropy-OJ architecture and debugging features")
        rewritten = await rewrite_follow_up_query(
            "tell me more",
            history,
            llm=fake_llm,
        )
        assert rewritten == "Entropy-OJ architecture and debugging features"

    @pytest.mark.asyncio
    async def test_bypasses_llm_when_not_follow_up(self) -> None:
        fake_llm = FakeLLM(reply="Should not be called")
        rewritten = await rewrite_follow_up_query(
            "What is Aamir's CGPA in university?",
            [],
            llm=fake_llm,
        )
        assert rewritten == "What is Aamir's CGPA in university?"
        assert fake_llm.call_count == 0

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_error(self) -> None:
        history = [
            ChatHistoryMessage(role="user", content="Tell me about Keynone"),
            ChatHistoryMessage(role="assistant", content="Keynone is a keyboard."),
        ]
        # Simulate LLM raising an unexpected error
        fake_llm = FakeLLM(error_to_raise=RuntimeError("Groq service timeout"))
        rewritten = await rewrite_follow_up_query(
            "tell me more",
            history,
            llm=fake_llm,
        )
        # Should gracefully return original query
        assert rewritten == "tell me more"
