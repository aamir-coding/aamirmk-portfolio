# ruff: noqa: E402
"""Build the redacted public projection offline; never edits result scores."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


from app.eval_summary import (
    CategoryCount,
    Count,
    JudgeValidation,
    PublicArtifact,
    PublicReport,
    RetrievalMetric,
    runtime_fingerprint,
)
from app.retrieval.artifacts import canonical_sha256
from evals.calibration import AnnotationSet, JudgeSet, agreement_report, load_packet
from evals.dataset import load_cases
from evals.replay import load_recordings
from evals.results import Baseline, OfflineResult, gate, input_fingerprints, write_json

# Establish root CLI imports before importing backend models.
from evals.run import DEFAULT_ROOT

VALIDATION = DEFAULT_ROOT / "annotations/runs/validation-2026-11-05-axis-independent"


def project(result: OfflineResult) -> PublicArtifact:
    baseline = Baseline.model_validate_json(
        (DEFAULT_ROOT / "baseline.json").read_text(encoding="utf-8")
    )
    # Gate failures are preserved; incompatible inputs cannot be published as current.
    failures = gate(result, baseline)
    if any(f.startswith("incompatible") for f in failures):
        raise ValueError("Incompatible artifact/baseline")
    if any(result.fingerprints[k] != v for k, v in input_fingerprints().items()):
        raise ValueError("Stale result inputs")
    packet = load_packet()
    human = AnnotationSet.model_validate_json(
        (DEFAULT_ROOT / "annotations/human-v1-aamir-2026-11-05.json").read_text(
            encoding="utf-8"
        )
    )
    judge = JudgeSet.model_validate_json(
        (VALIDATION / "judge.json").read_text(encoding="utf-8")
    )
    agreement = agreement_report(packet, human, judge)
    if agreement.status not in {"passed", "failed"}:
        raise ValueError("Independent judge validation is incomplete")
    records = load_recordings()
    cases = {c.id: c for c in load_cases()}
    category_by_record = {
        r.id: cases[r.case.id].category if r.case else "contract"
        for r in records.records
    }
    totals = Counter(category_by_record.values())
    passes = Counter(
        category_by_record[r.id] for r in result.replay.results if r.passed
    )
    report = PublicReport(
        generated_at=result.generated_at,
        source_commit=result.retrieval.provenance.commit,
        source_dirty=result.retrieval.provenance.dirty,
        source_result_sha256=canonical_sha256(result.model_dump(mode="json")),
        runtime_sha256=runtime_fingerprint(),
        replay=Count(
            passed=result.replay.checks_passed, total=result.replay.recordings_checked
        ),
        categories=[
            CategoryCount(category=k, passed=passes[k], total=v, skipped=0)
            for k, v in sorted(totals.items())
        ],
        retrieval=[
            RetrievalMetric(
                suite=name,
                metric=metric,
                numerator=value.numerator,
                denominator=value.denominator,
            )
            for name, suite in result.retrieval.suites.items()
            for metric, value in suite.metrics
            if metric != "query_mode"
        ],
        failed_checks=failures,
        held_out_reserved=len(result.split_ids["held_out"]),
        draft_chunks=result.retrieval.provenance.draft_chunks,
        development_without_recordings=len(
            result.replay.development_cases_without_recordings
        ),
        judge_validation=JudgeValidation(
            status=agreement.status,
            artifact_sha256=canonical_sha256(agreement.model_dump(mode="json")),
            rubric_sha256=packet.rubric_sha256,
            axes={
                axis: Count(passed=c.numerator, total=c.denominator)
                for axis, c in agreement.per_label.items()
            },
            failures_by_axis={
                axis: c.denominator - c.numerator
                for axis, c in agreement.per_label.items()
            },
            disagreements=[
                {
                    "item_id": row.item_id,
                    "axis": row.axis,
                    "human": row.human,
                    "judge": row.judge,
                }
                for row in agreement.human_overrides
            ],
        ),
    )
    return PublicArtifact(
        report_sha256=canonical_sha256(report.model_dump(mode="json")), report=report
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=DEFAULT_ROOT / "results.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ROOT.parent / "backend/app/data/eval-summary.json",
    )
    args = parser.parse_args()
    result = OfflineResult.model_validate_json(args.result.read_text(encoding="utf-8"))
    write_json(args.output, project(result))
    print(f"Public projection written: {args.output}; model accuracy unavailable")


if __name__ == "__main__":
    main()
