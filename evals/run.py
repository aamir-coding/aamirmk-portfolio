"""Offline retrieval diagnostics: python -m evals.run (never calls Groq)."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import statistics
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Literal, Self

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import yaml  # noqa: E402
from pydantic import BaseModel, Field, model_validator  # noqa: E402

from app.retrieval.artifacts import Sha256, canonical_sha256, file_sha256  # noqa: E402
from app.retrieval.retriever import Retriever  # noqa: E402
from evals.dataset import (  # noqa: E402
    DEFAULT_ROOT,
    REPO_ROOT,
    IndexSnapshot,
    load_cases,
    load_manifest,
    validate_source_ids,
    verify_dataset,
)
from evals.metrics import (  # noqa: E402
    MetricModel,
    RankingScores,
    RetrievalMetrics,
    score_ranking,
    summarize_scores,
)
from evals.schemas import CaseSuite, EvalCase, Text  # noqa: E402

SkipReason = Literal[
    "no_source_expectation",
    "requires_recorded_rewrite",
    "requires_requirement_extraction",
    "protocol_case",
]


class RetrievalRunError(RuntimeError):
    """An incomplete run must not produce a passing result."""


class CaseResult(MetricModel):
    id: str
    category: str
    retrieved_ids: list[str] = Field(default_factory=list)
    scores: RankingScores | None = None
    latency_ms: float | None = Field(default=None, ge=0)
    skip_reason: SkipReason | None = None

    @model_validator(mode="after")
    def scored_or_skipped(self) -> Self:
        if self.skip_reason is not None:
            if (
                self.scores is not None
                or self.latency_ms is not None
                or self.retrieved_ids
            ):
                raise ValueError("A skipped case cannot contain measured scores")
        elif self.scores is None or self.latency_ms is None:
            raise ValueError("An evaluated case requires scores and measured latency")
        return self


class LatencySummary(MetricModel):
    count: int = Field(ge=0)
    mean_ms: float | None
    p50_ms: float | None
    p95_ms: float | None
    p99_ms: float | None
    percentile_method: Literal["nearest_rank"] = "nearest_rank"


class CategoryMetrics(RetrievalMetrics):
    total_cases: int
    excluded_cases: int


class SuiteReport(MetricModel):
    total_cases: int
    evaluated_cases: int
    excluded_cases: int
    metrics: RetrievalMetrics
    by_category: dict[str, CategoryMetrics]
    cases: list[CaseResult]
    latency: LatencySummary
    quality_passed: bool
    failed_quality_checks: list[str]
    thresholds: dict[str, float]
    query_mode: Literal["raw_query_top5"] = "raw_query_top5"


class LegacyRetrievalQuestion(BaseModel):
    id: Text
    question: Text
    intent_tag: Text
    expected_chunk_ids: list[Text] = Field(min_length=1)


class LegacyRetrievalSeeds(BaseModel):
    questions: list[LegacyRetrievalQuestion] = Field(min_length=1)


def load_legacy_cases() -> list[EvalCase]:
    document = LegacyRetrievalSeeds.model_validate(
        yaml.safe_load(
            (DEFAULT_ROOT / "seed_questions.yaml").read_text(encoding="utf-8")
        )
    )
    return CaseSuite(
        version="legacy-development",
        cases=[
            EvalCase.model_validate(
                {
                    "id": item.id,
                    "version": 1,
                    "group_id": f"legacy-{item.id}",
                    "split": "development",
                    "category": item.intent_tag.replace("-", "_"),
                    "target": "chat",
                    "origin": {"kind": "legacy_seed", "reference": item.id},
                    "conversation": [{"role": "user", "content": item.question}],
                    "checks": {
                        "sources": {
                            "mode": "any_of",
                            "ids": list(dict.fromkeys(item.expected_chunk_ids)),
                        },
                        "support_expectations": [
                            "Retrieve a listed legacy source; "
                            "semantic answer labels are not evaluated here."
                        ],
                    },
                }
            )
            for item in document.questions
        ],
    ).cases


def _skip_reason(case: EvalCase) -> SkipReason | None:
    if case.target == "fit":
        return "requires_requirement_extraction"
    if case.target == "protocol":
        return "protocol_case"
    if case.checks.sources.mode == "none":
        return "no_source_expectation"
    if len(case.conversation) > 1:
        return "requires_recorded_rewrite"
    return None


def _latency_summary(results: list[CaseResult]) -> LatencySummary:
    values = sorted(
        result.latency_ms for result in results if result.latency_ms is not None
    )

    def percentile(p: float) -> float | None:
        return values[math.ceil(len(values) * p) - 1] if values else None

    return LatencySummary(
        count=len(values),
        mean_ms=statistics.fmean(values) if values else None,
        p50_ms=percentile(0.5),
        p95_ms=percentile(0.95),
        p99_ms=percentile(0.99),
    )


async def evaluate_suite(
    cases: list[EvalCase],
    retriever: Retriever,
    *,
    clock: Callable[[], float] = time.perf_counter,
    warmup: bool = True,
    require_all_hit5: bool = False,
) -> SuiteReport:
    if any(case.split != "development" for case in cases):
        raise ValueError("This runner does not execute held-out/reserved cases")
    if cases:
        CaseSuite(version="evaluation-input", cases=cases)
    if warmup and any(_skip_reason(case) is None for case in cases):
        try:
            await retriever.retrieve("embedding warm-up", top_k=1)
        except Exception as exc:
            raise RetrievalRunError("Retrieval failed during warm-up") from exc
    results: list[CaseResult] = []
    for case in cases:
        reason = _skip_reason(case)
        if reason is not None:
            results.append(
                CaseResult(id=case.id, category=case.category, skip_reason=reason)
            )
            continue
        try:
            start = clock()
            chunks = await retriever.retrieve(case.conversation[-1].content, top_k=5)
            elapsed = (clock() - start) * 1000
            ids = [chunk.chunk.id for chunk in chunks]
            results.append(
                CaseResult(
                    id=case.id,
                    category=case.category,
                    retrieved_ids=ids,
                    scores=score_ranking(ids, case.checks.sources),
                    latency_ms=elapsed,
                )
            )
        except Exception as exc:
            raise RetrievalRunError(f"Retrieval failed for {case.id}") from exc
    metrics = summarize_scores([r.scores for r in results if r.scores is not None])
    thresholds = {"hit_at_3": 0.90, "mrr_at_5": 0.80}
    if require_all_hit5:
        thresholds["hit_at_5"] = 1.0
    failed = [
        name
        for name, threshold in thresholds.items()
        if getattr(metrics, name).value is None
        or getattr(metrics, name).value < threshold
    ]
    categories: dict[str, CategoryMetrics] = {}
    for category in sorted({case.category for case in cases}):
        selected = [r for r in results if r.category == category]
        summary = summarize_scores([r.scores for r in selected if r.scores is not None])
        categories[category] = CategoryMetrics(
            total_cases=len(selected),
            excluded_cases=sum(r.scores is None for r in selected),
            **summary.model_dump(),
        )
    return SuiteReport(
        total_cases=len(results),
        evaluated_cases=metrics.hit_at_3.denominator,
        excluded_cases=sum(r.scores is None for r in results),
        metrics=metrics,
        by_category=categories,
        cases=results,
        latency=_latency_summary(results),
        quality_passed=not failed,
        failed_quality_checks=failed,
        thresholds=thresholds,
    )


class RunProvenance(MetricModel):
    created_at: datetime
    commit: str
    dirty: bool
    retrieval_source_sha256: Sha256
    dataset_manifest_sha256: Sha256
    corpus_sha256: Sha256
    index_artifact_sha256: Sha256
    embedding_model: str
    draft_chunks: int
    rrf_k: Literal[60] = 60
    candidates_multiplier: Literal[4] = 4
    python_version: str
    library_versions: dict[str, str]


class LatencyGate(MetricModel):
    max_mean_ms: float = Field(gt=0)
    passed: bool
    failed_suites: list[str]


class OfflineRetrievalReport(MetricModel):
    schema_version: Literal[1] = 1
    kind: Literal["offline_retrieval_diagnostic"] = "offline_retrieval_diagnostic"
    retriever: Literal["local_hybrid_rrf", "injected_test_double"] = "local_hybrid_rrf"
    label_status: Literal["provisional"] = "provisional"
    held_out_executed: Literal[False] = False
    groq_calls: Literal[0] = 0
    provenance: RunProvenance
    suites: dict[str, SuiteReport]
    latency_gate: LatencyGate | None = None


async def build_report(selection: str) -> OfflineRetrievalReport:
    from app.retrieval.dense import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDINGS_PATH
    from app.retrieval.hybrid import HybridRetriever
    from app.retrieval.loader import FactLoader

    if selection not in {"all", "legacy", "development"}:
        raise ValueError("Unknown retrieval suite selection")
    verified = verify_dataset()
    manifest = load_manifest()
    facts = FactLoader().load_all()
    index = IndexSnapshot.model_validate_json(
        (DEFAULT_ROOT / "manifests/index-v1.json").read_text(encoding="utf-8")
    )
    source_paths = [
        DEFAULT_ROOT / name
        for name in ("run.py", "metrics.py", "schemas.py", "dataset.py")
    ]
    source_paths.extend(sorted((REPO_ROOT / "backend/app/retrieval").glob("*.py")))
    provenance = RunProvenance(
        created_at=datetime.now(UTC),
        commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip(),
        dirty=bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True
            ).strip()
        ),
        retrieval_source_sha256=canonical_sha256(
            {
                p.relative_to(REPO_ROOT).as_posix(): p.read_text(encoding="utf-8")
                for p in source_paths
            }
        ),
        dataset_manifest_sha256=canonical_sha256(manifest.model_dump(mode="json")),
        corpus_sha256=index.manifest.corpus_sha256,
        index_artifact_sha256=file_sha256(DEFAULT_EMBEDDINGS_PATH),
        embedding_model=DEFAULT_EMBEDDING_MODEL,
        draft_chunks=verified["draft_chunks"],
        python_version=sys.version.split()[0],
        library_versions={
            name: version(name) for name in ("pydantic", "numpy", "fastembed", "PyYAML")
        },
    )
    retriever = HybridRetriever(chunks=facts, rrf_k=60, candidates_multiplier=4)
    suites: dict[str, SuiteReport] = {}
    for name, cases in (
        (
            "legacy_development",
            load_legacy_cases() if selection in {"all", "legacy"} else [],
        ),
        (
            "versioned_development",
            load_cases() if selection in {"all", "development"} else [],
        ),
    ):
        if not cases:
            continue
        validate_source_ids(cases, {fact.id for fact in facts})
        suites[name] = await evaluate_suite(
            cases, retriever, require_all_hit5=name == "legacy_development"
        )
    return OfflineRetrievalReport(provenance=provenance, suites=suites)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full", action="store_true", help="Retrieval + replay + CI gate"
    )
    parser.add_argument("--baseline", type=Path, default=DEFAULT_ROOT / "baseline.json")
    parser.add_argument(
        "--suite", choices=("all", "legacy", "development"), default="all"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional complete diagnostic JSON; no public badge is updated",
    )
    parser.add_argument(
        "--max-mean-ms",
        type=float,
        help="Optional machine-specific latency ceiling; never a default quality gate",
    )
    args = parser.parse_args(argv)
    if args.full:
        from evals.results import run_full

        try:
            return asyncio.run(
                run_full(args.output or DEFAULT_ROOT / "results.json", args.baseline)
            )
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            print(f"Offline suite unavailable: {exc}", file=sys.stderr)
            return 2
    if args.max_mean_ms is not None and (
        not math.isfinite(args.max_mean_ms) or args.max_mean_ms <= 0
    ):
        parser.error("--max-mean-ms must be finite and positive")
    try:
        report = asyncio.run(build_report(args.suite))
    except (RetrievalRunError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"Retrieval evaluation failed; no result written: {exc}", file=sys.stderr)
        return 2
    if args.max_mean_ms is not None:
        failed = [
            name
            for name, suite in report.suites.items()
            if suite.latency.mean_ms is None or suite.latency.mean_ms > args.max_mean_ms
        ]
        report = report.model_copy(
            update={
                "latency_gate": LatencyGate(
                    max_mean_ms=args.max_mean_ms,
                    passed=bool(report.suites) and not failed,
                    failed_suites=failed,
                )
            }
        )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(".json.tmp")
        temporary.write_text(
            report.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        temporary.replace(args.output)
    summary = report.model_dump(
        mode="json", exclude={"suites": {name: {"cases"} for name in report.suites}}
    )
    print(json.dumps(summary, indent=2))
    quality_ok = bool(report.suites) and all(
        suite.quality_passed for suite in report.suites.values()
    )
    latency_ok = report.latency_gate is None or report.latency_gate.passed
    return 0 if quality_ok and latency_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
