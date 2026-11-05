"""Frozen development grading inputs and transparent judge/human agreement."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Literal, Self

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from pydantic import Field, model_validator  # noqa: E402

from app.retrieval.artifacts import (  # noqa: E402
    Sha256,
    canonical_sha256,
    corpus_sha256,
)
from app.retrieval.loader import FactLoader  # noqa: E402
from evals.checks import CaseReference, ReplayModel  # noqa: E402
from evals.dataset import (  # noqa: E402
    DEFAULT_ROOT,
    case_fingerprint,
    load_cases,
    verify_dataset,
)
from evals.schemas import Text  # noqa: E402

AXES = ("support", "completeness", "behavior", "tone")
DEFAULT_PACKET = DEFAULT_ROOT / "annotations/packet-v1.json"
RUBRIC = DEFAULT_ROOT / "rubrics/support-v1.md"
JUDGE_PROMPT = DEFAULT_ROOT / "rubrics/judge-v1.txt"
JUDGE_RUNTIME_PROMPT = DEFAULT_ROOT / "rubrics/judge-v4.txt"


def text_sha(path: Path) -> str:
    return canonical_sha256(path.read_text(encoding="utf-8"))


def judge_system_prompt() -> str:
    rubric = RUBRIC.read_text(encoding="utf-8")
    definitions = []
    # Runtime v4 defines behavior/tone explicitly; keep the other frozen rubric
    # definitions verbatim without duplicating those runtime instructions.
    for axis in ("support", "completeness"):
        paragraph = rubric.split(f"- **{axis}**:", 1)[1].split("\n- **", 1)[0]
        sentence = " ".join(paragraph.split()).split(". ", 1)[0]
        definitions.append(f"{axis}: {sentence}.")
    # Keep the frozen authoring template intact. This independently versioned
    # runtime prefix retains its constraints and an explicit output shape.
    prefix = " ".join(JUDGE_RUNTIME_PROMPT.read_text(encoding="utf-8").split())
    return prefix + "\n\n" + "\n".join(definitions)


def effective_judge_prompt_sha256() -> str:
    return canonical_sha256(judge_system_prompt())


class Labels(ReplayModel):
    support: Literal["pass", "fail", "uncertain"]
    completeness: Literal["pass", "fail", "uncertain"]
    behavior: Literal["pass", "fail", "uncertain"]
    tone: Literal["pass", "fail", "uncertain"]


class Evidence(ReplayModel):
    id: Text
    content: Text
    draft: bool


class GradingItem(ReplayModel):
    id: Text
    case: CaseReference
    group_id: Text
    category: Text
    slice: Literal["calibration", "validation"]
    origin: Literal["authored_calibration_example"] = "authored_calibration_example"
    answer: Text
    cited_ids: list[Text]
    evidence: list[Evidence]
    requirement_evidence: dict[str, list[Text]] = Field(default_factory=dict)
    sha256: Sha256


def item_fingerprint(item: GradingItem) -> str:
    return canonical_sha256(item.model_dump(mode="json", exclude={"sha256"}))


class GradingPacket(ReplayModel):
    version: Literal[1] = 1
    purpose: Literal["authored_development_judge_calibration"] = (
        "authored_development_judge_calibration"
    )
    corpus_sha256: Sha256
    rubric_sha256: Sha256
    judge_prompt_sha256: Sha256
    minimum_calibration: Literal[20] = 20
    minimum_validation: Literal[8] = 8
    agreement_floor: Literal[0.8] = 0.8
    items: list[GradingItem]


def packet_fingerprint(packet: GradingPacket) -> str:
    return canonical_sha256(packet.model_dump(mode="json"))


def load_packet(path: Path = DEFAULT_PACKET) -> GradingPacket:
    verify_dataset()
    packet = GradingPacket.model_validate_json(path.read_text(encoding="utf-8"))
    lock = path.with_suffix(".lock.json")
    import json

    if json.loads(lock.read_text(encoding="utf-8")) != {
        "packet_sha256": packet_fingerprint(packet)
    }:
        raise ValueError("Grading packet changed; version and review a new packet")
    facts = {f.id: f for f in FactLoader().load_all()}
    cases = {c.id: c for c in load_cases()}
    if (
        packet.corpus_sha256 != corpus_sha256(list(facts.values()))
        or packet.rubric_sha256 != text_sha(RUBRIC)
        or packet.judge_prompt_sha256 != text_sha(JUDGE_PROMPT)
    ):
        raise ValueError(
            "Grading evidence/rubric/prompt changed; calibration unavailable"
        )
    groups: dict[str, str] = {}
    ids: set[str] = set()
    for item in packet.items:
        case = cases.get(item.case.id)
        if (
            case is None
            or case.target == "protocol"
            or item.case.version != case.version
            or item.case.sha256 != case_fingerprint(case)
            or item.group_id != case.group_id
            or item.category != case.category
        ):
            raise ValueError(
                "Grading item must bind to a current development answer case"
            )
        if item.id in ids or item.sha256 != item_fingerprint(item):
            raise ValueError("Duplicate or changed grading item")
        ids.add(item.id)
        if item.group_id in groups and groups[item.group_id] != item.slice:
            raise ValueError("Calibration/validation group leakage")
        groups[item.group_id] = item.slice
        for evidence in item.evidence:
            if (
                evidence.id not in facts
                or evidence.content != facts[evidence.id].content
                or evidence.draft != facts[evidence.id].draft
            ):
                raise ValueError("Evidence snapshot differs from frozen public corpus")
        evidence_ids = {e.id for e in item.evidence}
        if (
            len(evidence_ids) != len(item.evidence)
            or not set(item.cited_ids) <= evidence_ids
            or any(
                not set(v) <= evidence_ids for v in item.requirement_evidence.values()
            )
        ):
            raise ValueError("Invalid grading evidence identity/local map")
    counts = Counter(x.slice for x in packet.items)
    if (
        counts["calibration"] < packet.minimum_calibration
        or counts["validation"] < packet.minimum_validation
    ):
        raise ValueError(
            "Grading packet needs twenty calibration and eight validation answers"
        )
    return packet


class Review(ReplayModel):
    item_id: Text
    item_sha256: Sha256
    labels: Labels | None = None
    rationale: Text | None = None

    @model_validator(mode="after")
    def attributed_labels(self) -> Self:
        if self.labels is not None and not self.rationale:
            raise ValueError("Grades require a rationale")
        return self


class AnnotationSet(ReplayModel):
    packet_sha256: Sha256
    rubric_sha256: Sha256
    reviewer: Text | None = None
    attestation: Text | None = None
    reviews: list[Review]

    @model_validator(mode="after")
    def human_attribution(self) -> Self:
        if any(r.labels is not None for r in self.reviews) and (
            not self.reviewer or not self.attestation
        ):
            raise ValueError(
                "Human labels require named reviewer and explicit attestation"
            )
        return self


class JudgeConfiguration(ReplayModel):
    model: Literal["openai/gpt-oss-20b"] = "openai/gpt-oss-20b"
    temperature: Literal[0.2] = 0.2
    reasoning_effort: Literal["low"] = "low"
    response_format: Literal["json_object"] = "json_object"
    max_completion_tokens: int = Field(gt=0, le=1024, strict=True)


class JudgeSet(ReplayModel):
    packet_sha256: Sha256
    rubric_sha256: Sha256
    prompt_sha256: Sha256
    effective_prompt_sha256: Sha256
    configuration: JudgeConfiguration
    origin: Literal["fake", "live"]
    model: Text
    authorization_reference: Text | None = None
    ledger_sha256: Sha256 | None = None
    reviews: list[Review]

    @model_validator(mode="after")
    def judge_origin(self) -> Self:
        if any(r.labels is None for r in self.reviews):
            raise ValueError("Judge output cannot silently omit a label")
        if self.origin == "live" and (
            self.model != "openai/gpt-oss-20b"
            or not self.authorization_reference
            or not self.ledger_sha256
        ):
            raise ValueError(
                "Live judge output needs fixed model, authorization and attempt ledger"
            )
        return self


def validate_reviews(packet: GradingPacket, reviews: AnnotationSet | JudgeSet) -> None:
    if (
        reviews.packet_sha256 != packet_fingerprint(packet)
        or reviews.rubric_sha256 != packet.rubric_sha256
    ):
        raise ValueError("Grades do not match the frozen packet/rubric")
    if isinstance(reviews, JudgeSet) and (
        reviews.prompt_sha256 != packet.judge_prompt_sha256
        or reviews.effective_prompt_sha256 != effective_judge_prompt_sha256()
    ):
        raise ValueError("Judge prompt changed; validation unavailable")
    items = {x.id: x for x in packet.items}
    seen: set[str] = set()
    for review in reviews.reviews:
        if (
            review.item_id in seen
            or review.item_id not in items
            or review.item_sha256 != items[review.item_id].sha256
        ):
            raise ValueError("Unknown, duplicate or stale review")
        seen.add(review.item_id)


class LabelAgreement(ReplayModel):
    numerator: int
    denominator: int
    human_abstentions: int
    missing_judge: int
    confusion: dict[str, int]
    human_labels: list[str]


class HumanOverride(ReplayModel):
    item_id: str
    axis: str
    human: str
    judge: str
    rationale: str


class AgreementReport(ReplayModel):
    kind: Literal["judge_human_agreement"] = "judge_human_agreement"
    status: Literal["pending", "insufficient", "failed", "passed", "diagnostic_only"]
    packet_sha256: Sha256
    human_sha256: Sha256
    judge_sha256: Sha256 | None
    calibration_graded: int
    validation_graded: int
    calibration_judged: int = 0
    validation_judged: int = 0
    agreement_floor: Literal[0.8] = 0.8
    agreement_floor_met: bool = False
    live_judge_calibrated: bool = False
    generation_accuracy_available: Literal[False] = False
    per_label: dict[str, LabelAgreement] = Field(default_factory=dict)
    human_overrides: list[HumanOverride] = Field(default_factory=list)
    limitation: str = (
        "Authored development examples; not live generator accuracy. "
        "Same-family judge bias remains."
    )


def agreement_report(
    packet: GradingPacket, human: AnnotationSet, judge: JudgeSet | None
) -> AgreementReport:
    validate_reviews(packet, human)
    if judge is not None:
        validate_reviews(packet, judge)
    human_by_id = {r.item_id: r for r in human.reviews if r.labels is not None}
    counts = Counter(x.slice for x in packet.items if x.id in human_by_id)
    judged_ids = {r.item_id for r in judge.reviews} if judge else set()
    judge_counts = Counter(x.slice for x in packet.items if x.id in judged_ids)
    fields = {
        "packet_sha256": packet_fingerprint(packet),
        "human_sha256": canonical_sha256(human.model_dump(mode="json")),
        "judge_sha256": canonical_sha256(judge.model_dump(mode="json"))
        if judge
        else None,
        "calibration_graded": counts["calibration"],
        "validation_graded": counts["validation"],
        "calibration_judged": judge_counts["calibration"],
        "validation_judged": judge_counts["validation"],
    }
    if (
        counts["calibration"] < packet.minimum_calibration
        or counts["validation"] < packet.minimum_validation
        or judge is None
        or judge_counts["calibration"] < packet.minimum_calibration
    ):
        return AgreementReport(status="pending", **fields)
    judged = {r.item_id: r for r in judge.reviews}
    metrics: dict[str, LabelAgreement] = {}
    overrides: list[HumanOverride] = []
    for axis in AXES:
        confusion: Counter[str] = Counter()
        numerator = denominator = abstentions = missing = 0
        human_labels: set[str] = set()
        for item in packet.items:
            if item.slice != "validation":
                continue
            h = human_by_id.get(item.id)
            if h is None or h.labels is None:
                continue
            hlabel = getattr(h.labels, axis)
            if hlabel == "uncertain":
                abstentions += 1
                continue
            human_labels.add(hlabel)
            denominator += 1
            j = judged.get(item.id)
            jlabel = (
                getattr(j.labels, axis)
                if j is not None and j.labels is not None
                else "missing"
            )
            missing += jlabel == "missing"
            confusion[f"{hlabel}/{jlabel}"] += 1
            numerator += hlabel == jlabel
            if hlabel != jlabel:
                overrides.append(
                    HumanOverride(
                        item_id=item.id,
                        axis=axis,
                        human=hlabel,
                        judge=jlabel,
                        rationale=h.rationale or "",
                    )
                )
        metrics[axis] = LabelAgreement(
            numerator=numerator,
            denominator=denominator,
            human_abstentions=abstentions,
            missing_judge=missing,
            confusion=dict(confusion),
            human_labels=sorted(human_labels),
        )
    sufficient = all(
        x.denominator >= packet.minimum_validation
        and x.human_labels == ["fail", "pass"]
        and not x.missing_judge
        for x in metrics.values()
    )
    floor = sufficient and all(
        x.numerator * 5 >= x.denominator * 4 for x in metrics.values()
    )
    status = "insufficient" if not sufficient else "passed" if floor else "failed"
    if judge.origin == "fake":
        status = "diagnostic_only"
    return AgreementReport(
        status=status,
        agreement_floor_met=floor,
        live_judge_calibrated=floor and judge.origin == "live",
        per_label=metrics,
        human_overrides=overrides,
        **fields,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--annotations",
        type=Path,
        default=DEFAULT_ROOT / "annotations/human-v1.template.json",
    )
    parser.add_argument("--judge", type=Path)
    args = parser.parse_args()
    try:
        packet = load_packet()
        human = AnnotationSet.model_validate_json(
            args.annotations.read_text(encoding="utf-8")
        )
        judge = (
            JudgeSet.model_validate_json(args.judge.read_text(encoding="utf-8"))
            if args.judge
            else None
        )
        report = agreement_report(packet, human, judge)
    except (ValueError, OSError) as exc:
        print(f"Calibration unavailable: {exc}", file=sys.stderr)
        return 2
    print(report.model_dump_json(indent=2))
    return 0 if report.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
