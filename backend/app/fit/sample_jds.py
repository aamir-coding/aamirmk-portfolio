"""Preset sample Job Descriptions for recruiter convenience and CI testing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.fit.golden_benchmarks import GOLDEN_BENCHMARK_REPORTS
from app.fit.models import FitReport


@dataclass(frozen=True, slots=True)
class SampleJobDescription:
    """Metadata and raw text for a curated sample Job Description."""

    id: str
    title: str
    company: str
    match_expectation: str  # "Strong Match", "Partial Match", "Low Match"
    text: str
    report: FitReport | None = None


def _find_sample_jds_dir() -> Path:
    """Resolve sample_jds directory across dev and test environments."""
    candidates = [
        Path(__file__).resolve().parents[3] / "evals" / "sample_jds",
        Path.cwd() / "evals" / "sample_jds",
        Path.cwd().parent / "evals" / "sample_jds",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return candidates[0]


def load_sample_jds() -> list[SampleJobDescription]:
    """Load all curated sample job descriptions from disk.

    Includes pre-evaluated golden reports for 1-click evaluation.
    """
    sample_dir = _find_sample_jds_dir()
    if not sample_dir.is_dir():
        return []

    jds: list[SampleJobDescription] = []
    expectations = {
        "01-fullstack-ai-engineer": "Strong Match",
        "02-backend-python-engineer": "Strong Match",
        "03-genai-application-developer": "Partial Match",
        "04-embedded-firmware-engineer": "Low Match",
    }

    for file_path in sorted(sample_dir.glob("*.txt")):
        stem = file_path.stem
        raw_text = file_path.read_text(encoding="utf-8").strip()

        # Parse basic header fields
        role_match = re.search(r"^Role:\s*(.+)$", raw_text, re.MULTILINE)
        company_match = re.search(r"^Company:\s*(.+)$", raw_text, re.MULTILINE)

        title = role_match.group(1).strip() if role_match else stem
        company = company_match.group(1).strip() if company_match else "Tech Co"
        report = GOLDEN_BENCHMARK_REPORTS.get(stem)
        expectation = (
            report.score.overall_fit
            if report is not None
            else expectations.get(stem, "Partial Match")
        )

        jds.append(
            SampleJobDescription(
                id=stem,
                title=title,
                company=company,
                match_expectation=expectation,
                text=raw_text,
                report=report,
            )
        )

    return jds
