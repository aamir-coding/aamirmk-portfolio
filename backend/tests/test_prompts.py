"""Tests for prompt loading and system prompt construction."""

from app.prompt_loader import SYSTEM_PROMPT


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
