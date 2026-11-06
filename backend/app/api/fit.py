"""API endpoints for JD Fit Report generation and preset discovery."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from app.api.chat import StreamHeartbeat, stream_with_heartbeat
from app.fit.models import FitRequest
from app.fit.pipeline import FitPipeline
from app.llm import LLMClient, get_llm_client
from app.retrieval.retriever import Retriever, get_retriever
from app.safety.rate_limiter import check_fit_rate_limit
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["fit"])


def get_fit_pipeline(
    request: Request,
    llm: LLMClient = Depends(get_llm_client),
    retriever: Retriever = Depends(get_retriever),
    settings: Settings = Depends(get_settings),
) -> FitPipeline:
    """Request-local orchestration using an app-owned provider and shared cache."""
    override = getattr(request.app.state, "fit_pipeline_override", None)
    if override is not None:
        return override
    pipeline = FitPipeline(
        llm=llm,
        retriever=retriever,
        settings=settings,
        cache=request.app.state.fit_cache,
    )
    return pipeline


def set_fit_pipeline(pipeline: FitPipeline | None) -> None:
    """Legacy test helper; override only the exported default application's state."""
    from app.main import app

    app.state.fit_pipeline_override = pipeline


@router.get(
    "/fit/presets",
    summary="Get curated sample job descriptions for quick evaluation",
)
async def get_fit_presets(request: Request) -> list[dict[str, Any]]:
    """Return curated sample JDs with pre-evaluated golden reports.

    Enables 1-click exploration without burning Groq tokens.
    """
    samples = request.app.state.fit_cache.presets()
    return [
        {
            "id": s.id,
            "title": s.title,
            "company": s.company,
            "match_expectation": s.match_expectation,
            "text": s.text,
            "report": s.report.model_dump() if s.report else None,
        }
        for s in samples
    ]


@router.post(
    "/fit",
    summary="Generate a streaming, evidence-backed Job Fit Report",
    status_code=status.HTTP_200_OK,
)
async def generate_fit_report(
    body: FitRequest,
    _rate: Any = Depends(check_fit_rate_limit),
    pipeline: FitPipeline = Depends(get_fit_pipeline),
) -> StreamingResponse:
    """Analyze a pasted job description and stream progress and fit report via SSE."""
    logger.info("Initiating fit report generation")

    async def sse_event_generator() -> AsyncIterator[str]:
        async with aclosing(pipeline.run(body)) as frames:
            async for frame in frames:
                event_name = frame["event"]
                event_data = json.dumps(frame["data"])
                yield f"event: {event_name}\ndata: {event_data}\n\n"

    async def transport_stream() -> AsyncIterator[str]:
        async with aclosing(stream_with_heartbeat(sse_event_generator())) as frames:
            async for item in frames:
                yield ": heartbeat\n\n" if item is StreamHeartbeat.PING else item

    return StreamingResponse(
        transport_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
