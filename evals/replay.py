"""Replay saved development output offline; no generator, judge or model loading."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.retrieval.artifacts import (  # noqa: E402
    Sha256,
    canonical_sha256,
    corpus_sha256,
    file_sha256,
)
from app.retrieval.loader import FactLoader  # noqa: E402
from evals.checks import (  # noqa: E402
    CaptureBundle,
    CheckResult,
    ReplayModel,
    check_recording,
    prompt_files_fingerprint,
)
from evals.dataset import (  # noqa: E402
    DEFAULT_ROOT,
    REPO_ROOT,
    load_cases,
    load_manifest,
    verify_dataset,
)

DEFAULT_RECORDINGS = DEFAULT_ROOT / "recordings" / "endpoints-v1.json"


class UnavailableComparison(ReplayModel):
    status: Literal["unavailable"] = "unavailable"
    reason: str = (
        "No comparable authorized live stuffed/RAG answer and usage recordings exist."
    )


class ReplayReport(ReplayModel):
    kind: Literal["recorded_checker_diagnostic"] = "recorded_checker_diagnostic"
    generation_accuracy_available: Literal[False] = False
    replayed_at: datetime
    replay_commit: str
    replay_dirty: bool
    checker_sha256: Sha256
    recording_file_sha256: Sha256
    capture_commit: str
    captured_at: datetime
    prompt_matches_current: bool
    groq_calls: Literal[0] = 0
    held_out_executed: Literal[False] = False
    origins: dict[str, int]
    deliveries: dict[str, int]
    recordings_checked: int
    checks_passed: int
    development_cases_without_recordings: list[str]
    semantic_review: Literal["pending"] = "pending"
    baseline_comparison: UnavailableComparison
    results: list[CheckResult]


def load_recordings(path: Path = DEFAULT_RECORDINGS) -> CaptureBundle:
    verify_dataset()
    bundle = CaptureBundle.model_validate_json(path.read_text(encoding="utf-8"))
    facts = FactLoader().load_all()
    if bundle.corpus_sha256 != corpus_sha256(facts):
        raise ValueError(
            "Recording corpus has changed; replay is unavailable for current facts"
        )
    if bundle.dataset_manifest_sha256 != canonical_sha256(
        load_manifest().model_dump(mode="json")
    ):
        raise ValueError("Recording dataset has changed; review case bindings")
    return bundle


def replay_report(path: Path = DEFAULT_RECORDINGS) -> ReplayReport:
    bundle = load_recordings(path)
    cases = {case.id: case for case in load_cases()}
    facts = {fact.id for fact in FactLoader().load_all()}
    results = []
    for record in bundle.records:
        if record.case is not None and record.case.id not in cases:
            raise ValueError("Replay only accepts versioned development cases")
        results.append(
            check_recording(
                record, facts, case=cases[record.case.id] if record.case else None
            )
        )
    covered = {record.case.id for record in bundle.records if record.case}
    return ReplayReport(
        replayed_at=datetime.now(UTC),
        replay_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip(),
        replay_dirty=bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True
            ).strip()
        ),
        checker_sha256=canonical_sha256(
            {
                name: (DEFAULT_ROOT / name).read_text(encoding="utf-8")
                for name in ("checks.py", "replay.py")
            }
        ),
        recording_file_sha256=file_sha256(path),
        capture_commit=bundle.commit,
        captured_at=bundle.captured_at,
        prompt_matches_current=bundle.prompt_files_sha256 == prompt_files_fingerprint(),
        origins=dict(Counter(record.origin for record in bundle.records)),
        deliveries=dict(Counter(record.delivery for record in bundle.records)),
        recordings_checked=len(results),
        checks_passed=sum(result.passed for result in results),
        development_cases_without_recordings=sorted(set(cases) - covered),
        baseline_comparison=UnavailableComparison(),
        results=results,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recordings", type=Path, default=DEFAULT_RECORDINGS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = replay_report(args.recordings)
    except (ValueError, OSError) as exc:
        print(f"Replay unavailable; no result written: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(".json.tmp")
        temporary.write_text(
            report.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        temporary.replace(args.output)
    print(report.model_dump_json(indent=2))
    return 0 if report.checks_passed == report.recordings_checked else 1


if __name__ == "__main__":
    raise SystemExit(main())
