"""Prompt loading — reads system prompt and resume context from files.

Loads once at import time and caches. The system prompt contains a
{resume_context} placeholder that gets filled with the resume markdown.
"""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _read(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


# Loaded once, cached as module-level constants
_SYSTEM_TEMPLATE = _read("system.txt")
_RESUME_CONTEXT = _read("resume_context.md")

SYSTEM_PROMPT: str = _SYSTEM_TEMPLATE.replace("{resume_context}", _RESUME_CONTEXT)
