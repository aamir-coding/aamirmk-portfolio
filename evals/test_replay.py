"""Replay rejects bad saved output without calling a generator or judge."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from evals.checks import Recording, ReplayChecks, check_recording
from evals.schemas import EvalCase


def chat_recording(text: str = "Aamir built Entropy-OJ.") -> Recording:
    frames = [
        (
            "sources",
            {
                "sources": [
                    {"chunk_id": "project", "title": "Project", "type": "project"}
                ]
            },
        ),
        ("token", {"token": text}),
        (
            "done",
            {
                "conversation_id": "replay-test",
                "sources": [
                    {"chunk_id": "project", "title": "Project", "type": "project"}
                ],
                "cards": [],
            },
        ),
    ]
    raw = "".join(
        f"event: {event}\ndata: {json.dumps(data)}\n\n" for event, data in frames
    )
    return Recording(
        id="synthetic-chat",
        transport="chat_sse",
        origin="fake",
        delivery="fresh",
        model="fake-model",
        raw_sse=raw,
        retrieved_chat_ids=["project"],
        checks=ReplayChecks(
            must_include=["Entropy-OJ"],
            must_not_include=["Google employee"],
            max_chars=100,
        ),
    )


def fit_recording() -> Recording:
    from app.fit.models import FitReport, JudgedRequirement, Requirement
    from app.fit.scorer import compute_fit_summary

    rows = [
        JudgedRequirement(
            requirement=Requirement(id="python", text="Python APIs"),
            verdict="strong",
            evidence_chunk_ids=["python-fact"],
            explanation="Recorded Python evidence.",
        ),
        JudgedRequirement(
            requirement=Requirement(id="aws", text="Production AWS operations"),
            verdict="gap",
            evidence_chunk_ids=["negative-aws"],
            explanation="No hands-on AWS evidence.",
            ramp_up="Future learning plan only.",
        ),
    ]
    report = FitReport(
        role_title="Synthetic test role",
        jd_hash="a" * 64,
        requirements=rows,
        score=compute_fit_summary(rows),
        summary="Python evidence is present; AWS remains a gap.",
    )
    return Recording(
        id="synthetic-fit",
        transport="fit_sse",
        origin="fake",
        delivery="fresh",
        model="fake-model",
        raw_sse=f"event: complete\ndata: {report.model_dump_json()}\n\n",
        evidence_by_requirement={"python": ["python-fact"], "aws": ["negative-aws"]},
        checks=ReplayChecks(
            must_not_include=["Aamir has production AWS experience"],
            max_chars=2000,
            negative_rules=[
                {
                    "requirement_contains": "AWS",
                    "negative_evidence_ids": ["negative-aws"],
                }
            ],
        ),
    )


def change_fit(
    record: Recording, mutate: Callable[[dict[str, Any]], object]
) -> Recording:
    data = json.loads(record.raw_sse.split("data: ", 1)[1].strip())
    mutate(data)
    return record.model_copy(
        update={"raw_sse": f"event: complete\ndata: {json.dumps(data)}\n\n"}
    )


def test_required_and_forbidden_facts_and_length() -> None:
    assert check_recording(chat_recording(), {"project"}).passed
    missing = check_recording(chat_recording("Aamir built something."), {"project"})
    assert "required_text" in missing.failed_checks
    forbidden = check_recording(
        chat_recording("Entropy-OJ. Aamir is a Google employee."), {"project"}
    )
    assert "forbidden_text" in forbidden.failed_checks
    too_long = check_recording(chat_recording("Entropy-OJ " * 20), {"project"})
    assert "length" in too_long.failed_checks


def test_unknown_and_unretrieved_source_ids_are_rejected() -> None:
    assert (
        "citation_identity"
        in check_recording(chat_recording(), {"other"}).failed_checks
    )
    record = chat_recording().model_copy(update={"retrieved_chat_ids": ["other"]})
    assert (
        "retrieved_membership"
        in check_recording(record, {"project", "other"}).failed_checks
    )


def test_refusal_is_checked_from_output_not_a_recorded_self_label() -> None:
    record = chat_recording("I can only answer questions about Aamir's experience.")
    record = record.model_copy(update={"checks": ReplayChecks(expect_refusal=True)})
    assert check_recording(record, {"project"}).passed
    record = chat_recording("Aamir cannot operate AWS.").model_copy(
        update={"checks": ReplayChecks(expect_refusal=True)}
    )
    assert "refusal" in check_recording(record, {"project"}).failed_checks


def test_requirement_locality_is_not_a_global_citation_union() -> None:
    record = change_fit(
        fit_recording(),
        lambda d: d["requirements"][0].update(evidence_chunk_ids=["negative-aws"]),
    )
    result = check_recording(record, {"python-fact", "negative-aws"})
    assert "requirement_local_evidence" in result.failed_checks


def test_negative_only_local_evidence_cannot_justify_a_positive_verdict() -> None:
    def overclaim(data: dict[str, Any]) -> None:
        from app.fit.models import JudgedRequirement
        from app.fit.scorer import compute_fit_summary

        data["requirements"][1]["verdict"] = "strong"
        data["score"] = compute_fit_summary(
            [JudgedRequirement.model_validate(row) for row in data["requirements"]]
        ).model_dump()

    result = check_recording(
        change_fit(fit_recording(), overclaim), {"python-fact", "negative-aws"}
    )
    assert "negative_evidence" in result.failed_checks
    assert "requirement_local_evidence" not in result.failed_checks


@pytest.mark.parametrize("field", ["summary", "ramp_up"])
def test_summaries_and_ramp_up_are_checked_independently_of_score(field: str) -> None:
    def mutate(data: dict[str, Any]) -> None:
        if field == "summary":
            data[field] = "Aamir has production AWS experience."
        else:
            data["requirements"][1][field] = "Aamir has production AWS experience."

    result = check_recording(
        change_fit(fit_recording(), mutate), {"python-fact", "negative-aws"}
    )
    assert "forbidden_text" in result.failed_checks


def test_score_arithmetic_and_duplicate_requirements_cannot_hide_bad_reports() -> None:
    bad_score = change_fit(
        fit_recording(), lambda d: d["score"].update(must_have_strong=99)
    )
    assert (
        "fit_score"
        in check_recording(bad_score, {"python-fact", "negative-aws"}).failed_checks
    )
    duplicate = change_fit(
        fit_recording(),
        lambda d: d["requirements"][1]["requirement"].update(id="python"),
    )
    assert (
        "requirement_ids"
        in check_recording(duplicate, {"python-fact", "negative-aws"}).failed_checks
    )


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('event: token\ndata: {"token":"partial"}\n\n', "premature_eof"),
        ("event: done\ndata: not JSON\n\n", "malformed_event"),
        ("event: done\ndata: {}\n\n", "malformed_event"),
    ],
)
def test_malformed_or_truncated_streams_fail_unless_expected(
    raw: str, expected: str
) -> None:
    record = chat_recording().model_copy(
        update={"raw_sse": raw, "checks": ReplayChecks()}
    )
    assert "protocol" in check_recording(record, {"project"}).failed_checks
    record = record.model_copy(update={"checks": ReplayChecks(expected_error=expected)})
    result = check_recording(record, {"project"})
    assert result.passed and result.observed_error == expected


def test_stream_events_after_completion_are_rejected() -> None:
    record = chat_recording()
    record = record.model_copy(
        update={"raw_sse": record.raw_sse + 'event: token\ndata: {"token":"late"}\n\n'}
    )
    assert "protocol" in check_recording(record, {"project"}).failed_checks


def test_checks_do_not_claim_to_validate_all_semantic_expectations() -> None:
    result = check_recording(chat_recording(), {"project"})
    assert result.semantic_review == "pending"
    assert result.generation_accuracy_available is False


def bound_record(record: Recording, case_id: str) -> tuple[Recording, EvalCase]:
    from evals.checks import CaseReference
    from evals.dataset import case_fingerprint, load_cases

    case = next(case for case in load_cases() if case.id == case_id)
    return record.model_copy(
        update={
            "case": CaseReference(
                id=case.id, version=case.version, sha256=case_fingerprint(case)
            )
        }
    ), case


def test_recording_cannot_override_frozen_refusal_expectation() -> None:
    record, case = bound_record(chat_recording(), "persona-override")
    record = record.model_copy(update={"checks": ReplayChecks(expect_refusal=False)})
    result = check_recording(record, {"project"}, case=case)
    assert not result.passed
    assert "expectation_conflict" in result.failed_checks


def test_frozen_protocol_expectation_is_used_without_a_record_override() -> None:
    record = chat_recording().model_copy(
        update={
            "raw_sse": 'event: token\ndata: {"token":"partial"}\n\n',
            "checks": ReplayChecks(),
        }
    )
    record, case = bound_record(record, "protocol-premature-eof")
    result = check_recording(record, {"project"}, case=case)
    assert result.passed and result.observed_error == "premature_eof"


def test_expected_application_error_does_not_approve_bad_emitted_citations() -> None:
    record = chat_recording()
    prefix = record.raw_sse[: record.raw_sse.index("event: token")]
    record = record.model_copy(
        update={
            "raw_sse": prefix + 'event: error\ndata: {"detail":"synthetic error"}\n\n',
            "checks": ReplayChecks(expected_error="chat_error"),
        }
    )
    assert (
        "citation_identity" in check_recording(record, {"different-fact"}).failed_checks
    )


def test_unknown_negative_rule_facts_are_not_silently_ignored() -> None:
    record = fit_recording().model_copy(
        update={
            "checks": ReplayChecks(
                negative_rules=[
                    {
                        "requirement_contains": "AWS",
                        "negative_evidence_ids": ["missing-fact"],
                    }
                ]
            )
        }
    )
    assert (
        "rule_configuration"
        in check_recording(record, {"python-fact", "negative-aws"}).failed_checks
    )


def test_expected_error_still_requires_a_valid_case_binding() -> None:
    from evals.checks import CaseReference

    record, case = bound_record(chat_recording(), "protocol-premature-eof")
    record = record.model_copy(
        update={
            "case": CaseReference(id=case.id, version=case.version, sha256="0" * 64),
            "raw_sse": 'event: token\ndata: {"token":"partial"}\n\n',
            "checks": ReplayChecks(expected_error="premature_eof"),
        }
    )
    assert (
        "case_binding" in check_recording(record, {"project"}, case=case).failed_checks
    )


def test_recording_origins_cannot_claim_provider_usage_for_fake_data() -> None:
    from pydantic import ValidationError

    data = chat_recording().model_dump(mode="json")
    data["usage"] = {"source": "provider", "prompt_tokens": 1, "completion_tokens": 1}
    with pytest.raises(ValidationError, match="provider usage"):
        Recording.model_validate(data)


def test_stale_corpus_recordings_are_unavailable_instead_of_silently_regraded(
    tmp_path: Path,
) -> None:
    from evals.replay import DEFAULT_RECORDINGS, load_recordings

    data = json.loads(DEFAULT_RECORDINGS.read_text(encoding="utf-8"))
    data["corpus_sha256"] = "0" * 64
    path = tmp_path / "stale.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="corpus"):
        load_recordings(path)


def test_replay_never_invents_baseline_comparisons_or_full_answer_coverage() -> None:
    from evals.replay import replay_report

    report = replay_report()
    assert report.origins == {"fake": 7, "curated": 1}
    assert report.generation_accuracy_available is False
    assert report.baseline_comparison.status == "unavailable"
    assert len(report.development_cases_without_recordings) == 36
    assert report.held_out_executed is False


def test_failed_replay_leaves_prior_result_and_returns_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import evals.replay as replay

    def stale(path: Path) -> object:
        raise ValueError("synthetic stale corpus")

    monkeypatch.setattr(replay, "replay_report", stale)
    path = tmp_path / "prior.json"
    path.write_text("prior complete result", encoding="utf-8")
    assert replay.main(["--output", str(path)]) == 2
    assert path.read_text(encoding="utf-8") == "prior complete result"
    assert "no result written" in capsys.readouterr().err


@pytest.mark.parametrize("ending", ["eof", "application_error"])
def test_expected_failure_does_not_excuse_bad_emitted_prefix(ending: str) -> None:
    record = chat_recording("Entropy-OJ. Aamir is a Google employee.")
    prefix = record.raw_sse[: record.raw_sse.index("event: done")]
    if ending == "eof":
        record, case = bound_record(record, "protocol-premature-eof")
        error = "premature_eof"
    else:
        record, case = bound_record(record, "eval-07-entropy-oj-pitch")
        prefix += 'event: error\ndata: {"detail":"synthetic error"}\n\n'
        error = "chat_error"
    record = record.model_copy(
        update={
            "raw_sse": prefix,
            "checks": ReplayChecks(
                expected_error=error, must_not_include=["Google employee"]
            ),
        }
    )
    result = check_recording(record, {"different-fact"}, case=case)
    assert "forbidden_text" in result.failed_checks
    assert "citation_identity" in result.failed_checks


def test_fit_case_cannot_be_satisfied_with_a_chat_transport_capture() -> None:
    record, case = bound_record(chat_recording(), "fit-cloud-negative")
    record = record.model_copy(
        update={
            "raw_sse": record.raw_sse.replace('"project"', '"skill-not-claimed"'),
            "retrieved_chat_ids": ["skill-not-claimed", "skill-ramp-up-narratives"],
        }
    )
    result = check_recording(
        record, {"skill-not-claimed", "skill-ramp-up-narratives"}, case=case
    )
    assert "transport_binding" in result.failed_checks


def test_target_binding_is_required_even_for_expected_protocol_failures() -> None:
    record, case = bound_record(chat_recording(), "fit-cloud-negative")
    record = record.model_copy(
        update={
            "raw_sse": 'event: token\ndata: {"token":"partial"}\n\n',
            "checks": ReplayChecks(expected_error="premature_eof"),
        }
    )
    assert (
        "transport_binding"
        in check_recording(record, {"project"}, case=case).failed_checks
    )


@pytest.mark.parametrize("failure", ["empty_positive", "negative_only_positive"])
def test_curated_reports_still_enforce_intrinsic_evidence_rules(failure: str) -> None:
    from app.fit.models import FitReport, JudgedRequirement
    from app.fit.scorer import compute_fit_summary
    from evals.checks import decode_recording

    report = decode_recording(fit_recording()).fit_report
    assert report is not None
    data = report.model_dump(mode="json")
    if failure == "empty_positive":
        data["requirements"][0]["evidence_chunk_ids"] = []
    else:
        data["requirements"][1]["verdict"] = "strong"
    data["score"] = compute_fit_summary(
        [JudgedRequirement.model_validate(row) for row in data["requirements"]]
    ).model_dump()
    record = Recording(
        id="curated-counterexample",
        origin="curated",
        delivery="preset",
        transport="preset_json",
        preset_report=FitReport.model_validate(data),
        checks=fit_recording().checks,
    )
    result = check_recording(record, {"python-fact", "negative-aws"})
    assert "requirement_local_evidence" in result.unavailable_checks
    assert (
        "positive_evidence" if failure == "empty_positive" else "negative_evidence"
    ) in result.failed_checks
