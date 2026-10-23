from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Schema for service health status."""

    status: str
    ready: bool

    model_config = ConfigDict(extra="forbid")


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Return service health and readiness status."""
    return HealthResponse(status="ok", ready=True)
