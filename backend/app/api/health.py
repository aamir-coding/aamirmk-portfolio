from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict

from app.release import ReleaseInfo


class HealthResponse(BaseModel):
    """Schema for service health status."""

    status: str
    ready: bool
    assistant_state: Literal["ready", "resting"]
    release: ReleaseInfo

    model_config = ConfigDict(extra="forbid")


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request, response: Response) -> HealthResponse:
    """Return service health and readiness status."""
    snapshot = request.app.state.llm.ledger.snapshot()
    ready = request.app.state.retrieval_ready
    response.status_code = 200 if ready else 503
    return HealthResponse(
        status="ok" if ready else "unavailable",
        ready=ready,
        assistant_state="resting" if snapshot.reason else "ready",
        release=request.app.state.release,
    )
