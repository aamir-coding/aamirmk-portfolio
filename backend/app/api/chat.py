"""Chat endpoint — handles conversational requests grounded in Aamir's profile."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Response, status
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
from app.prompt_loader import build_system_prompt
from app.retrieval.retriever import Retriever, get_retriever
from app.safety.guardrails import (
    SAFE_REFUSAL_MESSAGE,
    check_prompt_injection,
    format_safe_user_message,
)
from app.safety.quota import (
    DailyQuotaGuard,
    check_daily_quota,
    get_quota_guard,
)
from app.safety.rate_limiter import (
    RateLimitResult,
    check_rate_limit,
)

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
    response: Response,
    llm: LLMClient = Depends(get_llm_client),
    retriever: Retriever = Depends(get_retriever),
    rate_limit: RateLimitResult = Depends(check_rate_limit),
    _quota: None = Depends(check_daily_quota),
    quota_guard: DailyQuotaGuard = Depends(get_quota_guard),
) -> ChatResponse:
    """Process user message using LLM grounded with retrieved context chunks."""
    conv_id = request.conversation_id or uuid.uuid4().hex

    # Attach rate limit visibility headers to successful response
    response.headers["X-RateLimit-Limit"] = str(rate_limit.limit)
    response.headers["X-RateLimit-Remaining"] = str(rate_limit.remaining)
    response.headers["X-RateLimit-Reset"] = str(rate_limit.reset_seconds)

    # 1. Guard against adversarial prompt injections (0 LLM token cost)
    injection_check = check_prompt_injection(request.message)
    if not injection_check.is_safe:
        return ChatResponse(
            reply=SAFE_REFUSAL_MESSAGE,
            conversation_id=conv_id,
            model="guardrails",
            usage=TokenUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            ),
        )

    # 2. Retrieve relevant factual context chunks
    retrieved_chunks = await retriever.retrieve(request.message, top_k=4)
    system_prompt = build_system_prompt(retrieved_chunks)

    # 3. Format user query with XML boundary fencing
    safe_user_content = format_safe_user_message(request.message)

    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=safe_user_content),
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

    # 4. Track actual consumed tokens against daily quota
    await quota_guard.record_usage(tokens=completion.total_tokens)

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
    retriever: Retriever = Depends(get_retriever),
    rate_limit: RateLimitResult = Depends(check_rate_limit),
    _quota: None = Depends(check_daily_quota),
    quota_guard: DailyQuotaGuard = Depends(get_quota_guard),
) -> StreamingResponse:
    """Stream user message using LLM via Server-Sent Events (SSE)."""
    conv_id = request.conversation_id or uuid.uuid4().hex

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "X-RateLimit-Limit": str(rate_limit.limit),
        "X-RateLimit-Remaining": str(rate_limit.remaining),
        "X-RateLimit-Reset": str(rate_limit.reset_seconds),
    }

    # 1. Guard against adversarial prompt injections (0 LLM token cost)
    injection_check = check_prompt_injection(request.message)
    if not injection_check.is_safe:

        async def refusal_generator() -> AsyncIterator[str]:
            payload = json.dumps({"token": SAFE_REFUSAL_MESSAGE})
            yield f"event: token\ndata: {payload}\n\n"
            done_payload = json.dumps({"conversation_id": conv_id})
            yield f"event: done\ndata: {done_payload}\n\n"

        return StreamingResponse(
            refusal_generator(),
            media_type="text/event-stream",
            headers=headers,
        )

    # 2. Retrieve relevant factual context chunks
    retrieved_chunks = await retriever.retrieve(request.message, top_k=4)
    system_prompt = build_system_prompt(retrieved_chunks)

    # 3. Format user query with XML boundary fencing
    safe_user_content = format_safe_user_message(request.message)

    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=safe_user_content),
    ]

    async def event_generator() -> AsyncIterator[str]:
        tokens_emitted = 0
        try:
            async for token in llm.stream(messages):
                tokens_emitted += 1
                payload = json.dumps({"token": token})
                yield f"event: token\ndata: {payload}\n\n"

            done_payload = json.dumps({"conversation_id": conv_id})
            yield f"event: done\ndata: {done_payload}\n\n"

            # 4. Track tokens (estimated prompt + generated tokens)
            estimated_prompt_tokens = max(len(system_prompt) // 4, 100)
            await quota_guard.record_usage(
                tokens=estimated_prompt_tokens + tokens_emitted
            )
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

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=headers,
    )
