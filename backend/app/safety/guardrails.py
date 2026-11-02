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
    # Questioning startup directives
    re.compile(
        r"(?:what\s+were\s+the\s+initial\s+instructions|tell\s+me\s+your\s+instructions|"
        r"output\s+all\s+rules)",
        re.IGNORECASE,
    ),
    # Persona hijacking / Jailbreak identities (DAN, developer mode, unrestricted)
    re.compile(
        r"(?:you\s+are\s+now|pretend\s+to\s+be|act\s+as|speak\s+as)\s+(?:an?\s+)?"
        r"(?:dan|jailbroken|unrestricted|unaligned|evil\s+bot|ai\s+without\s+(?:rules|boundaries))",
        re.IGNORECASE,
    ),
    # Special tokenizer / chat template token breakout attempts
    re.compile(
        r"(?:<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>|\[SYSTEM\]|\[INST\])",
        re.IGNORECASE,
    ),
    # Delimiter breakout attempts targeting XML framing
    re.compile(
        r"<\s*/?\s*(?:user_inquiry|context|system_instructions)\s*>",
        re.IGNORECASE,
    ),
    # System administrative command spoofing
    re.compile(
        r"(?:system\s+reboot|master\s+credentials|root\s+access|admin\s+mode\s+activated)",
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

    Uses deterministic regex boundary checks to reject attacks at 0 LLM token cost
    with zero false-positives on legitimate queries about architecture or engineering.
    """
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            reason = f"Matched injection pattern: {pattern.pattern}"
            logger.warning(
                "Prompt injection rejected: %s (matched '%s')", text, match.group(0)
            )
            return InjectionCheckResult(is_safe=False, flagged_reason=reason)

    return InjectionCheckResult(is_safe=True)


def sanitize_user_input(text: str) -> str:
    """Strip or neutralize potentially malicious delimiter tags from user input."""
    # Escape xml tags that might conflict with system prompt delimiter isolation
    sanitized = re.sub(r"<\s*(/?)user_inquiry\s*>", r"[\1user_inquiry]", text)
    sanitized = re.sub(r"<\s*(/?)context\s*>", r"[\1context]", sanitized)
    return sanitized.strip()


def format_safe_user_message(user_input: str) -> str:
    """Wrap user query in strict structural XML delimiter boundary fencing."""
    cleaned = sanitize_user_input(user_input)
    return f"<user_inquiry>\n{cleaned}\n</user_inquiry>"
