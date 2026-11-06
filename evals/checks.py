"""Deterministic checks on saved responses; no generator or semantic judge."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.fit.models import FitReport
from app.fit.scorer import compute_fit_summary
from app.models import SourceCitation
from app.retrieval.artifacts import Sha256
from app.tools.projects import ProjectCardData
from evals.schemas import EvalCase, Text


class ReplayModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class NegativeEvidenceRule(ReplayModel):
    requirement_contains: Text
    negative_evidence_ids: list[Text] = Field(min_length=1)


class ReplayChecks(ReplayModel):
    must_include: list[Text] = Field(default_factory=list)
    must_not_include: list[Text] = Field(default_factory=list)
    max_chars: int = Field(default=6000, gt=0)
    expect_refusal: bool | None = None
    expected_error: Text | None = None
    negative_rules: list[NegativeEvidenceRule] = Field(default_factory=list)


class RecordedUsage(ReplayModel):
    source: Literal["unavailable", "fake", "provider"] = "unavailable"
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def honest_usage(self) -> Self:
        missing = self.prompt_tokens is None or self.completion_tokens is None
        if self.source == "unavailable":
            if self.prompt_tokens is not None or self.completion_tokens is not None:
                raise ValueError("Unavailable usage must not contain invented counts")
        elif missing:
            raise ValueError("Reported usage requires both token counts")
        return self


class CaseReference(ReplayModel):
    id: Text
    version: int = Field(gt=0)
    sha256: Sha256


class Recording(ReplayModel):
    id: Text
    transport: Literal["chat_sse", "fit_sse", "preset_json"]
    origin: Literal["fake", "curated", "live"]
    delivery: Literal["fresh", "cached", "preset"]
    model: Text | None = None
    authorization_reference: Text | None = None
    case: CaseReference | None = None
    raw_sse: str = ""
    preset_report: FitReport | None = None
    retrieved_chat_ids: list[str] = Field(default_factory=list)
    retrieval_queries: list[str] = Field(default_factory=list)
    evidence_by_requirement: dict[str, list[str]] = Field(default_factory=dict)
    checks: ReplayChecks = Field(default_factory=ReplayChecks)
    usage: RecordedUsage = Field(default_factory=RecordedUsage)
    adapter_complete_calls: int = Field(default=0, ge=0)
    adapter_stream_calls: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def coherent_origin(self) -> Self:
        if self.origin == "live" and (
            not self.authorization_reference or not self.model
        ):
            raise ValueError(
                "Live recordings require an authorization reference and model"
            )
        if self.origin != "live" and self.usage.source == "provider":
            raise ValueError("Fake/curated recordings cannot claim provider usage")
        if self.transport == "preset_json":
            if (
                self.preset_report is None
                or self.raw_sse
                or self.delivery != "preset"
                or self.origin != "curated"
            ):
                raise ValueError(
                    "Preset capture must contain an explicitly curated report"
                )
        elif (
            not self.raw_sse
            or self.preset_report is not None
            or self.delivery == "preset"
        ):
            raise ValueError("SSE capture must contain its raw transport response")
        return self


class CaptureBundle(ReplayModel):
    schema_version: Literal[1] = 1
    purpose: Literal["fake_and_curated_endpoint_captures"] = (
        "fake_and_curated_endpoint_captures"
    )
    captured_at: datetime
    commit: str
    dirty: bool
    corpus_sha256: Sha256
    dataset_manifest_sha256: Sha256
    prompt_files_sha256: Sha256
    capture_source_sha256: Sha256
    records: list[Recording] = Field(min_length=1)

    @model_validator(mode="after")
    def distinct_offline_records(self) -> Self:
        if len({r.id for r in self.records}) != len(self.records):
            raise ValueError("Duplicate recording IDs")
        if any(record.origin == "live" for record in self.records):
            raise ValueError(
                "The offline capture bundle cannot contain live recordings"
            )
        if any(
            record.origin == "fake" and record.case is None for record in self.records
        ):
            raise ValueError("Endpoint fake recordings must bind to a development case")
        return self


def prompt_files_fingerprint() -> str:
    from app.retrieval.artifacts import canonical_sha256
    from evals.dataset import REPO_ROOT

    paths = [
        REPO_ROOT / "backend/app/prompts/system.txt",
        REPO_ROOT / "backend/app/fit/prompts.py",
        REPO_ROOT / "backend/app/retrieval/rewriter.py",
    ]
    return canonical_sha256(
        {
            p.relative_to(REPO_ROOT).as_posix(): p.read_text(encoding="utf-8")
            for p in paths
        }
    )


class TokenPayload(ReplayModel):
    token: str


class SourcesPayload(ReplayModel):
    sources: list[SourceCitation]


class CardPayload(ReplayModel):
    card: ProjectCardData


class DonePayload(ReplayModel):
    conversation_id: Text
    sources: list[SourceCitation] = Field(default_factory=list)
    cards: list[ProjectCardData] = Field(default_factory=list)


class ChatErrorPayload(ReplayModel):
    detail: Text


class FitErrorPayload(ReplayModel):
    code: Text
    message: Text


class ProgressPayload(ReplayModel):
    step: Text
    origin: Literal["curated", "cache"] | None = None
    message: Text
    percent: float = Field(ge=0, le=100)


class CapturedEvent(ReplayModel):
    event: str
    data: dict[str, object]


class Transcript(ReplayModel):
    answer: str = ""
    sources: list[SourceCitation] = Field(default_factory=list)
    cards: list[ProjectCardData] = Field(default_factory=list)
    fit_report: FitReport | None = None
    error_code: str | None = None
    cache_hit: bool = False
    events: list[CapturedEvent] = Field(default_factory=list)


class ReplayProtocolError(ValueError):
    def __init__(self, code: str, prefix: Transcript | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.prefix = prefix


def decode_recording(record: Recording) -> Transcript:
    if record.transport == "preset_json":
        return Transcript(fit_report=record.preset_report)
    frames = record.raw_sse.replace("\r\n", "\n").replace("\r", "\n").split("\n\n")
    pending = frames.pop()
    answer: list[str] = []
    sources: list[SourceCitation] = []
    cards: list[ProjectCardData] = []
    events: list[CapturedEvent] = []
    terminal = False
    report = None
    error = None
    cache_hit = False

    def snapshot() -> Transcript:
        return Transcript(
            answer="".join(answer),
            sources=sources,
            cards=cards,
            fit_report=report,
            error_code=error,
            cache_hit=cache_hit,
            events=events,
        )

    for frame in frames:
        lines = frame.splitlines()
        data_lines = [
            line[5:].lstrip(" ") for line in lines if line.startswith("data:")
        ]
        if not data_lines:
            continue
        if terminal:
            raise ReplayProtocolError("protocol_error", snapshot())
        event = next(
            (line[6:].strip() for line in lines if line.startswith("event:")), "message"
        )
        try:
            payload = json.loads("\n".join(data_lines))
            if record.transport == "chat_sse":
                if event == "token":
                    answer.append(TokenPayload.model_validate(payload).token)
                elif event == "sources":
                    sources.extend(SourcesPayload.model_validate(payload).sources)
                elif event == "card":
                    cards.append(CardPayload.model_validate(payload).card)
                elif event == "done":
                    done = DonePayload.model_validate(payload)
                    if done.sources != sources or done.cards != cards:
                        raise ReplayProtocolError("terminal_metadata_mismatch")
                    terminal = True
                elif event == "error":
                    ChatErrorPayload.model_validate(payload)
                    error, terminal = "chat_error", True
                else:
                    raise ReplayProtocolError("malformed_event")
            elif event == "progress":
                cache_hit |= ProgressPayload.model_validate(payload).step == "cache_hit"
            elif event == "complete":
                report, terminal = FitReport.model_validate(payload), True
            elif event == "error":
                error, terminal = FitErrorPayload.model_validate(payload).code, True
            else:
                raise ReplayProtocolError("malformed_event")
            events.append(CapturedEvent(event=event, data=payload))
        except (ValueError, TypeError, ValidationError) as exc:
            if isinstance(exc, ReplayProtocolError):
                raise ReplayProtocolError(exc.code, snapshot()) from exc
            raise ReplayProtocolError("malformed_event", snapshot()) from exc
    if pending.strip() or not terminal:
        code = "protocol_error" if terminal else "premature_eof"
        raise ReplayProtocolError(code, snapshot())
    return snapshot()


class CheckResult(ReplayModel):
    id: str
    passed: bool
    failed_checks: list[str]
    unavailable_checks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    observed_error: str | None = None
    semantic_review: Literal["pending"] = "pending"
    generation_accuracy_available: Literal[False] = False


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def check_recording(
    record: Recording,
    public_fact_ids: set[str],
    *,
    case: EvalCase | None = None,
) -> CheckResult:
    failed: list[str] = []
    unavailable: list[str] = []
    warnings: list[str] = []
    expected_error = record.checks.expected_error
    expect_refusal = record.checks.expect_refusal
    if any(
        not set(rule.negative_evidence_ids) <= public_fact_ids
        for rule in record.checks.negative_rules
    ):
        failed.append("rule_configuration")
    if case is not None:
        from evals.dataset import case_fingerprint

        if (
            record.case is None
            or record.case.id != case.id
            or record.case.version != case.version
            or record.case.sha256 != case_fingerprint(case)
            or case.split != "development"
        ):
            failed.append("case_binding")
        if case.target in {"chat", "fit"} and record.transport != f"{case.target}_sse":
            failed.append("transport_binding")
        if case.target == "protocol" and record.transport == "preset_json":
            failed.append("transport_binding")
        for recorded, frozen in (
            (record.checks.expected_error, case.checks.expected_error),
            (record.checks.expect_refusal, case.checks.expect_refusal),
        ):
            if recorded is not None and frozen is not None and recorded != frozen:
                failed.append("expectation_conflict")
        if case.checks.expected_error is not None:
            expected_error = case.checks.expected_error
        if case.checks.expect_refusal is not None:
            expect_refusal = case.checks.expect_refusal
    protocol_error = None
    try:
        transcript = decode_recording(record)
    except ReplayProtocolError as exc:
        protocol_error = exc.code
        transcript = exc.prefix or Transcript()
    observed_error = protocol_error or transcript.error_code
    if record.transport == "chat_sse":
        source_ids = [source.chunk_id for source in transcript.sources]
        if not set(source_ids) <= public_fact_ids or len(source_ids) != len(
            set(source_ids)
        ):
            failed.append("citation_identity")
        if not set(source_ids) <= set(record.retrieved_chat_ids):
            failed.append("retrieved_membership")
    if expected_error != observed_error:
        failed.append("protocol" if protocol_error else "expected_error")
    report = transcript.fit_report
    output = (
        transcript.answer
        if report is None
        else "\n".join(
            [
                report.summary,
                *[
                    f"{row.explanation}\n{row.ramp_up or ''}"
                    for row in report.requirements
                ],
            ]
        )
    )
    required = record.checks.must_include + (case.checks.must_include if case else [])
    forbidden = record.checks.must_not_include + (
        case.checks.must_not_include if case else []
    )
    if not observed_error and any(
        _normalized(fragment) not in _normalized(output) for fragment in required
    ):
        failed.append("required_text")
    if any(_normalized(fragment) in _normalized(output) for fragment in forbidden):
        failed.append("forbidden_text")
    if (not observed_error and not output.strip()) or len(
        output
    ) > record.checks.max_chars:
        failed.append("length")
    if observed_error:
        unavailable.append("answer_completion")
        if required:
            unavailable.append("required_text")
        if expect_refusal is not None:
            unavailable.append("refusal")
        if record.transport == "fit_sse" and report is None:
            unavailable.append("requirement_local_evidence")
    if not observed_error and expect_refusal is not None:
        lexical_refusal = bool(
            re.search(
                r"\bI (?:can only answer|only answer|"
                r"cannot (?:help|provide)|can't help)\b",
                output,
                re.I,
            )
        )
        if lexical_refusal != expect_refusal:
            failed.append("refusal")
    if report is None:
        retrieved = set(record.retrieved_chat_ids)
    else:
        req_ids = [row.requirement.id for row in report.requirements]
        if not req_ids or len(req_ids) != len(set(req_ids)):
            failed.append("requirement_ids")
        if report.score != compute_fit_summary(report.requirements):
            failed.append("fit_score")
        retrieved = {
            cid for ids in record.evidence_by_requirement.values() for cid in ids
        }
        cited = [cid for row in report.requirements for cid in row.evidence_chunk_ids]
        if not set(cited) <= public_fact_ids:
            failed.append("citation_identity")
        for row in report.requirements:
            if row.verdict != "gap" and not row.evidence_chunk_ids:
                failed.append("positive_evidence")
            for rule in record.checks.negative_rules:
                if (
                    rule.requirement_contains.casefold()
                    in row.requirement.text.casefold()
                    and row.verdict != "gap"
                    and row.evidence_chunk_ids
                    and set(row.evidence_chunk_ids) <= set(rule.negative_evidence_ids)
                ):
                    failed.append("negative_evidence")
        if record.origin == "curated" and not record.evidence_by_requirement:
            unavailable.append("requirement_local_evidence")
        else:
            if (
                set(req_ids) != set(record.evidence_by_requirement)
                or not retrieved <= public_fact_ids
            ):
                failed.append("requirement_local_evidence")
            for row in report.requirements:
                local = set(record.evidence_by_requirement.get(row.requirement.id, []))
                if not set(row.evidence_chunk_ids) <= local:
                    failed.append("requirement_local_evidence")
        if record.delivery == "cached":
            if not transcript.cache_hit:
                failed.append("cache_origin")
            if not report.cached:
                warnings.append("server_cached_flag_unreliable")
        elif transcript.cache_hit:
            failed.append("cache_origin")
    if not observed_error and case is not None and case.checks.sources.mode != "none":
        wanted = set(case.checks.sources.ids)
        if (case.checks.sources.mode == "all_relevant" and not wanted <= retrieved) or (
            case.checks.sources.mode == "any_of" and not wanted & retrieved
        ):
            failed.append("expected_sources")
    return CheckResult(
        id=record.id,
        passed=not failed,
        failed_checks=sorted(set(failed)),
        unavailable_checks=unavailable,
        warnings=warnings,
        observed_error=observed_error,
    )
