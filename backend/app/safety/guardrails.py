"""Prompt injection and adversarial input defenses for the portfolio assistant."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from html import escape

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

    Reject known lexical attacks at zero model cost. This is not a semantic
    injection detector or a guarantee of zero false positives.
    """
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            reason = f"Matched injection pattern: {pattern.pattern}"
            logger.warning("Known injection pattern rejected")
            return InjectionCheckResult(is_safe=False, flagged_reason=reason)

    return InjectionCheckResult(is_safe=True)


def sanitize_user_input(text: str) -> str:
    """Escape structural characters; semantic instructions remain untrusted data."""
    return escape(text.strip(), quote=False)


def valid_unicode(text: str) -> str:
    try:
        text.encode("utf-8")
    except UnicodeError:
        raise ValueError("Text must contain valid Unicode") from None
    return text


def data_block(tag: str, text: str) -> str:
    if not re.fullmatch(r"[a-z_]+", tag):
        raise ValueError("Invalid internal data tag")
    return f"<{tag}>\n{sanitize_user_input(text)}\n</{tag}>"


def format_safe_user_message(user_input: str) -> str:
    """Wrap user query in strict structural XML delimiter boundary fencing."""
    return data_block("user_inquiry", user_input)
