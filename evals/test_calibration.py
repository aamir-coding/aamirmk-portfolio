"""Human review stays independent of authored samples and fake judges."""

from pathlib import Path

import pytest

from evals.calibration import (
    AnnotationSet,
    JudgeConfiguration,
    JudgeSet,
    Labels,
    Review,
    agreement_report,
    effective_judge_prompt_sha256,
    load_packet,
    packet_fingerprint,
    validate_reviews,
)


def test_frozen_packet_is_development_only_group_disjoint_and_ungraded() -> None:
    packet = load_packet()
    assert len([x for x in packet.items if x.slice == "calibration"]) >= 20
    assert len([x for x in packet.items if x.slice == "validation"]) >= 8
    groups = {
        s: {x.group_id for x in packet.items if x.slice == s}
        for s in ("calibration", "validation")
    }
    assert not groups["calibration"] & groups["validation"]
    assert any(x.category == "fit" for x in packet.items if x.slice == "calibration")
    assert all(x.origin == "authored_calibration_example" for x in packet.items)
    template = AnnotationSet.model_validate_json(
        Path("evals/annotations/human-v1.template.json").read_text()
    )
    validate_reviews(packet, template)
    assert all(x.labels is None for x in template.reviews)
    assert agreement_report(packet, template, None).status == "pending"


def reviews(*, judge: bool = False, wrong: bool = False) -> AnnotationSet | JudgeSet:
    packet = load_packet()
    rows = [
        Review(
            item_id=x.id,
            item_sha256=x.sha256,
            labels=Labels(
                support="fail" if i % 2 else "pass",
                completeness="fail" if i % 2 else "pass",
                behavior="fail" if i % 2 else "pass",
                tone="fail" if i % 2 else "pass",
            ),
            rationale="Synthetic test grade, never human evidence.",
        )
        for i, x in enumerate(packet.items)
    ]
    if wrong:
        rows = [
            row.model_copy(
                update={
                    "labels": Labels(
                        support="uncertain",
                        completeness="fail",
                        behavior="fail",
                        tone="fail",
                    )
                }
            )
            for row in rows
        ]
    fields = {
        "packet_sha256": packet_fingerprint(packet),
        "rubric_sha256": packet.rubric_sha256,
        "reviews": rows,
    }
    if judge:
        return JudgeSet(
            **fields,
            origin="fake",
            model="fake",
            prompt_sha256=packet.judge_prompt_sha256,
            effective_prompt_sha256=effective_judge_prompt_sha256(),
            configuration=JudgeConfiguration(max_completion_tokens=512),
        )
    return AnnotationSet(
        **fields, reviewer="test-only reviewer", attestation="test-only"
    )


def test_fake_agreement_never_calibrates_a_live_judge() -> None:
    packet = load_packet()
    report = agreement_report(packet, reviews(), reviews(judge=True))
    assert report.status == "diagnostic_only"
    assert report.agreement_floor_met
    assert not report.live_judge_calibrated
    assert not report.generation_accuracy_available
    assert all(x.numerator == x.denominator == 8 for x in report.per_label.values())


def test_legacy_judge_result_cannot_guess_unrecorded_settings() -> None:
    data = reviews(judge=True).model_dump(mode="json")
    del data["configuration"]
    with pytest.raises(ValueError):
        JudgeSet.model_validate(data)


def test_uncertain_judge_counts_as_disagreement_and_humans_override() -> None:
    report = agreement_report(load_packet(), reviews(), reviews(judge=True, wrong=True))
    assert not report.agreement_floor_met
    assert report.per_label["support"].numerator == 0
    assert report.per_label["support"].denominator == 8
    assert report.human_overrides
    assert report.per_label["support"].confusion["pass/uncertain"] == 4


@pytest.mark.parametrize(
    "change",
    ["item_hash", "packet_hash", "rubric_hash", "duplicate", "unknown", "reviewer"],
)
def test_stale_or_unattributed_human_grades_fail_closed(change: str) -> None:
    packet = load_packet()
    data = reviews().model_dump(mode="json")
    if change == "item_hash":
        data["reviews"][0]["item_sha256"] = "0" * 64
    if change == "packet_hash":
        data["packet_sha256"] = "0" * 64
    if change == "rubric_hash":
        data["rubric_sha256"] = "0" * 64
    if change == "duplicate":
        data["reviews"].append(data["reviews"][0])
    if change == "unknown":
        data["reviews"][0]["item_id"] = "unknown"
    if change == "reviewer":
        data["reviewer"] = None
    with pytest.raises(ValueError):
        validate_reviews(packet, AnnotationSet.model_validate(data))


def test_validation_is_not_reported_without_twenty_calibration_grades() -> None:
    packet = load_packet()
    human = reviews()
    human = human.model_copy(
        update={
            "reviews": [
                r
                for r in human.reviews
                if next(x for x in packet.items if x.id == r.item_id).slice
                == "validation"
            ]
        }
    )
    report = agreement_report(packet, human, reviews(judge=True))
    assert report.status == "pending"
    assert report.per_label == {}


def test_human_abstention_is_excluded_and_coverage_remains_visible() -> None:
    packet = load_packet()
    human = reviews()
    val = next(x for x in packet.items if x.slice == "validation")
    human = human.model_copy(
        update={
            "reviews": [
                r.model_copy(
                    update={
                        "labels": Labels(
                            support="uncertain",
                            completeness="uncertain",
                            behavior="uncertain",
                            tone="uncertain",
                        )
                    }
                )
                if r.item_id == val.id
                else r
                for r in human.reviews
            ]
        }
    )
    report = agreement_report(packet, human, reviews(judge=True))
    assert report.per_label["support"].denominator == 7
    assert report.per_label["support"].human_abstentions == 1
    assert not report.live_judge_calibrated


def test_validation_only_judge_cannot_claim_calibrated_without_calibration_slice() -> (
    None
):
    packet = load_packet()
    judged = reviews(judge=True)
    val_ids = {x.id for x in packet.items if x.slice == "validation"}
    judged = judged.model_copy(
        update={
            "origin": "live",
            "model": "openai/gpt-oss-20b",
            "authorization_reference": "TEST ONLY",
            "ledger_sha256": "0" * 64,
            "reviews": [r for r in judged.reviews if r.item_id in val_ids],
        }
    )
    report = agreement_report(packet, reviews(), judged)
    assert not report.live_judge_calibrated
    assert report.status == "pending"


def test_authored_packet_builder_still_matches_immutable_frozen_examples() -> None:
    from evals.prepare_grading import build_packet

    assert build_packet() == load_packet()


def test_compact_judge_prompt_keeps_all_evidence_and_fits_recorded_limit_policy() -> (
    None
):
    import json

    from evals.budget import input_reservation_bound, request_payload
    from evals.live import judge_messages, judge_response_format

    packet = load_packet()
    bounds = []
    for item in packet.items:
        messages = judge_messages(packet, item.id)
        data = json.loads(messages[1].content)
        assert data["answer"] == item.answer
        assert data["evidence"] == [e.model_dump() for e in item.evidence]
        assert "labels" not in data
        bounds.append(
            input_reservation_bound(
                request_payload(messages, response_format=judge_response_format())
            )
        )
    assert max(bounds) <= 6976
    # Feasibility arithmetic, not a proposed or authorized run budget.
    assert 6976 + 1024 <= 8000
    assert 20 * (6976 + 1024) == 160000
    assert 20 * (6976 + 1024) + 25951 <= 200000


def test_changed_effective_prompt_invalidates_prior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.calibration as calibration

    packet, judged = load_packet(), reviews(judge=True)
    original = calibration.judge_system_prompt()
    monkeypatch.setattr(
        calibration, "judge_system_prompt", lambda: original + "changed recipe"
    )
    with pytest.raises(ValueError, match="Judge prompt changed"):
        validate_reviews(packet, judged)


def test_changed_wire_schema_invalidates_prior(monkeypatch: pytest.MonkeyPatch) -> None:
    import evals.calibration as calibration

    packet, judged = load_packet(), reviews(judge=True)
    original = calibration.judge_response_format()
    changed = {
        **original,
        "json_schema": {**original["json_schema"], "name": "changed"},
    }
    monkeypatch.setattr(calibration, "judge_response_format", lambda: changed)
    with pytest.raises(ValueError, match="Judge prompt changed"):
        validate_reviews(packet, judged)


def test_runtime_prefix_change_invalidates_judge(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import evals.calibration as calibration

    packet, judged = load_packet(), reviews(judge=True)
    changed = tmp_path / "runtime-prefix.txt"
    changed.write_text("Different runtime instructions.", encoding="utf-8")
    monkeypatch.setattr(calibration, "JUDGE_RUNTIME_PROMPT", changed)
    assert load_packet() == packet
    with pytest.raises(ValueError, match="Judge prompt changed"):
        validate_reviews(packet, judged)
