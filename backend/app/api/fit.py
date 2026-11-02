"""API endpoints for JD Fit Report generation and preset discovery."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.api.chat import stream_with_heartbeat
from app.fit.models import FitRequest
from app.fit.pipeline import FitPipeline
from app.fit.sample_jds import load_sample_jds
from app.llm import LLMClient, get_llm_client
from app.retrieval.retriever import Retriever, get_retriever
from app.safety.quota import check_daily_quota
from app.safety.rate_limiter import check_fit_rate_limit
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["fit"])

_fit_pipeline_instance: FitPipeline | None = None


def get_fit_pipeline(
    llm: LLMClient = Depends(get_llm_client),
    retriever: Retriever = Depends(get_retriever),
    settings: Settings = Depends(get_settings),
) -> FitPipeline:
    """Dependency provider returning singleton FitPipeline instance."""
    global _fit_pipeline_instance
    if _fit_pipeline_instance is None:
        _fit_pipeline_instance = FitPipeline(
            llm=llm,
            retriever=retriever,
            settings=settings,
        )
    return _fit_pipeline_instance


def set_fit_pipeline(pipeline: FitPipeline | None) -> None:
    """Set or override active FitPipeline instance (for test isolation)."""
    global _fit_pipeline_instance
    _fit_pipeline_instance = pipeline


@router.get(
    "/fit/presets",
    summary="Get curated sample job descriptions for quick evaluation",
)
async def get_fit_presets() -> list[dict[str, Any]]:
    """Return curated sample JDs with pre-evaluated golden reports.

    Enables 1-click exploration without burning Groq tokens.
    """
    samples = load_sample_jds()
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
    _quota: Any = Depends(check_daily_quota),
    pipeline: FitPipeline = Depends(get_fit_pipeline),
) -> StreamingResponse:
    """Analyze a pasted job description and stream progress and fit report via SSE."""
    logger.info("Initiating fit report generation (hash: %s)", body.compute_hash())

    async def sse_event_generator() -> AsyncIterator[str]:
        async for frame in pipeline.run(body):
            event_name = frame["event"]
            event_data = json.dumps(frame["data"])
            yield f"event: {event_name}\ndata: {event_data}\n\n"

    # Wrap with 15s heartbeats to keep idle cloud proxies alive
    stream = stream_with_heartbeat(sse_event_generator())

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
