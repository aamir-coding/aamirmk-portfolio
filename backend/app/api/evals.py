"""Public engineering results, read from the same validated artifact as the badge."""

from fastapi import APIRouter, Response

from app.eval_summary import EvalSummary, load_summary

router = APIRouter(tags=["evals"])


@router.get("/eval-summary", response_model=EvalSummary)
def eval_summary(response: Response) -> EvalSummary:
    response.headers["Cache-Control"] = "no-store"
    return load_summary()
