"""Reproducible offline artifact and compatible regression gate. No provider calls."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from app.retrieval.artifacts import Sha256, canonical_sha256, corpus_sha256, file_sha256
from app.retrieval.dense import DEFAULT_EMBEDDINGS_PATH
from app.retrieval.loader import FactLoader
from evals.dataset import DEFAULT_ROOT, REPO_ROOT, load_manifest
from evals.metrics import MetricModel, summarize_scores
from evals.replay import ReplayReport, replay_report
from evals.run import OfflineRetrievalReport, build_report


class OfflineResult(MetricModel):
    schema_version: Literal[1] = 1
    kind: Literal["offline_engineering_checks"] = "offline_engineering_checks"
    generated_at: datetime
    generation_accuracy_available: Literal[False] = False
    configured_models: dict[str, str] = {
        "generator": "openai/gpt-oss-120b",
        "judge": "openai/gpt-oss-20b",
    }
    generation_settings: Literal["not_executed"] = "not_executed"
    reported_models: list[str] = []
    provider_calls: Literal[0] = 0
    provider_tokens: Literal[0] = 0
    runtime: dict[str, str]
    fingerprints: dict[str, Sha256]
    split_ids: dict[str, list[str]]
    retrieval: OfflineRetrievalReport
    replay: ReplayReport

    @model_validator(mode="after")
    def coherent(self) -> OfflineResult:
        if set(self.retrieval.suites) != {
            "legacy_development",
            "versioned_development",
        }:
            raise ValueError("Both retrieval suites are required")
        if self.retrieval.retriever != "local_hybrid_rrf":
            raise ValueError("Artifact requires actual local retrieval")
        for suite in self.retrieval.suites.values():
            scored = [c.scores for c in suite.cases if c.scores is not None]
            if (
                suite.total_cases != len(suite.cases)
                or suite.evaluated_cases != len(scored)
                or suite.excluded_cases != len(suite.cases) - len(scored)
                or suite.metrics != summarize_scores(scored)
                or len({c.id for c in suite.cases}) != len(suite.cases)
            ):
                raise ValueError("Retrieval counts/metrics differ from case outcomes")
        if not self.replay.results or len({r.id for r in self.replay.results}) != len(
            self.replay.results
        ):
            raise ValueError("Replay requires unique, nonempty results")
        if any(r.passed != (not r.failed_checks) for r in self.replay.results):
            raise ValueError("Replay status differs from failed checks")
        if self.replay.recordings_checked != len(self.replay.results) or (
            self.replay.checks_passed != sum(r.passed for r in self.replay.results)
        ):
            raise ValueError("Replay counts differ from individual results")
        if set(self.split_ids) != {"development", "held_out"} or (
            set(self.split_ids["development"]) & set(self.split_ids["held_out"])
        ):
            raise ValueError("Invalid split IDs")
        if not self.replay.prompt_matches_current:
            raise ValueError(
                "Recordings use a different prompt; recapture/review required"
            )
        return self

    def scores(self) -> dict[str, float]:
        scores = {"replay": self.replay.checks_passed / self.replay.recordings_checked}
        for name, suite in self.retrieval.suites.items():
            for metric in ("hit_at_3", "hit_at_5", "mrr_at_5"):
                value = getattr(suite.metrics, metric).value
                if value is None:
                    raise ValueError("Missing retrieval metric")
                scores[f"{name}.{metric}"] = value
        return scores


def input_fingerprints() -> dict[str, str]:
    """Text hashes are portable across Windows/Linux newline checkout modes."""
    groups = {
        "prompts": list((REPO_ROOT / "backend/app/prompts").glob("*.txt")),
        "checker": [DEFAULT_ROOT / n for n in ("checks.py", "replay.py")],
        "rubric": sorted((DEFAULT_ROOT / "rubrics").glob("*.*")),
        "recordings": sorted((DEFAULT_ROOT / "recordings").glob("*.json")),
        "evaluator": [
            p
            for p in sorted(DEFAULT_ROOT.glob("*.py"))
            if not p.name.startswith("test")
        ],
        "application": sorted((REPO_ROOT / "backend/app").rglob("*.py")),
        "cases": sorted((DEFAULT_ROOT / "cases").glob("*.yaml")),
        "safety_assets": [
            *sorted((DEFAULT_ROOT / "attacks").glob("*.json")),
            REPO_ROOT / "backend/app/fit/curated-provenance.json",
            REPO_ROOT / "backend/logging.json",
        ],
    }
    fingerprints = {
        name: canonical_sha256(
            {
                p.relative_to(REPO_ROOT).as_posix(): p.read_text(encoding="utf-8")
                for p in paths
            }
        )
        for name, paths in groups.items()
    }
    fingerprints.update(
        corpus=corpus_sha256(FactLoader().load_all()),
        index=file_sha256(DEFAULT_EMBEDDINGS_PATH),
        dataset=canonical_sha256(load_manifest().model_dump(mode="json")),
        dependencies=canonical_sha256(
            {
                name: version(name)
                for name in (
                    "fastembed",
                    "numpy",
                    "pydantic",
                    "groq",
                    "fastapi",
                    "starlette",
                    "httpx",
                )
            }
        ),
    )
    return fingerprints


async def offline_result() -> OfflineResult:
    retrieval = await build_report("all")
    # Keep historical v1/v2 replay inputs frozen; the current safety contract is v3.
    replay = replay_report(DEFAULT_ROOT / "recordings/endpoints-v3-safety.json")
    manifest = load_manifest()
    fingerprints = input_fingerprints()
    fingerprints.update(
        {
            "corpus": retrieval.provenance.corpus_sha256,
            "index": retrieval.provenance.index_artifact_sha256,
            "dataset": retrieval.provenance.dataset_manifest_sha256,
            "retrieval": retrieval.provenance.retrieval_source_sha256,
        }
    )
    return OfflineResult(
        generated_at=datetime.now(UTC),
        runtime={
            "python": sys.version.split()[0],
            **{n: version(n) for n in ("pydantic", "fastembed", "numpy", "groq")},
        },
        fingerprints=fingerprints,
        split_ids={
            split: [c.id for c in manifest.cases if c.split == split]
            for split in ("development", "held_out")
        },
        retrieval=retrieval,
        replay=replay,
    )


class Baseline(MetricModel):
    schema_version: Literal[1] = 1
    review_reference: str = Field(min_length=1)
    fingerprints: dict[str, Sha256]
    scores: dict[str, float] = Field(min_length=1)


def gate(result: OfflineResult, baseline: Baseline) -> list[str]:
    failures = []
    if result.fingerprints != baseline.fingerprints:
        failures.append("incompatible_baseline: review changed inputs before updating")
    scores = result.scores()
    if set(scores) != set(baseline.scores):
        failures.append("incompatible_metric_set")
    for key, value in scores.items():
        if key in baseline.scores and value + 0.020000000001 < baseline.scores[key]:
            failures.append(f"regression:{key}")
    for name, suite in result.retrieval.suites.items():
        if not suite.quality_passed:
            failures.append(f"retrieval_quality:{name}")
    # Every saved contract/evidence regression is critical, regardless of average.
    failures.extend(f"critical:{r.id}" for r in result.replay.results if not r.passed)
    return failures


def write_json(path: Path, document: MetricModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(document.model_dump_json(indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


async def run_full(output: Path, baseline_path: Path) -> int:
    result = await offline_result()
    baseline = Baseline.model_validate_json(baseline_path.read_text(encoding="utf-8"))
    failures = gate(result, baseline)
    write_json(output, result)
    print(
        {
            "scores": result.scores(),
            "gate_failures": failures,
            "artifact": str(output),
            "held_out": "reserved, not executed",
        }
    )
    return int(bool(failures))
