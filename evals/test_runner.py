"""Runner tests use injected retrievers and clocks, without ONNX/Groq calls."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from app.retrieval.models import FactChunk, RetrievedChunk
from app.retrieval.retriever import FakeRetriever
from evals.run import (
    OfflineRetrievalReport,
    RetrievalRunError,
    RunProvenance,
    evaluate_suite,
    load_legacy_cases,
    main,
)
from evals.schemas import EvalCase


def make_case(cid: str = "one", **updates: Any) -> EvalCase:
    payload = {
        "id": cid,
        "version": 1,
        "group_id": cid,
        "split": "development",
        "category": "factual",
        "target": "chat",
        "origin": {"kind": "authored", "reference": "Synthetic runner test"},
        "conversation": [{"role": "user", "content": "A self-contained question?"}],
        "checks": {
            "sources": {"mode": "all_relevant", "ids": ["fact-a", "fact-b"]},
            "support_expectations": ["Use only the retrieved facts."],
        },
    }
    payload.update(updates)
    return EvalCase.model_validate(payload)


def fake_with_hit() -> FakeRetriever:
    chunk = FactChunk(id="fact-a", type="skill", title="A", content="Synthetic fact")
    return FakeRetriever(canned_chunks=[RetrievedChunk(chunk=chunk, rank=1, score=1.0)])


@pytest.mark.asyncio
async def test_runner_uses_injected_clock_and_real_retriever_interface() -> None:
    fake = fake_with_hit()
    ticks = iter([2.0, 2.012])
    report = await evaluate_suite(
        [make_case()], fake, clock=lambda: next(ticks), warmup=False
    )
    assert fake.recorded_queries == ["A self-contained question?"]
    assert report.evaluated_cases == 1
    assert report.cases[0].latency_ms == pytest.approx(12)
    assert report.metrics.recall_at_3.value == 0.5
    assert report.metrics.hit_at_3.value == 1
    assert report.by_category["factual"].hit_at_3.denominator == 1
    assert report.quality_passed is True


@pytest.mark.asyncio
async def test_skipped_behaviors_do_not_consume_calls_or_improve_quality() -> None:
    none = make_case(
        "none",
        checks={
            "sources": {"mode": "none"},
            "support_expectations": ["Out of scope"],
        },
    )
    followup = make_case(
        "followup",
        category="follow_up",
        conversation=[
            {"role": "user", "content": "A question?"},
            {"role": "assistant", "content": "A recorded prior answer."},
            {"role": "user", "content": "What about it?"},
        ],
    )
    fit = make_case(
        "fit",
        target="fit",
        category="fit",
        conversation=[
            {
                "role": "user",
                "content": (
                    "We need a backend engineer with Python API design "
                    "and reliable deployment experience."
                ),
            }
        ],
    )
    fake = fake_with_hit()
    report = await evaluate_suite([none, followup, fit], fake, warmup=False)
    assert fake.recorded_queries == []
    assert report.evaluated_cases == 0
    assert report.excluded_cases == 3
    assert {case.skip_reason for case in report.cases} == {
        "no_source_expectation",
        "requires_recorded_rewrite",
        "requires_requirement_extraction",
    }
    assert report.metrics.hit_at_3.value is None
    assert report.quality_passed is False


@pytest.mark.asyncio
async def test_partial_misses_remain_in_category_denominators() -> None:
    class QueryRetriever(FakeRetriever):
        async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
            return (
                []
                if query == "A different question?"
                else await super().retrieve(query, top_k)
            )

    fake = QueryRetriever(canned_chunks=fake_with_hit().canned_chunks)
    other = make_case(
        "two",
        category="technical",
        conversation=[
            {
                "role": "user",
                "content": "A different question?",
            }
        ],
    )
    report = await evaluate_suite([make_case(), other], fake, warmup=False)
    assert report.metrics.hit_at_5.denominator == 2
    assert report.metrics.hit_at_5.value == 0.5
    assert report.by_category["technical"].hit_at_3.value == 0
    assert report.quality_passed is False


@pytest.mark.asyncio
async def test_retriever_failure_is_not_silently_graded_as_a_missing_answer() -> None:
    class FailedRetriever(FakeRetriever):
        async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
            raise RuntimeError("synthetic backend failure")

    with pytest.raises(RetrievalRunError, match="one"):
        await evaluate_suite([make_case()], FailedRetriever(), warmup=False)


@pytest.mark.asyncio
async def test_duplicate_or_held_out_inputs_are_rejected_before_calls() -> None:
    fake = fake_with_hit()
    with pytest.raises(ValueError, match="Duplicate"):
        await evaluate_suite([make_case(), make_case()], fake, warmup=False)
    reserved = make_case().model_copy(update={"split": "held_out"})
    with pytest.raises(ValueError, match="held.out|reserved"):
        await evaluate_suite([reserved], fake, warmup=False)
    assert fake.recorded_queries == []


@pytest.mark.asyncio
async def test_latency_is_reported_separately_from_quality() -> None:
    ticks = iter([2.0, 3.0])
    report = await evaluate_suite(
        [make_case()], fake_with_hit(), clock=lambda: next(ticks), warmup=False
    )
    assert report.quality_passed is True
    assert report.latency.mean_ms == report.latency.p95_ms == 1000


def test_legacy_loader_retains_all_queries_and_deduplicates_source_alternatives() -> (
    None
):
    cases = load_legacy_cases()
    assert len(cases) == 45
    assert {case.split for case in cases} == {"development"}
    assert all(case.checks.sources.mode == "any_of" for case in cases)
    assert len(cases[16].checks.sources.ids) == 1


def test_cli_has_no_held_out_or_live_mode(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(["--held-out", "--output", str(tmp_path / "result.json")])
    assert not (tmp_path / "result.json").exists()


async def fake_report(selection: str) -> OfflineRetrievalReport:
    ticks = iter([0.0, 1.0])
    suite = await evaluate_suite(
        [make_case()], fake_with_hit(), clock=lambda: next(ticks), warmup=False
    )
    provenance = RunProvenance(
        created_at=datetime.now(UTC),
        commit="synthetic-test",
        dirty=True,
        retrieval_source_sha256="0" * 64,
        dataset_manifest_sha256="0" * 64,
        corpus_sha256="0" * 64,
        index_artifact_sha256="0" * 64,
        embedding_model="synthetic-test-model",
        draft_chunks=0,
        python_version="test",
        library_versions={},
    )
    return OfflineRetrievalReport(
        provenance=provenance,
        suites={"synthetic": suite},
        retriever="injected_test_double",
    )


def test_cli_output_roundtrips_and_never_labels_fake_metrics_as_model_accuracy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.run as runner

    monkeypatch.setattr(runner, "build_report", fake_report)
    path = tmp_path / "result.json"
    assert main(["--output", str(path)]) == 0
    report = OfflineRetrievalReport.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    assert report.retriever == "injected_test_double"
    assert report.kind == "offline_retrieval_diagnostic"
    assert report.groq_calls == 0 and report.held_out_executed is False
    assert report.latency_gate is None


def test_optional_latency_gate_is_recorded_without_changing_quality(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.run as runner

    monkeypatch.setattr(runner, "build_report", fake_report)
    path = tmp_path / "result.json"
    assert main(["--output", str(path), "--max-mean-ms", "10"]) == 1
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["latency_gate"]["passed"] is False
    assert report["latency_gate"]["max_mean_ms"] == 10
    assert report["suites"]["synthetic"]["quality_passed"] is True


def test_failed_run_cannot_overwrite_a_previous_complete_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import evals.run as runner

    async def failure(selection: str) -> OfflineRetrievalReport:
        raise RetrievalRunError("synthetic failure")

    monkeypatch.setattr(runner, "build_report", failure)
    path = tmp_path / "result.json"
    path.write_text("prior complete result", encoding="utf-8")
    assert main(["--output", str(path)]) == 2
    assert path.read_text(encoding="utf-8") == "prior complete result"
    assert "no result written" in capsys.readouterr().err


@pytest.mark.parametrize("ceiling", ["0", "-1", "nan", "inf"])
def test_invalid_latency_budget_is_rejected_before_running(ceiling: str) -> None:
    with pytest.raises(SystemExit):
        main(["--max-mean-ms", ceiling])


@pytest.mark.asyncio
async def test_all_legacy_hits_remain_an_explicit_gate() -> None:
    class LateHit(FakeRetriever):
        async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
            if query == "Only this question misses?":
                return []
            return await super().retrieve(query, top_k)

    cases = [
        make_case(
            f"case-{i}",
            conversation=[
                {
                    "role": "user",
                    "content": f"Question number {i}?",
                }
            ],
        )
        for i in range(19)
    ]
    cases.append(
        make_case(
            "miss",
            conversation=[
                {
                    "role": "user",
                    "content": "Only this question misses?",
                }
            ],
        )
    )
    retriever = LateHit(canned_chunks=fake_with_hit().canned_chunks)
    report = await evaluate_suite(cases, retriever, warmup=False, require_all_hit5=True)
    assert report.metrics.hit_at_3.value == 0.95
    assert report.metrics.mrr_at_5.value == 0.95
    assert report.quality_passed is False
    assert report.failed_quality_checks == ["hit_at_5"]
