"""Tests for prompt loading and system prompt construction."""

from __future__ import annotations

from app.prompt_loader import (
    SYSTEM_PROMPT,
    build_system_prompt,
)
from app.retrieval.models import FactChunk, RetrievedChunk


def test_system_prompt_is_populated() -> None:
    assert SYSTEM_PROMPT
    assert len(SYSTEM_PROMPT) > 500


def test_resume_placeholder_is_replaced() -> None:
    assert "{resume_context}" not in SYSTEM_PROMPT


def test_system_prompt_contains_identity_and_voice() -> None:
    assert "Aamir Mohammed Khan" in SYSTEM_PROMPT
    assert "third person" in SYSTEM_PROMPT.lower()
    assert "AlgoUniversity" in SYSTEM_PROMPT


def test_phone_number_is_excluded() -> None:
    # Per hard rules, no private phone numbers in prompt/context
    assert "8904816279" not in SYSTEM_PROMPT


def test_build_system_prompt_with_chunks() -> None:
    chunk = FactChunk(
        id="test-chunk",
        type="project",
        title="Sample Project",
        content="Built with FastAPI.",
        source_section="J1",
        source_url="https://example.com",
    )
    retrieved = RetrievedChunk(chunk=chunk, score=0.9, rank=1)
    prompt = build_system_prompt([retrieved])

    assert "Sample Project" in prompt
    assert "Built with FastAPI." in prompt
    assert "https://example.com" in prompt
    assert "{resume_context}" not in prompt


def test_build_system_prompt_with_empty_chunks() -> None:
    prompt = build_system_prompt([])
    assert "No specific portfolio facts were retrieved" in prompt
    assert "{resume_context}" not in prompt
