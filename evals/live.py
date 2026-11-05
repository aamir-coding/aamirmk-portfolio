"""Offline preflight by default; live provider execution needs a matched approval."""

from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Self

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from pydantic import (  # noqa: E402
    AwareDatetime,
    Field,
    ValidationError,
    model_validator,
)

from app.llm import Message, ToolCall  # noqa: E402
from app.retrieval.artifacts import (  # noqa: E402
    Sha256,
    canonical_sha256,
    corpus_sha256,
)
from app.retrieval.loader import FactLoader  # noqa: E402
from app.retrieval.models import RetrievedChunk  # noqa: E402
from app.retrieval.retriever import Retriever  # noqa: E402
from evals.budget import (  # noqa: E402
    MAIN,
    UTILITY,
    Attempt,
    Budget,
    CompletionProvider,
    MeteredLLM,
    ProviderReply,
    ProviderRequest,
    Usage,
    input_reservation_bound,
    request_payload,
)
from evals.calibration import (  # noqa: E402
    AnnotationSet,
    GradingPacket,
    JudgeConfiguration,
    JudgeSet,
    Labels,
    Review,
    effective_judge_prompt_sha256,
    judge_system_prompt,
    load_packet,
    packet_fingerprint,
    validate_reviews,
)
from evals.checks import ReplayModel, prompt_files_fingerprint  # noqa: E402
from evals.dataset import (  # noqa: E402
    DEFAULT_ROOT,
    REPO_ROOT,
    case_fingerprint,
    load_cases,
    load_manifest,
    verify_dataset,
)
from evals.schemas import Identifier, Text  # noqa: E402


def source_state() -> dict[str, Any]:
    paths = [
        *sorted((REPO_ROOT / "backend/app").rglob("*.py")),
        *sorted(DEFAULT_ROOT.glob("*.py")),
    ]
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip(),
        "dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True
            ).strip()
        ),
        "code_sha256": canonical_sha256(
            {
                p.relative_to(REPO_ROOT).as_posix(): p.read_text(encoding="utf-8")
                for p in paths
            }
        ),
        "prompt_sha256": prompt_files_fingerprint(),
        "dataset_sha256": canonical_sha256(load_manifest().model_dump(mode="json")),
        "corpus_sha256": corpus_sha256(FactLoader().load_all()),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("groq", "pydantic", "httpx", "fastapi", "fastembed", "numpy")
        },
        "python": sys.version,
    }


class LivePlan(ReplayModel):
    version: Literal[2] = 2
    run_id: Identifier
    stage: Literal["generation", "judge_calibration", "judge_validation"]
    case_ids: list[Identifier] = Field(default_factory=list)
    budget: Budget
    source: dict[str, Any]
    inputs_sha256: str
    judge_configuration: JudgeConfiguration | None = None

    @model_validator(mode="after")
    def stage_inputs(self) -> Self:
        if self.stage.startswith("judge") != (self.judge_configuration is not None):
            raise ValueError(
                "Judge stages require explicit settings; "
                "generation retains application settings"
            )
        if len(set(self.case_ids)) != len(self.case_ids) or (
            self.stage == "generation"
        ) != bool(self.case_ids):
            raise ValueError(
                "Generation requires distinct cases; judging uses its frozen slice"
            )
        return self


class LiveApproval(ReplayModel):
    purpose: Literal["live_groq_authorization"]
    approved_by: Text
    reference: Text
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approved_at: AwareDatetime
    expires_at: AwareDatetime
    limits_verified_at: AwareDatetime
    limits_reference: Text
    visitor_allowance_acknowledged: Literal[True]
    draft_corpus_acknowledged: Literal[True]
    input_reservation_policy_acknowledged: Literal[True]


def inputs_state(
    stage: str,
    case_ids: list[str],
    human: AnnotationSet | None = None,
    prior: JudgeSet | None = None,
) -> dict[str, Any]:
    if stage == "generation":
        cases = {c.id: c for c in load_cases()}
        if any(cid not in cases or cases[cid].target == "protocol" for cid in case_ids):
            raise ValueError("Only explicit development answer cases may be generated")
        return {"cases": {cid: case_fingerprint(cases[cid]) for cid in case_ids}}
    packet = load_packet()
    if human is None:
        raise ValueError(
            "Judging needs a human annotation file; no labels are invented"
        )
    validate_reviews(packet, human)
    graded = {r.item_id for r in human.reviews if r.labels is not None}
    if (
        sum(x.id in graded for x in packet.items if x.slice == "calibration")
        < packet.minimum_calibration
    ):
        raise ValueError("At least twenty calibration answers need human grades first")
    if stage == "judge_validation":
        if (
            sum(x.id in graded for x in packet.items if x.slice == "validation")
            < packet.minimum_validation
        ):
            raise ValueError(
                "Validation needs eight independently human-graded answers"
            )
        if prior is None:
            raise ValueError("Validation requires a completed live calibration slice")
        validate_reviews(packet, prior)
        cal_ids = {x.id for x in packet.items if x.slice == "calibration"}
        if prior.origin != "live" or {r.item_id for r in prior.reviews} != cal_ids:
            raise ValueError(
                "Prior judge result must contain exactly the live calibration slice"
            )
    elif prior is not None:
        raise ValueError("Calibration cannot import validation judge results")
    return {
        "packet_sha256": packet_fingerprint(packet),
        "effective_prompt_sha256": effective_judge_prompt_sha256(),
        "human_sha256": canonical_sha256(human.model_dump(mode="json")),
        "prior_judge_sha256": canonical_sha256(prior.model_dump(mode="json"))
        if prior
        else None,
    }


def preflight(
    plan: LivePlan, *, human: AnnotationSet | None = None, prior: JudgeSet | None = None
) -> None:
    verify_dataset()
    if plan.source != source_state():
        raise ValueError(
            "Source/data/runtime changed since planning; review a new plan"
        )
    if plan.inputs_sha256 != canonical_sha256(
        inputs_state(plan.stage, plan.case_ids, human, prior)
    ):
        raise ValueError("Selected cases or grading inputs changed since planning")
    if plan.stage.startswith("judge") and set(plan.budget.models) != {UTILITY}:
        raise ValueError("Evaluation judge must use the approved 20b model only")
    if plan.stage == "generation" and MAIN not in plan.budget.models:
        raise ValueError("Generation needs an explicit main-model budget")
    if plan.stage.startswith("judge"):
        packet = load_packet()
        wanted = "validation" if plan.stage == "judge_validation" else "calibration"
        items = [x for x in packet.items if x.slice == wanted]
        cap = plan.budget.models[UTILITY]
        expected = JudgeConfiguration(max_completion_tokens=cap.per_call_output)
        if plan.judge_configuration != expected:
            raise ValueError("Judge settings differ from the request/output budget")
        if prior is not None and prior.configuration != expected:
            raise ValueError(
                "Validation must use the same judge settings as calibration"
            )
        if (
            cap.max_attempts < len(items)
            or cap.input_tokens < len(items) * cap.per_call_input
            or cap.output_tokens < len(items) * cap.per_call_output
        ):
            raise ValueError("Budget cannot reserve the full requested judge slice")
        if any(
            input_reservation_bound(
                request_payload(
                    judge_messages(packet, x.id),
                    response_format={"type": "json_object"},
                )
            )
            > cap.per_call_input
            for x in items
        ):
            raise ValueError(
                "A judge prompt exceeds the byte reservation policy; do not execute"
            )


def authorize(plan: LivePlan, approval: LiveApproval, now: datetime) -> None:
    if plan.source.get("dirty"):
        raise ValueError("Live execution requires a clean reviewed source commit")
    if approval.plan_sha256 != canonical_sha256(plan.model_dump(mode="json")):
        raise ValueError(
            "Authorization does not match this exact run and numeric budget"
        )
    if (
        not approval.approved_at <= now < approval.expires_at
        or approval.expires_at - approval.approved_at > timedelta(days=1)
    ):
        raise ValueError("Authorization is not current or exceeds the one-day window")
    if not now - timedelta(days=1) <= approval.limits_verified_at <= now:
        raise ValueError("Exact account limits need a fresh verification reference")


class GroqProvider:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def complete(self, request: ProviderRequest) -> ProviderReply:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": request.messages,
            "max_completion_tokens": request.max_completion_tokens,
            "temperature": 0.2 if request.response_format else 0.4,
            "timeout": request.timeout_seconds,
            "stream": False,
        }
        if request.tools:
            kwargs.update(tools=request.tools, tool_choice="auto")
        if request.response_format:
            kwargs["response_format"] = request.response_format
        if request.reasoning_effort is not None:
            kwargs["reasoning_effort"] = request.reasoning_effort
        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        usage = response.usage
        return ProviderReply(
            content=choice.message.content or "",
            model=response.model,
            usage=Usage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )
            if usage is not None
            else None,
            finish_reason=choice.finish_reason,
            tool_calls=[
                ToolCall(
                    id=tc.id, name=tc.function.name, arguments=tc.function.arguments
                )
                for tc in choice.message.tool_calls or []
            ],
        )


@asynccontextmanager
async def live_provider() -> AsyncIterator[GroqProvider]:
    import os

    from groq import AsyncGroq

    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError(
            "Live execution requires GROQ_API_KEY in the process environment"
        )
    # Standalone eval client: production defaults/retries are deliberately bypassed.
    async with AsyncGroq(
        api_key=key, base_url="https://api.groq.com", max_retries=0, timeout=30.0
    ) as client:
        yield GroqProvider(client)


class TraceRetriever:
    def __init__(self, inner: Retriever) -> None:
        self.inner = inner
        self.calls: list[dict[str, Any]] = []

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        chunks = await self.inner.retrieve(query, top_k)
        self.calls.append(
            {"query": query, "chunks": [c.model_dump(mode="json") for c in chunks]}
        )
        return chunks


async def generate_case(
    case_id: str, llm: MeteredLLM, retriever: Retriever
) -> dict[str, Any]:
    from fastapi import Response

    from app.api.chat import chat
    from app.fit.models import FitReport, FitRequest
    from app.fit.pipeline import FitPipeline
    from app.models import ChatRequest
    from app.safety.quota import DailyQuotaGuard
    from app.safety.rate_limiter import RateLimitResult
    from app.settings import Settings
    from app.tools.registry import ToolRegistry

    case = next(c for c in load_cases() if c.id == case_id)
    trace = TraceRetriever(retriever)
    if case.target == "chat":
        response = await chat(
            request=ChatRequest(
                message=case.conversation[-1].content,
                history=[t.model_dump() for t in case.conversation[:-1]],
                conversation_id=f"eval-{case_id}",
            ),
            response=Response(),
            llm=llm,
            retriever=trace,
            tool_registry=ToolRegistry(),
            rate_limit=RateLimitResult(True, 10, 9, 60),
            _quota=None,
            quota_guard=DailyQuotaGuard(),
        )
        output = response.model_dump(mode="json")
    else:
        pipeline = FitPipeline(
            llm,
            trace,
            settings=Settings(
                _env_file=None,
                GROQ_API_KEY="",
                LLM_MODEL_MAIN=MAIN,
                LLM_MODEL_UTILITY=UTILITY,
            ),
            cache={},
        )
        output = None
        async for event in pipeline.run(
            FitRequest(jd_text=case.conversation[-1].content)
        ):
            if event["event"] == "complete":
                output = FitReport.model_validate(event["data"]).model_dump(mode="json")
            elif event["event"] == "error":
                raise ValueError("Fit pipeline did not produce a complete report")
        if output is None:
            raise ValueError("Missing fit completion")
    return {
        "case_id": case_id,
        "case_sha256": case_fingerprint(case),
        "origin": "guardrail" if output.get("model") == "guardrails" else "live",
        "delivery": "fresh",
        "transport": "chat_json" if case.target == "chat" else "fit_pipeline",
        "output": output,
        "retrieval": trace.calls,
    }


def judge_messages(
    packet: GradingPacket, item_id: str, *, system_prompt: str | None = None
) -> list[Message]:
    item = next(x for x in packet.items if x.id == item_id)
    case = next(c for c in load_cases() if c.id == item.case.id)
    # Neither human labels nor other judge outputs cross this prompt interface.
    data = {
        "conversation": [t.model_dump() for t in case.conversation],
        "answer": item.answer,
        "cited_ids": item.cited_ids,
        "evidence": [e.model_dump() for e in item.evidence],
        "requirement_evidence": item.requirement_evidence,
    }
    return [
        Message(
            role="system",
            content=system_prompt
            if system_prompt is not None
            else judge_system_prompt(),
        ),
        Message(
            role="user",
            content=json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        ),
    ]


class JudgePayload(ReplayModel):
    labels: Labels
    rationale: Text


async def run_jobs(
    plan: LivePlan,
    provider: CompletionProvider,
    *,
    retriever: Retriever | None = None,
    prior: JudgeSet | None = None,
    authorization_expires_at: datetime | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    remaining = min(plan.budget.deadline_seconds, (tomorrow - now).total_seconds())
    if authorization_expires_at is not None:
        remaining = min(remaining, (authorization_expires_at - now).total_seconds())
    if remaining <= 0:
        raise ValueError("Authorization expired before execution")
    runtime_budget = plan.budget.model_copy(update={"deadline_seconds": remaining})
    llm = MeteredLLM(
        provider,
        runtime_budget,
        default_model=UTILITY if plan.stage.startswith("judge") else MAIN,
        reasoning_effort=plan.judge_configuration.reasoning_effort
        if plan.judge_configuration
        else None,
    )
    results: list[dict[str, Any]] = []
    reviews: list[Review] = list(prior.reviews) if prior else []
    status = "complete"
    system_prompt = None
    judge_outputs: list[dict[str, Any]] = []
    failed_judge_outputs: list[dict[str, Any]] = []
    failure: dict[str, Any] | None = None
    try:
        async with asyncio.timeout(runtime_budget.deadline_seconds):
            if plan.stage == "generation":
                if retriever is None:
                    from app.retrieval.hybrid import HybridRetriever

                    retriever = await asyncio.to_thread(
                        HybridRetriever, chunks=FactLoader().load_all()
                    )
                for case_id in plan.case_ids:
                    llm.task_id = case_id
                    result = await generate_case(case_id, llm, retriever)
                    if llm.stop_reason:
                        raise ValueError(
                            "Provider ledger stopped within application fallback"
                        )
                    results.append(result)
            else:
                packet = load_packet()
                system_prompt = judge_system_prompt()
                wanted = (
                    "validation" if plan.stage == "judge_validation" else "calibration"
                )
                for item in packet.items:
                    if item.slice != wanted:
                        continue
                    llm.task_id = item.id
                    response = await llm.complete(
                        judge_messages(packet, item.id, system_prompt=system_prompt),
                        model=UTILITY,
                        response_format={"type": "json_object"},
                    )
                    raw_output = {
                        "item_id": item.id,
                        "item_sha256": item.sha256,
                        "output": response.content,
                    }
                    judge_outputs.append(raw_output)
                    try:
                        grade = JudgePayload.model_validate_json(response.content)
                    except ValidationError as exc:
                        failed_judge_outputs.append(raw_output)
                        failure = {
                            "error_type": type(exc).__name__,
                            "task_id": item.id,
                            "issues": exc.errors(
                                include_url=False,
                                include_input=False,
                                include_context=False,
                            ),
                        }
                        llm.stop_reason = "judge_contract_error"
                        raise
                    reviews.append(
                        Review(
                            item_id=item.id,
                            item_sha256=item.sha256,
                            labels=grade.labels,
                            rationale=grade.rationale,
                        )
                    )
    except (Exception, asyncio.CancelledError) as exc:
        status = "stopped"
        llm.stop_reason = llm.stop_reason or "task_error_or_deadline"
        failure = failure or {"error_type": type(exc).__name__, "task_id": llm.task_id}
    ledger = [a.model_dump(mode="json") for a in llm.attempts]
    return {
        "kind": "live_eval_attempts",
        "status": status,
        "stage": plan.stage,
        "runtime_deadline_seconds": runtime_budget.deadline_seconds,
        "effective_prompt_sha256": canonical_sha256(system_prompt)
        if system_prompt is not None
        else None,
        "judge_configuration": plan.judge_configuration.model_dump(mode="json")
        if plan.judge_configuration
        else None,
        "generation_accuracy_available": False,
        "plan_sha256": canonical_sha256(plan.model_dump(mode="json")),
        "source": plan.source,
        "finished_at": datetime.now(UTC).isoformat(),
        "stop_reason": llm.stop_reason,
        "failure": failure,
        "judge_outputs": judge_outputs,
        "failed_judge_outputs": failed_judge_outputs,
        "attempts": ledger,
        "ledger_sha256": canonical_sha256(ledger),
        "results": results,
        "reviews": [r.model_dump(mode="json") for r in reviews],
    }


class KnownStopReconciliation(ReplayModel):
    purpose: Literal[
        "fully_reported_incomplete_output", "explicit_reported_actual_usage"
    ] = "fully_reported_incomplete_output"
    run_id: Identifier
    receipt_sha256: Sha256
    result_sha256: Sha256
    ledger_sha256: Sha256
    actor: Text
    reference: Text
    created_at: AwareDatetime
    process_exit_verified: Literal[True]
    charged_requests: int = Field(gt=0, strict=True)
    charged_reserved_tokens: int = Field(gt=0, strict=True)
    reported_tokens: int = Field(ge=0, strict=True)


def _known_stop_charge(
    receipt: dict[str, Any],
    result: dict[str, Any],
    run_id: str,
    *,
    actual_usage: bool = False,
) -> tuple[int, int, int]:
    plan_hash = canonical_sha256(receipt["plan"])
    approved = LiveApproval.model_validate(receipt.get("approval", {}))
    if result.get("plan_sha256") != plan_hash or approved.plan_sha256 != plan_hash:
        raise ValueError("Stopped usage must bind to its original approved plan")
    if (
        receipt["plan"]["run_id"] != run_id
        or result.get("kind") != "live_eval_attempts"
        or result.get("status") != "stopped"
        or result.get("stop_reason")
        not in (
            {
                "incomplete_provider_output",
                "task_error_or_deadline",
                "judge_contract_error",
            }
            if actual_usage
            else {"incomplete_provider_output"}
        )
    ):
        raise ValueError("Only a fully reported incomplete-output stop is reconcilable")
    rows = result.get("attempts", [])
    finished = datetime.fromisoformat(result.get("finished_at", ""))
    started = datetime.fromisoformat(receipt.get("started_at", ""))
    if (
        started.utcoffset() is None
        or finished.utcoffset() is None
        or not approved.approved_at <= started <= finished <= approved.expires_at
        or finished > datetime.now(UTC)
    ):
        raise ValueError("A known stop needs a valid completed timestamp")
    if not rows or result.get("ledger_sha256") != canonical_sha256(rows):
        raise ValueError("Missing or inconsistent stopped-run ledger")
    attempts = [Attempt.model_validate(row) for row in rows]
    if [a.number for a in attempts] != list(range(1, len(attempts) + 1)):
        raise ValueError("Stopped-run attempt sequence is not complete")
    budget = Budget.model_validate(receipt["plan"]["budget"])
    counts: dict[str, int] = {}
    previous_finish = 0.0
    for a in attempts:
        cap = budget.models.get(a.model)
        counts[a.model] = counts.get(a.model, 0) + 1
        if (
            cap is None
            or counts[a.model] > cap.max_attempts
            or a.status != "reported"
            or a.usage is None
            or a.finished_seconds is None
            or not previous_finish <= a.start_seconds <= a.finished_seconds
            or a.reported_model != a.model
            or a.reserved_input != cap.per_call_input
            or a.reserved_output != cap.per_call_output
            or a.usage.prompt_tokens > a.reserved_input
            or a.usage.completion_tokens > a.reserved_output
        ):
            raise ValueError("Unknown or inconsistent usage cannot release a hold")
        previous_finish = a.finished_seconds
    for model, cap in budget.models.items():
        selected = [a for a in attempts if a.model == model]
        if (
            sum(a.reserved_input for a in selected) > cap.input_tokens
            or sum(a.reserved_output for a in selected) > cap.output_tokens
        ):
            raise ValueError(
                "Stopped-run reservations exceed the approved model budget"
            )
    return (
        len(attempts),
        sum(a.reserved_input + a.reserved_output for a in attempts),
        sum(a.usage.total_tokens for a in attempts if a.usage is not None),
    )


def build_known_stop_reconciliation(
    run_dir: Path,
    *,
    actor: str,
    reference: str,
    process_exit_verified: bool,
    actual_usage: bool = False,
) -> KnownStopReconciliation:
    if (run_dir.parent / "active.lock").exists():
        raise ValueError("Cannot reconcile while a runner is active")
    receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
    result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    requests, reserved, reported = _known_stop_charge(
        receipt, result, run_dir.name, actual_usage=actual_usage
    )
    return KnownStopReconciliation(
        purpose="explicit_reported_actual_usage"
        if actual_usage
        else "fully_reported_incomplete_output",
        run_id=run_dir.name,
        receipt_sha256=canonical_sha256(receipt),
        result_sha256=canonical_sha256(result),
        ledger_sha256=result["ledger_sha256"],
        actor=actor,
        reference=reference,
        created_at=datetime.now(UTC),
        process_exit_verified=process_exit_verified,
        charged_requests=requests,
        charged_reserved_tokens=reserved,
        reported_tokens=reported,
    )


def check_local_prior_usage(plan: LivePlan, directory: Path, now: datetime) -> None:
    known_requests = known_tokens = 0
    for receipt_path in directory.glob("*/receipt.json"):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        started = datetime.fromisoformat(receipt["started_at"]).astimezone(UTC)
        old_budget = Budget.model_validate(receipt["plan"]["budget"])
        finished = started + timedelta(seconds=old_budget.deadline_seconds)
        # Charge whole approved ceilings for an unreconciled/crashed run.
        request_charge = sum(x.max_attempts for x in old_budget.models.values())
        token_charge = sum(
            x.input_tokens + x.output_tokens for x in old_budget.models.values()
        )
        result_path = receipt_path.parent / "result.json"
        reconciliation_path = receipt_path.parent / "reconciliation.json"
        actual_path = receipt_path.parent / "actual-usage-reconciliation.json"
        actual_usage = actual_path.exists()
        if actual_usage:
            reconciliation_path = actual_path
        if reconciliation_path.exists() and not result_path.exists():
            raise ValueError("A reconciliation cannot replace a missing result")
        if result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if result.get("finished_at"):
                finished = max(
                    started,
                    datetime.fromisoformat(result["finished_at"]).astimezone(UTC),
                )
            if result.get("status") == "complete":
                request_charge = len(result["attempts"])
                token_charge = sum(
                    max(
                        a["reserved_input"] + a["reserved_output"],
                        a["usage"]["total_tokens"],
                    )
                    for a in result["attempts"]
                )
            if reconciliation_path.exists():
                record = KnownStopReconciliation.model_validate_json(
                    reconciliation_path.read_text(encoding="utf-8")
                )
                if (
                    record.purpose
                    != (
                        "explicit_reported_actual_usage"
                        if actual_usage
                        else "fully_reported_incomplete_output"
                    )
                    or record.run_id != receipt_path.parent.name
                    or record.receipt_sha256 != canonical_sha256(receipt)
                    or record.result_sha256 != canonical_sha256(result)
                    or record.ledger_sha256 != result.get("ledger_sha256")
                    or not finished <= record.created_at <= now
                ):
                    raise ValueError("Stopped-run reconciliation is stale or invalid")
                requests, reserved, reported = _known_stop_charge(
                    receipt, result, record.run_id, actual_usage=actual_usage
                )
                if (
                    record.charged_requests,
                    record.charged_reserved_tokens,
                    record.reported_tokens,
                ) != (requests, reserved, reported):
                    raise ValueError(
                        "Reconciliation cannot reduce attempted-call reservations"
                    )
                request_charge, token_charge = (
                    requests,
                    reported if actual_usage else reserved,
                )
        if now < finished + timedelta(seconds=60):
            raise ValueError(
                "Local run cooldown has not elapsed; do not reset minute usage"
            )
        if not started.date() <= now.date() <= finished.date():
            continue
        known_requests += request_charge
        known_tokens += token_charge
    if (
        plan.budget.prior_requests_today < known_requests
        or plan.budget.prior_tokens_today < known_tokens
    ):
        raise ValueError(
            "Plan understates known local prior usage; review remaining daily budget"
        )


async def execute(
    plan: LivePlan,
    approval: LiveApproval,
    directory: Path,
    *,
    human: AnnotationSet | None = None,
    prior: JudgeSet | None = None,
) -> dict[str, Any]:
    preflight(plan, human=human, prior=prior)
    authorize(plan, approval, datetime.now(UTC))
    directory.mkdir(parents=True, exist_ok=True)
    active = directory / "active.lock"
    with active.open("x", encoding="utf-8") as handle:
        handle.write(plan.run_id)
    try:
        run_dir = directory / plan.run_id
        if run_dir.exists():
            raise FileExistsError("Run ID already consumed; no automatic resume")
        check_local_prior_usage(plan, directory, datetime.now(UTC))
        # No automatic resume/reuse: approval ceilings cannot reset on a retry.
        run_dir.mkdir()
        receipt = {
            "plan": plan.model_dump(mode="json"),
            "approval": approval.model_dump(mode="json"),
            "state": "started_consumption_unknown_until_result",
            "started_at": datetime.now(UTC).isoformat(),
        }
        (run_dir / "receipt.json").write_text(
            json.dumps(receipt, indent=2), encoding="utf-8"
        )

        def persist_result(value: dict[str, Any]) -> None:
            temporary = run_dir / "result.json.tmp"
            temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
            temporary.replace(run_dir / "result.json")

        result = None
        try:
            async with live_provider() as provider:
                result = await run_jobs(
                    plan,
                    provider,
                    prior=prior,
                    authorization_expires_at=approval.expires_at,
                )
                persist_result(result)
                await asyncio.to_thread(preflight, plan, human=human, prior=prior)
        except BaseException as exc:
            # Preserve the attempt ledger even if client cleanup fails after calls.
            result = dict(
                result
                or {
                    "attempts": [],
                    "results": [],
                    "reviews": [],
                    "generation_accuracy_available": False,
                    "plan_sha256": canonical_sha256(plan.model_dump(mode="json")),
                }
            )
            result.update(
                status="stopped",
                stop_reason="client_lifecycle_or_consumption_unknown",
                finished_at=datetime.now(UTC).isoformat(),
            )
            persist_result(result)
            if isinstance(exc, KeyboardInterrupt | SystemExit | asyncio.CancelledError):
                raise
        if plan.stage.startswith("judge") and result["status"] == "complete":
            packet = load_packet()
            judged = JudgeSet(
                packet_sha256=packet_fingerprint(packet),
                rubric_sha256=packet.rubric_sha256,
                prompt_sha256=packet.judge_prompt_sha256,
                effective_prompt_sha256=result["effective_prompt_sha256"],
                configuration=plan.judge_configuration,
                origin="live",
                model=UTILITY,
                authorization_reference=approval.reference,
                ledger_sha256=result["ledger_sha256"],
                reviews=[Review.model_validate(row) for row in result["reviews"]],
            )
            (run_dir / "judge.json").write_text(
                judged.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )
        return result
    finally:
        active.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--draft-plan", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--budget", type=Path)
    parser.add_argument(
        "--stage",
        choices=("generation", "judge_calibration", "judge_validation"),
        default="generation",
    )
    parser.add_argument("--cases", nargs="+", default=[])
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--prior-judge", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approval", type=Path)
    args = parser.parse_args()
    if not args.plan and not args.draft_plan and not args.execute:
        print(
            "Offline only: no plan executed, no provider client created, "
            "zero Groq calls."
        )
        return 0
    try:
        human = (
            AnnotationSet.model_validate_json(
                args.annotations.read_text(encoding="utf-8")
            )
            if args.annotations
            else None
        )
        prior = (
            JudgeSet.model_validate_json(args.prior_judge.read_text(encoding="utf-8"))
            if args.prior_judge
            else None
        )
        if args.draft_plan:
            if args.execute or args.plan or not args.budget or not args.run_id:
                raise ValueError(
                    "Draft planning needs run-id/budget and cannot execute"
                )
            verify_dataset()
            budget = Budget.model_validate_json(args.budget.read_text(encoding="utf-8"))
            if args.stage.startswith("judge") and set(budget.models) != {UTILITY}:
                raise ValueError(
                    "Evaluation judge must budget only the fixed utility model"
                )
            plan = LivePlan(
                run_id=args.run_id,
                stage=args.stage,
                case_ids=args.cases,
                budget=budget,
                judge_configuration=JudgeConfiguration(
                    max_completion_tokens=budget.models[UTILITY].per_call_output
                )
                if args.stage.startswith("judge")
                else None,
                source=source_state(),
                inputs_sha256=canonical_sha256(
                    inputs_state(args.stage, args.cases, human, prior)
                ),
            )
            preflight(plan, human=human, prior=prior)
            with args.draft_plan.open("x", encoding="utf-8") as handle:
                handle.write(plan.model_dump_json(indent=2) + "\n")
        else:
            if not args.plan:
                raise ValueError("Live execution requires an exact reviewed plan")
            plan = LivePlan.model_validate_json(args.plan.read_text(encoding="utf-8"))
            preflight(plan, human=human, prior=prior)
        digest = canonical_sha256(plan.model_dump(mode="json"))
        if not args.execute:
            print(
                json.dumps(
                    {
                        "mode": "offline_preflight",
                        "plan_sha256": digest,
                        "groq_calls": 0,
                        "authorization": "not_granted",
                    }
                )
            )
            return 0
        if args.approval is None:
            raise ValueError(
                "Live evaluation requires separate explicit budget approval"
            )
        approval = LiveApproval.model_validate_json(
            args.approval.read_text(encoding="utf-8")
        )
        result = asyncio.run(
            execute(
                plan, approval, REPO_ROOT / "build/eval-live", human=human, prior=prior
            )
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "attempts": len(result["attempts"]),
                    "stop_reason": result["stop_reason"],
                }
            )
        )
        return 0 if result["status"] == "complete" else 1
    except (ValueError, OSError) as exc:
        # Schema/path failures are safe; provider exception text is never emitted.
        print(f"Live eval unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
