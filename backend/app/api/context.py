"""Per-company recruiter context shared by the cover and chat routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel

from app.companies import CompanyContext

router = APIRouter(tags=["context"])


async def resolve_company(
    request: Request, slug: Annotated[str | None, Query(alias="for")] = None
) -> CompanyContext | None:
    contexts: dict[str, CompanyContext] = request.app.state.company_contexts
    return contexts.get(slug) if slug is not None else None


ResolvedCompany = Annotated[CompanyContext | None, Depends(resolve_company)]


class ContextResponse(BaseModel):
    company: CompanyContext | None


@router.get("/context")
async def get_context(response: Response, company: ResolvedCompany) -> ContextResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return ContextResponse(company=company)
