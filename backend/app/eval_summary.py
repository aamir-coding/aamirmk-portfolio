"""Allowlisted public projection. No raw answers, human rationales or held-out IDs."""

from __future__ import annotations

from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.retrieval.artifacts import Sha256, canonical_sha256, corpus_sha256, file_sha256
from app.retrieval.loader import FactLoader

APP_ROOT = Path(__file__).parent
DEFAULT_ARTIFACT = APP_ROOT / "data/eval-summary.json"


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Count(PublicModel):
    passed: int = Field(ge=0)
    total: int = Field(gt=0)

    @model_validator(mode="after")
    def valid_count(self) -> Self:
        if self.passed > self.total:
            raise ValueError("Numerator exceeds denominator")
        return self


class CategoryCount(PublicModel):
    category: str
    passed: int = Field(ge=0)
    total: int = Field(ge=0)
    skipped: int = Field(ge=0)

    @model_validator(mode="after")
    def valid_category(self) -> Self:
        if self.passed + self.skipped > self.total:
            raise ValueError("Invalid category totals")
        return self


class RetrievalMetric(PublicModel):
    suite: str
    metric: Literal["hit_at_3", "hit_at_5", "recall_at_3", "recall_at_5", "mrr_at_5"]
    numerator: float = Field(ge=0)
    denominator: int = Field(ge=0)

    @model_validator(mode="after")
    def valid_metric(self) -> Self:
        if self.numerator > self.denominator:
            raise ValueError("Metric numerator exceeds denominator")
        return self


class JudgeValidation(PublicModel):
    kind: Literal["judge_human_agreement"] = "judge_human_agreement"
    status: Literal["failed", "passed"]
    artifact_sha256: Sha256
    rubric_sha256: Sha256
    model: Literal["openai/gpt-oss-20b"] = "openai/gpt-oss-20b"
    axes: dict[Literal["support", "completeness", "behavior", "tone"], Count]
    failures_by_axis: dict[str, int]
    disagreements: list[dict[Literal["item_id", "axis", "human", "judge"], str]]

    @model_validator(mode="after")
    def coherent_validation(self) -> Self:
        if set(self.axes) != {"support", "completeness", "behavior", "tone"}:
            raise ValueError("Four axes required")
        passed = all(c.passed / c.total >= 0.8 for c in self.axes.values())
        if (self.status == "passed") != passed:
            raise ValueError("Validation gate differs from actual counts")
        if self.failures_by_axis != {
            axis: c.total - c.passed for axis, c in self.axes.items()
        }:
            raise ValueError("Validation failure counts disagree")
        return self


class PublicReport(PublicModel):
    kind: Literal["offline_engineering_checks"] = "offline_engineering_checks"
    generated_at: datetime
    source_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    source_dirty: bool
    source_result_sha256: Sha256
    runtime_sha256: Sha256
    replay: Count
    categories: list[CategoryCount]
    retrieval: list[RetrievalMetric]
    failed_checks: list[str]
    held_out_reserved: int = Field(gt=0)
    held_out_executed: Literal[False] = False
    draft_chunks: int = Field(ge=0)
    generation_accuracy_available: Literal[False] = False
    judge_validation: JudgeValidation
    development_without_recordings: int = Field(ge=0)

    @model_validator(mode="after")
    def coherent_categories(self) -> Self:
        if (
            sum(c.total for c in self.categories) != self.replay.total
            or sum(c.passed for c in self.categories) != self.replay.passed
        ):
            raise ValueError("Category counts differ from replay totals")
        if (
            len(self.retrieval) != 10
            or len({(r.suite, r.metric) for r in self.retrieval}) != 10
        ):
            raise ValueError("Both complete retrieval metric sets are required")
        return self

    @property
    def badge(self) -> str:
        return f"Replay checks: {self.replay.passed}/{self.replay.total} (offline)"


class PublicArtifact(PublicModel):
    schema_version: Literal[1] = 1
    report_sha256: Sha256
    report: PublicReport

    @model_validator(mode="after")
    def intact(self) -> Self:
        if self.report_sha256 != canonical_sha256(self.report.model_dump(mode="json")):
            raise ValueError("Public projection checksum differs")
        return self


class EvalSummary(PublicModel):
    status: Literal["available", "unavailable", "stale"]
    badge: str
    report: PublicReport | None = None
    reason: str | None = None


def runtime_fingerprint() -> str:
    # Independent of git availability and OS newline convention on Render.
    paths = [*APP_ROOT.rglob("*.py"), *(APP_ROOT / "prompts").glob("*.txt")]
    return canonical_sha256(
        {
            "source": {
                p.relative_to(APP_ROOT).as_posix(): p.read_text(encoding="utf-8")
                for p in sorted(paths)
            },
            "corpus": corpus_sha256(FactLoader().load_all()),
            "index": file_sha256(APP_ROOT / "retrieval/facts_embeddings.npz"),
            "dependencies": {
                name: version(name)
                for name in ("fastembed", "numpy", "pydantic", "groq")
            },
        }
    )


def load_summary(path: Path = DEFAULT_ARTIFACT) -> EvalSummary:
    try:
        artifact = PublicArtifact.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return EvalSummary(
            status="unavailable",
            badge="Evaluation results unavailable",
            reason="No complete, valid result artifact is installed.",
        )
    try:
        if artifact.report.runtime_sha256 != runtime_fingerprint():
            return EvalSummary(
                status="stale",
                badge="Evaluation results stale",
                reason="The installed result describes different source or evidence.",
            )
    except (OSError, ValueError):
        return EvalSummary(
            status="unavailable",
            badge="Evaluation results unavailable",
            reason="Current evidence provenance could not be verified.",
        )
    return EvalSummary(
        status="available", badge=artifact.report.badge, report=artifact.report
    )
