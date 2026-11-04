"""Generate event fixtures through real routes with fully isolated fake adapters."""

import sys
from pathlib import Path

import pytest

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from evals.capture import capture_contracts  # noqa: E402
from evals.checks import check_recording, decode_recording  # noqa: E402
from evals.replay import load_recordings  # noqa: E402


def test_current_endpoint_captures_match_the_committed_cross_language_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import fastembed

    import app.llm

    def forbidden(**kwargs: object) -> None:
        pytest.fail(
            "Contract capture must never create a real Groq or embedding adapter"
        )

    monkeypatch.setattr(app.llm, "AsyncGroq", forbidden)
    monkeypatch.setattr(fastembed, "TextEmbedding", forbidden)
    actual = capture_contracts()
    saved = load_recordings()
    assert actual.records == saved.records
    assert actual.corpus_sha256 == saved.corpus_sha256
    assert actual.prompt_files_sha256 == saved.prompt_files_sha256


def test_repeat_capture_isolated_from_seeded_and_previous_fit_caches() -> None:
    first = capture_contracts()
    second = capture_contracts()
    assert first.records == second.records
    fresh = next(record for record in first.records if record.id == "fit-fresh")
    cached = next(record for record in first.records if record.id == "fit-cached")
    assert fresh.adapter_complete_calls == 3
    assert cached.adapter_complete_calls == 0
    assert not decode_recording(fresh).cache_hit
    assert decode_recording(cached).cache_hit


def test_saved_captures_pass_limited_checks_and_expose_unavailable_guarantees() -> None:
    from app.retrieval.loader import FactLoader
    from evals.dataset import load_cases

    facts = {fact.id for fact in FactLoader().load_all()}
    cases = {case.id: case for case in load_cases()}
    for record in load_recordings().records:
        case = cases[record.case.id] if record.case else None
        result = check_recording(record, facts, case=case)
        assert result.passed, (record.id, result.failed_checks)
        assert result.semantic_review == "pending"
        if record.origin == "curated":
            assert "requirement_local_evidence" in result.unavailable_checks
        if record.delivery == "cached":
            report = decode_recording(record).fit_report
            assert report is not None
            assert ("server_cached_flag_unreliable" in result.warnings) == (
                not report.cached
            )
