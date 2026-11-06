"""Follow-up query rewriter — resolves conversational coreferences.

Rewrites pronouns and relative queries into standalone search queries.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from app.llm import LLMClient, Message

if TYPE_CHECKING:
    from app.models import ChatHistoryMessage

logger = logging.getLogger(__name__)

# Heuristic pattern to detect potential follow-up questions
_FOLLOW_UP_PATTERN = re.compile(
    r"\b(it|its|that|this|the project|the app|the tool|he|his|him|more|"
    r"details|expand|continue|else|why|how so|what about)\b",
    re.IGNORECASE,
)

REWRITE_SYSTEM_PROMPT = (
    "You are a query rewriting assistant for a technical portfolio search engine "
    "about Aamir Mohammed Khan.\n"
    "Given the recent chat history and the user's latest follow-up question, "
    "rewrite the follow-up question into a single, concise, standalone search query "
    "that includes the specific subject, project, or topic referenced.\n"
    "- If the question is already self-contained, return it unchanged.\n"
    "- Do NOT answer the question.\n"
    "- Do NOT output preamble, quotes, markdown formatting, or explanations.\n"
    "- Output ONLY the standalone search query."
)


def is_likely_follow_up(query: str, history: list[ChatHistoryMessage]) -> bool:
    """Determine whether an inbound query needs conversational context rewriting."""
    if not history:
        return False
    trimmed = query.strip()
    words = trimmed.split()
    # Very short queries (e.g. "tell me more", "expand", "why?")
    if len(words) <= 4:
        return True
    # If the query explicitly names "Aamir" and does not contain relative references,
    # it is already a self-contained candidate question.
    lower = trimmed.lower()
    if "aamir" in lower and not re.search(
        r"\b(that|it|its|the project|the app|the tool|more details|expand)\b",
        trimmed,
        re.I,
    ):
        return False
    # Queries containing pronouns or relative references
    return bool(_FOLLOW_UP_PATTERN.search(trimmed))


async def rewrite_follow_up_query(
    query: str,
    history: list[ChatHistoryMessage],
    llm: LLMClient,
    model: str | None = None,
) -> str:
    """Rewrite a follow-up query into a standalone search query.

    If rewriting is unneeded, fails, or produces empty text, falls back to
    the original query.
    """
    if not is_likely_follow_up(query, history):
        return query

    # Take the last 4 messages (2 exchanges) to keep context compact
    recent = history[-4:]
    history_text = "\n".join(f"{m.role.capitalize()}: {m.content}" for m in recent)
    user_prompt = (
        f"Chat History:\n{history_text}\n\n"
        f"Follow-up Question: {query}\n\n"
        "Standalone Search Query:"
    )

    messages = [
        Message(role="system", content=REWRITE_SYSTEM_PROMPT),
        Message(role="user", content=user_prompt),
    ]

    try:
        completion = await asyncio.wait_for(
            llm.complete(messages, model=model), timeout=2
        )
        rewritten = completion.content.strip().strip('"').strip("'")
        if rewritten and len(rewritten) > 2:
            logger.info("Rewrote follow-up query '%s' -> '%s'", query, rewritten)
            return rewritten
    except Exception as exc:
        logger.warning("Query rewriting failed: %s; using original query", exc)

    return query
