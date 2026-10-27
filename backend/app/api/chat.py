"""Chat endpoint — handles conversational requests grounded in Aamir's profile."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.llm import (
    LLMAuthError,
    LLMClient,
    LLMError,
    LLMRateLimitError,
    LLMUnavailableError,
    Message,
    get_llm_client,
)
from app.models import ChatRequest, ChatResponse, TokenUsage
from app.prompt_loader import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Non-streaming chat query grounded in Aamir's verified résumé",
)
async def chat(
    request: ChatRequest,
    llm: LLMClient = Depends(get_llm_client),
) -> ChatResponse:
    """Process user message using LLM grounded with system prompt context."""
    conv_id = request.conversation_id or uuid.uuid4().hex

    messages = [
        Message(role="system", content=SYSTEM_PROMPT),
        Message(role="user", content=request.message),
    ]

    try:
        completion = await llm.complete(messages)
    except LLMRateLimitError as exc:
        logger.warning("[%s] Groq rate limit: %s", conv_id, exc)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit reached. Please try again in a few moments.",
        ) from exc
    except LLMAuthError as exc:
        logger.error("[%s] Groq auth error: %s", conv_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM authentication failure. Please check server configuration.",
        ) from exc
    except LLMUnavailableError as exc:
        logger.error("[%s] Groq unavailable: %s", conv_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is currently unavailable. Please try again shortly.",
        ) from exc
    except LLMError as exc:
        logger.error("[%s] LLM unexpected error: %s", conv_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while communicating with the AI service.",
        ) from exc

    return ChatResponse(
        reply=completion.content,
        conversation_id=conv_id,
        model=completion.model,
        usage=TokenUsage(
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            total_tokens=completion.total_tokens,
        ),
    )


@router.post(
    "/chat/stream",
    status_code=status.HTTP_200_OK,
    summary="Streaming chat query grounded in Aamir's verified résumé via SSE",
)
async def chat_stream(
    request: ChatRequest,
    llm: LLMClient = Depends(get_llm_client),
) -> StreamingResponse:
    """Stream user message using LLM via Server-Sent Events (SSE)."""
    conv_id = request.conversation_id or uuid.uuid4().hex

    messages = [
        Message(role="system", content=SYSTEM_PROMPT),
        Message(role="user", content=request.message),
    ]

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for token in llm.stream(messages):
                payload = json.dumps({"token": token})
                yield f"event: token\ndata: {payload}\n\n"

            done_payload = json.dumps({"conversation_id": conv_id})
            yield f"event: done\ndata: {done_payload}\n\n"
        except LLMRateLimitError as exc:
            logger.warning("[%s] Groq rate limit during stream: %s", conv_id, exc)
            err_payload = json.dumps(
                {"detail": "Rate limit reached. Please try again in a few moments."}
            )
            yield f"event: error\ndata: {err_payload}\n\n"
        except LLMAuthError as exc:
            logger.error("[%s] Groq auth error during stream: %s", conv_id, exc)
            err_payload = json.dumps(
                {
                    "detail": "LLM authentication failure. "
                    "Please check server configuration."
                }
            )
            yield f"event: error\ndata: {err_payload}\n\n"
        except (LLMUnavailableError, LLMError) as exc:
            logger.error("[%s] LLM error during stream: %s", conv_id, exc)
            err_payload = json.dumps(
                {
                    "detail": "AI service is currently unavailable. "
                    "Please try again shortly."
                }
            )
            yield f"event: error\ndata: {err_payload}\n\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=headers,
    )
