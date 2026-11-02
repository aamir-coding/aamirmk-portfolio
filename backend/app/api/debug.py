"""Development inspection endpoints for testing retrieval and system state."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.retrieval.retriever import Retriever, get_retriever
from app.settings import Settings, get_settings

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get(
    "/retrieve",
    summary="Development retrieval inspection endpoint",
)
async def debug_retrieve(
    request: Request,
    q: str = Query(..., min_length=1, description="Query string to retrieve"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to retrieve"),
    retriever: Retriever = Depends(get_retriever),
) -> dict[str, Any]:
    """Retrieve top-k chunks and scores for debugging retrieval quality."""
    settings: Settings = getattr(request.app.state, "settings", get_settings())
    if settings.ENVIRONMENT == "production" and not getattr(
        settings, "ENABLE_DEBUG_RETRIEVAL", False
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debug retrieval endpoint is disabled in production.",
        )

    results = await retriever.retrieve(q, top_k=top_k)
    return {
        "query": q,
        "count": len(results),
        "results": [
            {
                "id": r.chunk.id,
                "title": r.chunk.title,
                "score": r.score,
                "rank": r.rank,
                "retrieval_method": r.retrieval_method,
                "source_section": r.chunk.source_section,
                "source_url": r.chunk.source_url,
                "snippet": r.chunk.content[:200],
            }
            for r in results
        ],
    }
