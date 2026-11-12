"""Explicit recruiter handoff submission."""

import logging
from typing import Literal

import asyncpg
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import UUID4, BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.handoff import HandoffConflict, HandoffRequest, Handoffs
from app.safety.rate_limiter import check_handoff_rate_limit

router = APIRouter(tags=["handoff"])
logger = logging.getLogger(__name__)


async def handoff_available(request: Request) -> bool:
    return request.app.state.handoffs is not None


class HandoffAccepted(BaseModel):
    id: UUID4
    status: Literal["accepted"] = "accepted"


@router.post("/handoff", status_code=202)
async def submit_handoff(
    request: Request, response: Response, payload: HandoffRequest
) -> HandoffAccepted:
    handoffs: Handoffs | None = request.app.state.handoffs
    if handoffs is None:
        raise HTTPException(
            503, "Handoff is unavailable. You can contact Aamir directly."
        )
    await check_handoff_rate_limit(request)
    try:
        await handoffs.accept(payload)
    except HandoffConflict:
        raise HTTPException(409, "This handoff ID was already used.") from None
    except (
        OSError,
        SQLAlchemyError,
        asyncpg.PostgresError,
        asyncpg.InterfaceError,
    ) as exc:
        logger.warning(
            "[%s] Handoff could not be saved: %s",
            request.state.request_id,
            type(exc).__name__,
        )
        raise HTTPException(
            503, "Handoff could not be saved. Please try again."
        ) from None
    response.headers["Cache-Control"] = "no-store"
    return HandoffAccepted(id=payload.id)
