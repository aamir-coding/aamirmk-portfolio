"""Prompt loading — reads system prompt template and formats dynamic context."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.retrieval.models import RetrievedChunk

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _read(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


# Loaded once, cached as module-level constants
_SYSTEM_TEMPLATE = _read("system.txt")
_RESUME_CONTEXT = _read("resume_context.md")

# Static system prompt baseline for backwards compatibility and fallback
SYSTEM_PROMPT: str = _SYSTEM_TEMPLATE.replace("{resume_context}", _RESUME_CONTEXT)


def format_retrieved_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved fact chunks into structured markdown source blocks."""
    if not chunks:
        return (
            "No specific portfolio facts were retrieved for this inquiry. "
            "If the question cannot be answered with verified certainty, "
            "state honestly that you do not have verified information in "
            "Aamir's approved portfolio, and offer to forward the inquiry to "
            "him directly at aamirmkh25@gmail.com."
        )

    sections: list[str] = []
    for item in chunks:
        c = item.chunk
        source_label = f"Source: {c.title}"
        if c.source_section:
            source_label += f" ({c.source_section})"
        if c.source_url:
            source_label += f" | {c.source_url}"

        sections.append(f"### [{source_label}]\n{c.content.strip()}")

    return "\n\n".join(sections)


def build_system_prompt(chunks: list[RetrievedChunk] | None = None) -> str:
    """Construct system prompt with dynamically retrieved context or static baseline."""
    if chunks is None:
        return SYSTEM_PROMPT

    context_str = format_retrieved_context(chunks)
    return _SYSTEM_TEMPLATE.replace("{resume_context}", context_str)
