"""Offline evidence integrity checks for the curated fit snapshots."""

from app.fit.golden_benchmarks import GOLDEN_BENCHMARK_REPORTS
from app.fit.scorer import compute_fit_summary
from app.retrieval.loader import FactLoader


def test_golden_citations_exist_in_current_public_corpus() -> None:
    ids = {chunk.id for chunk in FactLoader().load_all()}
    for report in GOLDEN_BENCHMARK_REPORTS.values():
        for item in report.requirements:
            assert set(item.evidence_chunk_ids) <= ids
            if item.verdict != "gap":
                assert item.evidence_chunk_ids


def test_golden_scores_are_computed_from_verdicts() -> None:
    for report in GOLDEN_BENCHMARK_REPORTS.values():
        assert report.score == compute_fit_summary(report.requirements)


def test_golden_gaps_do_not_claim_unestablished_active_training() -> None:
    for report in GOLDEN_BENCHMARK_REPORTS.values():
        for item in report.requirements:
            if item.verdict == "gap":
                text = f"{item.explanation} {item.ramp_up}".lower()
                assert "actively" not in text
                assert "cka" not in text
                assert "kind/k3s" not in text
