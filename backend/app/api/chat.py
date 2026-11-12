"""Chat endpoint — handles conversational requests grounded in Aamir's profile."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import aclosing, suppress
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from app.api.context import ResolvedCompany
from app.api.handoff import handoff_available
from app.companies import CompanyContext
from app.db.analytics import Analytics, AnalyticsRequest
from app.llm import (
    LLMAuthError,
    LLMCapacityError,
    LLMClient,
    LLMError,
    LLMRateLimitError,
    LLMUnavailableError,
    Message,
    ToolCall,
    get_llm_client,
)
from app.models import ChatRequest, ChatResponse, SourceCitation, TokenUsage
from app.prompt_loader import build_system_prompt
from app.retrieval.models import RetrievedChunk
from app.retrieval.retriever import Retriever, get_retriever
from app.retrieval.rewriter import rewrite_follow_up_query
from app.safety.guardrails import (
    SAFE_REFUSAL_MESSAGE,
    check_prompt_injection,
    data_block,
    format_safe_user_message,
)
from app.safety.rate_limiter import (
    RateLimitResult,
    check_rate_limit,
)
from app.settings import get_settings
from app.telemetry import (
    ObservedLLM,
    ObservedRetriever,
    RequestTelemetry,
    Trace,
    provenance,
)
from app.tools.projects import ProjectCardData
from app.tools.registry import HandoffOffer, ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])
RESTING_MESSAGE = (
    "Live answers are resting. Use a saved answer, "
    "read the resume source or contact Aamir."
)
HANDOFF_REPLY = "I don’t have enough verified information to answer that fully."
HandoffAvailable = Annotated[bool, Depends(handoff_available)]


def _record_answer(
    analytics: AnalyticsRequest | None,
    company: CompanyContext | None,
    question: str,
    telemetry: RequestTelemetry,
    handoff_offered: bool | None,
) -> uuid.UUID | None:
    if analytics is None:
        return None
    return analytics.record(
        company.slug if company else None,
        question=question,
        telemetry=telemetry,
        handoff_offered=handoff_offered,
    )


def weak_evidence(query: str, chunks: list[RetrievedChunk]) -> bool:
    if query.lower().strip(" .!?\t\r\n") in {
        "hi",
        "hello",
        "hey",
        "hi there",
        "hey there",
    }:
        return False
    public = [hit for hit in chunks if hit.chunk.indexed and not hit.chunk.private]
    if not public:
        return True
    similarities = [
        hit.dense_similarity for hit in public if hit.dense_similarity is not None
    ]
    # RRF values rank hits. The cosine floor only catches very weak matches.
    return bool(similarities) and max(similarities) < 0.55


class StreamHeartbeat(Enum):
    PING = "heartbeat"


async def stream_with_heartbeat(
    stream: AsyncIterator[Any],
    heartbeat_interval: float = 15.0,
) -> AsyncIterator[Any]:
    """Yield items from stream, or periodic heartbeat comment if idle."""
    anext_task: asyncio.Task[Any] | None = None
    stream_iter = aiter(stream)
    try:
        while True:
            if anext_task is None:
                anext_task = asyncio.create_task(stream_iter.__anext__())
            done, _ = await asyncio.wait(
                {anext_task},
                timeout=heartbeat_interval,
            )
            if done:
                try:
                    item = anext_task.result()
                    anext_task = None
                    yield item
                except StopAsyncIteration:
                    break
            else:
                yield StreamHeartbeat.PING
    finally:
        if anext_task is not None and not anext_task.done():
            anext_task.cancel()
            with suppress(asyncio.CancelledError):
                await anext_task
        close = getattr(stream_iter, "aclose", None)
        if close is not None:
            await close()


def extract_citations(chunks: list[RetrievedChunk]) -> list[SourceCitation]:
    """Convert retrieved chunks into deduplicated SourceCitation receipts."""
    seen_ids: set[str] = set()
    citations: list[SourceCitation] = []
    for rc in chunks:
        chunk = rc.chunk
        if chunk.private or not chunk.indexed:
            continue
        if chunk.id in seen_ids:
            continue
        seen_ids.add(chunk.id)
        citations.append(
            SourceCitation(
                chunk_id=chunk.id,
                title=chunk.title,
                type=chunk.type,
                source_section=chunk.source_section,
                source_url=chunk.source_url,
            )
        )
    return citations


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
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    rate_limit: RateLimitResult = Depends(check_rate_limit),
    company: ResolvedCompany = None,
    analytics: Analytics = None,
    can_handoff: HandoffAvailable = False,
) -> ChatResponse:
    """Process user message using LLM grounded with retrieved context chunks."""
    conv_id = request.conversation_id or uuid.uuid4().hex
    trace = Trace()
    llm = ObservedLLM(llm, trace, main_model=get_settings().LLM_MODEL_MAIN)
    retriever = ObservedRetriever(retriever, trace)
    versions = await asyncio.to_thread(provenance)

    # Attach rate limit visibility headers to successful response
    response.headers["X-RateLimit-Limit"] = str(rate_limit.limit)
    response.headers["X-RateLimit-Remaining"] = str(rate_limit.remaining)
    response.headers["X-RateLimit-Reset"] = str(rate_limit.reset_seconds)

    # 1. Guard against adversarial prompt injections (0 LLM token cost)
    injection_check = check_prompt_injection(
        "\n".join([request.message, *(entry.content for entry in request.history)])
    )
    if not injection_check.is_safe:
        trace.origin = "refused"
        trace.text()
        return ChatResponse(
            telemetry=trace.snapshot().model_copy(update=versions),
            reply=SAFE_REFUSAL_MESSAGE,
            conversation_id=conv_id,
            model="guardrails",
            usage=TokenUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            ),
            sources=[],
            cards=[],
        )

    # 2. Rewrite follow-up query if conversation history is present
    trace.set_stage("rewrite")
    search_query = await rewrite_follow_up_query(
        request.message,
        request.history,
        llm=llm,
        model=get_settings().LLM_MODEL_UTILITY,
    )

    # 3. Retrieve relevant factual context chunks & generate receipts
    trace.set_stage("retrieval")
    retrieved_chunks = await retriever.retrieve(search_query, top_k=4)
    if can_handoff and weak_evidence(search_query, retrieved_chunks):
        trace.text()
        telemetry = trace.snapshot().model_copy(update=versions)
        return ChatResponse(
            telemetry=telemetry,
            reply=HANDOFF_REPLY,
            conversation_id=conv_id,
            model="retrieval",
            usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            handoff=True,
            feedback_id=_record_answer(
                analytics, company, request.message, telemetry, True
            ),
        )
    citations = extract_citations(retrieved_chunks)
    system_prompt = build_system_prompt(
        retrieved_chunks, company_note=company.why_us if company else None
    )

    # 4. Format user query with XML boundary fencing and assemble conversation messages
    safe_user_content = format_safe_user_message(request.message)

    history_messages: list[Message] = []
    if request.history:
        for h in request.history[-6:]:
            if h.role == "user":
                history_messages.append(
                    Message(role="user", content=format_safe_user_message(h.content))
                )
            elif h.role == "assistant":
                history_messages.append(
                    Message(
                        role="assistant",
                        content=data_block("assistant_history", h.content),
                    )
                )

    messages = [
        Message(role="system", content=system_prompt),
        *history_messages,
        Message(role="user", content=safe_user_content),
    ]

    tool_schemas = tool_registry.get_schemas(handoff=can_handoff)
    summoned_cards: list[ProjectCardData] = []
    offer_handoff = False

    try:
        trace.set_stage("answer")
        completion = await llm.complete(messages, tools=tool_schemas)
        reply_text = completion.content
        total_tokens = completion.total_tokens
        prompt_tokens = completion.prompt_tokens
        completion_tokens = completion.completion_tokens

        # If LLM requested tool calls, execute them and run turn 2 for text reply
        if completion.tool_calls:
            if len(completion.tool_calls) > 8:
                raise LLMError("Too many tool requests")
            messages.append(
                Message(
                    role="assistant",
                    content="",
                    tool_calls=completion.tool_calls,
                )
            )
            for tc in completion.tool_calls:
                result = tool_registry.execute(tc.name, tc.arguments)
                if isinstance(result, ProjectCardData):
                    summoned_cards.append(result)
                    tool_content = json.dumps(
                        {"status": "card_displayed", "title": result.title}
                    )
                elif can_handoff and isinstance(result, HandoffOffer):
                    offer_handoff = True
                    tool_content = '{"status":"handoff_offered"}'
                else:
                    tool_content = json.dumps({"error": "Project not found"})

                messages.append(
                    Message(
                        role="tool",
                        content=tool_content,
                        tool_call_id=tc.id,
                        name=tc.name,
                    )
                )

            if offer_handoff:
                reply_text = HANDOFF_REPLY
            else:
                trace.set_stage("tool_answer")
                second_completion = await llm.complete(messages)
                reply_text = second_completion.content
                total_tokens += second_completion.total_tokens
                prompt_tokens += second_completion.prompt_tokens
                completion_tokens += second_completion.completion_tokens

    except LLMCapacityError as exc:
        logger.warning("Inference capacity error: %s", exc)
        raise HTTPException(
            status_code=429,
            detail=RESTING_MESSAGE,
            headers={"X-Assistant-State": "resting"},
        ) from exc
    except LLMRateLimitError as exc:
        logger.warning("Groq rate limit: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit reached. Please try again in a few moments.",
        ) from exc
    except LLMAuthError as exc:
        logger.error("Groq auth error: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM authentication failure. Please check server configuration.",
        ) from exc
    except LLMUnavailableError as exc:
        logger.error("Groq unavailable: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is currently unavailable. Please try again shortly.",
        ) from exc
    except LLMError as exc:
        logger.error("LLM unexpected error: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while communicating with the AI service.",
        ) from exc

    if len(reply_text) > 6000:
        raise HTTPException(
            status_code=503, detail="Generated answer exceeded its size limit."
        )
    trace.text()
    telemetry = trace.snapshot().model_copy(update=versions)
    return ChatResponse(
        telemetry=telemetry,
        reply=reply_text,
        conversation_id=conv_id,
        model=completion.model,
        usage=TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
        sources=citations,
        cards=summoned_cards,
        handoff=offer_handoff,
        feedback_id=_record_answer(
            analytics,
            company,
            request.message,
            telemetry,
            offer_handoff if can_handoff else None,
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
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    rate_limit: RateLimitResult = Depends(check_rate_limit),
    company: ResolvedCompany = None,
    analytics: Analytics = None,
    can_handoff: HandoffAvailable = False,
) -> StreamingResponse:
    """Stream user message using LLM via Server-Sent Events (SSE)."""
    conv_id = request.conversation_id or uuid.uuid4().hex
    trace = Trace()
    llm = ObservedLLM(llm, trace, main_model=get_settings().LLM_MODEL_MAIN)
    retriever = ObservedRetriever(retriever, trace)
    versions = await asyncio.to_thread(provenance)

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "X-RateLimit-Limit": str(rate_limit.limit),
        "X-RateLimit-Remaining": str(rate_limit.remaining),
        "X-RateLimit-Reset": str(rate_limit.reset_seconds),
    }

    # 1. Guard against adversarial prompt injections (0 LLM token cost)
    injection_check = check_prompt_injection(
        "\n".join([request.message, *(entry.content for entry in request.history)])
    )
    if not injection_check.is_safe:

        async def refusal_generator() -> AsyncIterator[str]:
            trace.origin = "refused"
            trace.text()
            payload = json.dumps({"token": SAFE_REFUSAL_MESSAGE})
            yield f"event: token\ndata: {payload}\n\n"
            done_payload = json.dumps(
                {
                    "conversation_id": conv_id,
                    "sources": [],
                    "cards": [],
                    "telemetry": {**trace.snapshot().model_dump(), **versions},
                }
            )
            yield f"event: done\ndata: {done_payload}\n\n"

        return StreamingResponse(
            refusal_generator(),
            media_type="text/event-stream",
            headers=headers,
        )

    # 2. Rewrite follow-up query if conversation history is present
    trace.set_stage("rewrite")
    search_query = await rewrite_follow_up_query(
        request.message,
        request.history,
        llm=llm,
        model=get_settings().LLM_MODEL_UTILITY,
    )

    # 3. Retrieve relevant factual context chunks & generate receipts
    trace.set_stage("retrieval")
    retrieved_chunks = await retriever.retrieve(search_query, top_k=4)
    if can_handoff and weak_evidence(search_query, retrieved_chunks):

        async def handoff_generator() -> AsyncIterator[str]:
            trace.text()
            telemetry = trace.snapshot().model_copy(update=versions)
            feedback_id = _record_answer(
                analytics, company, request.message, telemetry, True
            )
            payload = json.dumps({"token": HANDOFF_REPLY})
            yield f"event: token\ndata: {payload}\n\n"
            done_payload = json.dumps(
                {
                    "conversation_id": conv_id,
                    "sources": [],
                    "cards": [],
                    "telemetry": telemetry.model_dump(),
                    "handoff": True,
                    **({"feedback_id": str(feedback_id)} if feedback_id else {}),
                }
            )
            yield f"event: done\ndata: {done_payload}\n\n"

        return StreamingResponse(
            handoff_generator(), media_type="text/event-stream", headers=headers
        )
    citations = extract_citations(retrieved_chunks)
    system_prompt = build_system_prompt(
        retrieved_chunks, company_note=company.why_us if company else None
    )

    # 4. Format user query with XML boundary fencing and assemble conversation messages
    safe_user_content = format_safe_user_message(request.message)

    history_messages: list[Message] = []
    if request.history:
        for h in request.history[-6:]:
            if h.role == "user":
                history_messages.append(
                    Message(role="user", content=format_safe_user_message(h.content))
                )
            elif h.role == "assistant":
                history_messages.append(
                    Message(
                        role="assistant",
                        content=data_block("assistant_history", h.content),
                    )
                )

    messages = [
        Message(role="system", content=system_prompt),
        *history_messages,
        Message(role="user", content=safe_user_content),
    ]

    tool_schemas = tool_registry.get_schemas(handoff=can_handoff)

    async def event_generator() -> AsyncIterator[str]:
        tokens_emitted = 0
        summoned_cards: list[ProjectCardData] = []
        output_chars = 0
        offer_handoff = False
        try:
            trace.set_stage("answer")
            # Emit verified source receipts before stream begins
            if citations:
                sources_payload = json.dumps(
                    {"sources": [c.model_dump() for c in citations]}
                )
                yield f"event: sources\ndata: {sources_payload}\n\n"

            # Stream Turn 1: checks for tool calls or direct text
            detected_tool_calls: list[ToolCall] = []
            async with aclosing(
                stream_with_heartbeat(llm.stream(messages, tools=tool_schemas))
            ) as items:
                async for item in items:
                    if item is StreamHeartbeat.PING:
                        yield ": heartbeat\n\n"
                        continue
                    if isinstance(item, ToolCall):
                        detected_tool_calls.append(item)
                        if len(detected_tool_calls) > 8:
                            raise LLMError("Too many tool requests")
                    else:
                        output_chars += len(item)
                        if output_chars > 6000:
                            raise LLMError("Generated answer exceeded its size limit")
                        trace.text()
                        tokens_emitted += 1
                        payload = json.dumps({"token": item})
                        yield f"event: token\ndata: {payload}\n\n"

            # If tool calls were made, resolve them and stream Turn 2 explanation
            if detected_tool_calls:
                trace.set_stage("tools")
                messages.append(
                    Message(
                        role="assistant",
                        content="",
                        tool_calls=detected_tool_calls,
                    )
                )
                for tc in detected_tool_calls:
                    result = tool_registry.execute(tc.name, tc.arguments)
                    if isinstance(result, ProjectCardData):
                        summoned_cards.append(result)
                        card_payload = json.dumps({"card": result.model_dump()})
                        yield f"event: card\ndata: {card_payload}\n\n"
                        tool_content = json.dumps(
                            {"status": "card_displayed", "title": result.title}
                        )
                    elif can_handoff and isinstance(result, HandoffOffer):
                        offer_handoff = True
                        tool_content = '{"status":"handoff_offered"}'
                    else:
                        tool_content = json.dumps({"error": "Project not found"})

                    messages.append(
                        Message(
                            role="tool",
                            content=tool_content,
                            tool_call_id=tc.id,
                            name=tc.name,
                        )
                    )

            if offer_handoff:
                trace.text()
                text = f"\n\n{HANDOFF_REPLY}" if tokens_emitted else HANDOFF_REPLY
                if output_chars + len(text) <= 6000:
                    payload = json.dumps({"token": text})
                    yield f"event: token\ndata: {payload}\n\n"
            elif detected_tool_calls:
                trace.set_stage("tool_answer")
                async with aclosing(
                    stream_with_heartbeat(llm.stream(messages))
                ) as items:
                    async for token in items:
                        if token is StreamHeartbeat.PING:
                            yield ": heartbeat\n\n"
                            continue
                        if isinstance(token, str):
                            output_chars += len(token)
                            if output_chars > 6000:
                                raise LLMError(
                                    "Generated answer exceeded its size limit"
                                )
                            trace.text()
                            tokens_emitted += 1
                            payload = json.dumps({"token": token})
                            yield f"event: token\ndata: {payload}\n\n"

            telemetry = trace.snapshot().model_copy(update=versions)
            feedback_id = _record_answer(
                analytics,
                company,
                request.message,
                telemetry,
                offer_handoff if can_handoff else None,
            )
            done_payload = json.dumps(
                {
                    "conversation_id": conv_id,
                    "sources": [c.model_dump() for c in citations],
                    "cards": [c.model_dump() for c in summoned_cards],
                    "telemetry": telemetry.model_dump(),
                    **({"handoff": True} if offer_handoff else {}),
                    **({"feedback_id": str(feedback_id)} if feedback_id else {}),
                }
            )
            yield f"event: done\ndata: {done_payload}\n\n"

        except LLMCapacityError as exc:
            logger.warning("Inference capacity error during stream: %s", exc)
            err_payload = json.dumps(
                {
                    "detail": RESTING_MESSAGE,
                    "state": "resting",
                    "telemetry": {**trace.snapshot().model_dump(), **versions},
                }
            )
            yield f"event: error\ndata: {err_payload}\n\n"
        except LLMRateLimitError as exc:
            logger.warning("Groq rate limit during stream: %s", type(exc).__name__)
            err_payload = json.dumps(
                {"detail": "Rate limit reached. Please try again in a few moments."}
            )
            err_payload = json.dumps(
                {
                    **json.loads(err_payload),
                    "telemetry": {**trace.snapshot().model_dump(), **versions},
                }
            )
            yield f"event: error\ndata: {err_payload}\n\n"
        except LLMAuthError as exc:
            logger.error("Groq auth error during stream: %s", type(exc).__name__)
            err_payload = json.dumps(
                {
                    "detail": "LLM authentication failure. "
                    "Please check server configuration."
                }
            )
            err_payload = json.dumps(
                {
                    **json.loads(err_payload),
                    "telemetry": {**trace.snapshot().model_dump(), **versions},
                }
            )
            yield f"event: error\ndata: {err_payload}\n\n"
        except (LLMUnavailableError, LLMError) as exc:
            logger.error("LLM error during stream: %s", type(exc).__name__)
            err_payload = json.dumps(
                {
                    "detail": "AI service is currently unavailable. "
                    "Please try again shortly."
                }
            )
            err_payload = json.dumps(
                {
                    **json.loads(err_payload),
                    "telemetry": {**trace.snapshot().model_dump(), **versions},
                }
            )
            yield f"event: error\ndata: {err_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=headers,
    )
