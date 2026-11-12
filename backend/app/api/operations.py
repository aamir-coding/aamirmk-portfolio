"""Opt-in operator adapter to the existing one-shot ledger interface."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from app.safety.admission import Allowance, InferenceLedger, LedgerSnapshot
from app.safety.boot_quota import (
    BootQuota,
    DurableCapacityUnavailable,
    QuotaStorageUnavailable,
)


class OperatorStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    boot_id: str
    capacity: LedgerSnapshot


async def operator_ledger(request: Request) -> InferenceLedger:
    configured = request.app.state.settings.OPS_TOKEN.get_secret_value()
    if not configured:
        raise HTTPException(404, "Not Found")
    values = request.headers.getlist("authorization")
    supplied = values[0] if len(values) == 1 else ""
    expected = f"Bearer {configured}".encode()
    valid = len(supplied) <= 135 and secrets.compare_digest(supplied.encode(), expected)
    valid = valid and "origin" not in request.headers
    decision = await request.app.state.ops_rate_limiter.check(
        "valid" if valid else "invalid"
    )
    if not decision.allowed:
        raise HTTPException(
            429, "Operator request limit reached", headers={"Retry-After": "60"}
        )
    if not valid:
        raise HTTPException(401, "Operator authentication required")
    return request.app.state.llm.ledger


router = APIRouter(prefix="/ops", include_in_schema=False)


@router.get("/inference", response_model=OperatorStatus)
async def inference_status(
    ledger: InferenceLedger = Depends(operator_ledger),
) -> OperatorStatus:
    return OperatorStatus(boot_id=ledger.boot_id, capacity=ledger.snapshot())


@router.post("/inference", response_model=LedgerSnapshot)
async def activate_inference(
    allowance: Allowance,
    request: Request,
    ledger: InferenceLedger = Depends(operator_ledger),
) -> LedgerSnapshot:
    settings = request.app.state.settings
    limits = settings.INFERENCE_SHARED_LIMITS
    if allowance.requests > limits.rpd or allowance.tokens > limits.tpd:
        raise HTTPException(409, "Allowance exceeds configured ceilings")
    try:
        if settings.DURABLE_INFERENCE_QUOTA:
            boot_quota: BootQuota | None = request.app.state.boot_quota
            if boot_quota is None:
                raise QuotaStorageUnavailable
            await boot_quota.authorize(allowance)
        else:
            ledger.authorize(allowance)
    except (ValueError, DurableCapacityUnavailable):
        raise HTTPException(
            409, "Allowance rejected for this boot or time window"
        ) from None
    except QuotaStorageUnavailable:
        raise HTTPException(503, "Durable quota storage is unavailable.") from None
    return ledger.snapshot()
