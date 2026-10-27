"""Prompt injection and adversarial input defenses for the portfolio assistant."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Standard canned polite refusal message (consumed at zero LLM token cost)
SAFE_REFUSAL_MESSAGE = (
    "I am Aamir's AI assistant. I can only answer questions related to "
    "Aamir's verified experience, projects, skills, and background."
)

# Compiled regex patterns targeting imperative adversarial attacks
_INJECTION_PATTERNS = [
    # Instruction override / memory reset attempts
    re.compile(
        r"(?:ignore|disregard|forget|bypass|override)\s+(?:all\s+)?(?:previous|prior|above|system)\s+"
        r"(?:instructions|prompts|rules|directives|constraints)",
        re.IGNORECASE,
    ),
    # System prompt extraction attempts
    re.compile(
        r"(?:reveal|print|show|dump|repeat|output|display)\s+(?:the|your)\s+"
        r"(?:full\s+|exact\s+|entire\s+)?(?:system\s+prompt|initial\s+instructions|"
        r"hidden\s+prompt|developer\s+mode\s+instructions)",
        re.IGNORECASE,
    ),
    # Persona hijacking / Jailbreak identities (DAN, developer mode, unrestricted)
    re.compile(
        r"(?:you\s+are\s+now|pretend\s+to\s+be|act\s+as)\s+(?:an?\s+)?"
        r"(?:dan|jailbroken|unrestricted|evil\s+bot|ai\s+without\s+rules)",
        re.IGNORECASE,
    ),
    # Special tokenizer / chat template token breakout attempts
    re.compile(
        r"(?:<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>|\[SYSTEM\]|\[INST\])",
        re.IGNORECASE,
    ),
    # Delimiter breakout attempts targeting XML framing
    re.compile(
        r"<\s*/\s*(?:user_inquiry|context|system_instructions)\s*>",
        re.IGNORECASE,
    ),
]


@dataclass(frozen=True)
class InjectionCheckResult:
    """Result of prompt injection evaluation."""

    is_safe: bool
    flagged_reason: str | None = None


def check_prompt_injection(text: str) -> InjectionCheckResult:
    """Evaluate whether input text contains adversarial prompt injection directives.

    Designed to detect imperative commands trying to subvert the LLM instructions
    while deliberately allowing recruiters to ask questions ABOUT prompt engineering,
    instructions, or safety systems.
    """
    if not text or not isinstance(text, str):
        return InjectionCheckResult(is_safe=True)

    normalized = text.strip()

    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(normalized)
        if match:
            reason = f"Matched injection pattern: {match.group(0)}"
            logger.warning("Adversarial prompt injection attempt detected: %s", reason)
            return InjectionCheckResult(is_safe=False, flagged_reason=reason)

    return InjectionCheckResult(is_safe=True)


def sanitize_user_input(text: str) -> str:
    """Sanitize user input to neutralize delimiter breakouts."""
    if not text:
        return ""
    # Neutralize XML-like tag injections
    sanitized = text.replace("<user_inquiry>", "[user_inquiry]").replace(
        "</user_inquiry>", "[/user_inquiry]"
    )
    return sanitized.strip()


def format_safe_user_message(text: str) -> str:
    """Format sanitized user text inside structured XML delimiter tags."""
    clean_text = sanitize_user_input(text)
    return f"<user_inquiry>\n{clean_text}\n</user_inquiry>"
