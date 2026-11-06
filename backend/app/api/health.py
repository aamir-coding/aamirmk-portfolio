from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Schema for service health status."""

    status: str
    ready: bool
    assistant_state: Literal["ready", "resting"]

    model_config = ConfigDict(extra="forbid")


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    """Return service health and readiness status."""
    snapshot = request.app.state.llm.ledger.snapshot()
    return HealthResponse(
        status="ok",
        ready=True,
        assistant_state="resting" if snapshot.reason else "ready",
    )
