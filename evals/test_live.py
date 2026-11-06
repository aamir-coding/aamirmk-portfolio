"""Budgeting tests inject clocks/providers; they never construct a live client."""

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from app.llm import Message
from app.retrieval.artifacts import canonical_sha256
from evals.budget import (
    Budget,
    BudgetStop,
    MeteredLLM,
    ProviderReply,
    ProviderRequest,
    Usage,
)
from evals.live import LiveApproval, LivePlan, authorize, inputs_state


@dataclass
class Clock:
    now: float = 0

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds


class Provider:
    def __init__(self, failure: str = "") -> None:
        self.calls = 0
        self.failure = failure
        self.requests: list[ProviderRequest] = []

    async def complete(self, request: ProviderRequest) -> ProviderReply:
        self.calls += 1
        self.requests.append(request)
        if self.failure == "error":
            raise RuntimeError("secret-bearing provider message")
        return ProviderReply(
            content="answer",
            model="unexpected" if self.failure == "model" else request.model,
            usage=None
            if self.failure == "usage"
            else Usage(
                prompt_tokens=15000 if self.failure == "overflow" else 20,
                completion_tokens=5,
                total_tokens=15005 if self.failure == "overflow" else 25,
            ),
            finish_reason="length" if self.failure == "length" else "stop",
        )


def budget(**changes: object) -> Budget:
    data = {
        "models": {
            "openai/gpt-oss-120b": {
                "max_attempts": 3,
                "input_tokens": 18000,
                "output_tokens": 300,
                "per_call_input": 6000,
                "per_call_output": 100,
            }
        },
        "shared_rpm": 30,
        "shared_tpm": 8000,
        "shared_rpd": 1000,
        "shared_tpd": 200000,
        "prior_requests_today": 0,
        "prior_tokens_today": 0,
        "visitor_rpm": 10,
        "visitor_tpm": 1000,
        "visitor_rpd": 100,
        "visitor_tpd": 20000,
        "min_interval_seconds": 3,
        "deadline_seconds": 240,
        "request_timeout_seconds": 15,
    }
    data.update(changes)
    return Budget.model_validate(data)


@pytest.mark.asyncio
async def test_provider_http_failure_retains_safe_diagnostics_only() -> None:
    import httpx
    from groq import BadRequestError

    class Rejected(Provider):
        async def complete(self, request: ProviderRequest) -> ProviderReply:
            self.calls += 1
            raise BadRequestError(
                "secret-bearing message",
                response=httpx.Response(
                    400, request=httpx.Request("POST", "https://example.invalid")
                ),
                body={
                    "error": {
                        "code": "json_validate_failed",
                        "message": "secret-bearing message",
                        "failed_generation": "secret-bearing hidden output",
                    }
                },
            )

    clock, provider = Clock(), Rejected()
    llm = MeteredLLM(provider, budget(), clock=clock, sleep=clock.sleep)
    with pytest.raises(BudgetStop, match="provider_consumption_unknown"):
        await llm.complete([Message(role="user", content="public eval")])
    row = llm.attempts[0].model_dump(mode="json")
    assert row["provider_error"] == {
        "exception_type": "BadRequestError",
        "status_code": 400,
        "code": "json_validate_failed",
    }
    assert row["usage"] is None and row["status"] == "unknown"
    assert provider.calls == 1
    assert "secret-bearing" not in json.dumps(row)


@pytest.mark.asyncio
async def test_every_attempt_reserves_caps_and_reports_actual_usage() -> None:
    provider, clock = Provider(), Clock()
    llm = MeteredLLM(provider, budget(), clock=clock, sleep=clock.sleep)
    for _ in range(3):
        await llm.complete([Message(role="user", content="hello")])
    assert provider.calls == 3
    assert clock.now >= 120
    assert sum(x.reserved_input for x in llm.attempts) == 18000
    assert sum(x.usage.prompt_tokens for x in llm.attempts) == 60
    with pytest.raises(BudgetStop):
        await llm.complete([])
    assert provider.calls == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["error", "usage", "overflow", "model", "length"])
async def test_uncertain_or_invalid_consumption_stops_all_further_calls(
    failure: str,
) -> None:
    provider, clock = Provider(failure), Clock()
    llm = MeteredLLM(provider, budget(), clock=clock, sleep=clock.sleep)
    with pytest.raises(BudgetStop):
        await llm.complete([Message(role="user", content="hello")])
    with pytest.raises(BudgetStop):
        await llm.complete([])
    assert provider.calls == 1
    assert llm.stop_reason
    assert "secret-bearing" not in str(llm.attempts)
    if failure == "length":
        assert llm.attempts[0].finish_reason == "length"


@pytest.mark.asyncio
async def test_prompt_over_cap_and_deadline_stop_before_network() -> None:
    provider, clock = Provider(), Clock()
    llm = MeteredLLM(provider, budget(), clock=clock, sleep=clock.sleep)
    with pytest.raises(BudgetStop):
        await llm.complete([Message(role="user", content="x" * 6000)])
    assert provider.calls == 0
    llm = MeteredLLM(
        provider, budget(deadline_seconds=1), clock=clock, sleep=clock.sleep
    )
    clock.now = 2
    with pytest.raises(BudgetStop):
        await llm.complete([])
    assert provider.calls == 0


def test_visitor_headroom_and_per_model_totals_are_required() -> None:
    with pytest.raises(ValueError):
        budget(visitor_tpm=8000)
    with pytest.raises(ValueError):
        budget(shared_tpd=1000)
    with pytest.raises(ValueError):
        budget(shared_rpd=101)


@pytest.mark.asyncio
async def test_model_override_cannot_escape_fixed_approved_pair() -> None:
    provider, clock = Provider(), Clock()
    llm = MeteredLLM(provider, budget(), clock=clock, sleep=clock.sleep)
    with pytest.raises(BudgetStop):
        await llm.complete([], model="unapproved")
    assert provider.calls == 0


def plan() -> LivePlan:
    return LivePlan(
        run_id="test-run",
        stage="generation",
        case_ids=["eval-01-degree-grad"],
        budget=budget(),
        source={"commit": "test-only", "dirty": False},
        inputs_sha256=canonical_sha256(
            inputs_state("generation", ["eval-01-degree-grad"])
        ),
    )


def test_judge_plan_requires_explicit_generation_settings() -> None:
    data = plan().model_dump(mode="json")
    data.update(stage="judge_calibration", case_ids=[])
    with pytest.raises(ValueError):
        LivePlan.model_validate(data)


def approval(proposal: LivePlan) -> LiveApproval:
    now = datetime.now(UTC)
    return LiveApproval(
        purpose="live_groq_authorization",
        approved_by="TEST ONLY",
        reference="TEST ONLY: no actual authorization",
        plan_sha256=canonical_sha256(proposal.model_dump(mode="json")),
        approved_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=5),
        limits_verified_at=now,
        limits_reference="TEST ONLY",
        visitor_allowance_acknowledged=True,
        draft_corpus_acknowledged=True,
        input_reservation_policy_acknowledged=True,
    )


@pytest.mark.parametrize(
    "change",
    ["numeric_budget", "dirty", "expired", "limits_stale", "future", "long_approval"],
)
def test_authorization_binds_budget_source_time_and_verified_limits(
    change: str,
) -> None:
    proposal = plan()
    accepted = approval(proposal)
    if change == "numeric_budget":
        proposal = proposal.model_copy(update={"budget": budget(shared_tpm=9000)})
    if change == "dirty":
        proposal = proposal.model_copy(update={"source": {"dirty": True}})
    if change == "expired":
        accepted = accepted.model_copy(
            update={"expires_at": datetime.now(UTC) - timedelta(seconds=1)}
        )
    if change == "limits_stale":
        accepted = accepted.model_copy(
            update={"limits_verified_at": datetime.now(UTC) - timedelta(days=2)}
        )
    if change == "future":
        accepted = accepted.model_copy(
            update={"approved_at": datetime.now(UTC) + timedelta(seconds=10)}
        )
    if change == "long_approval":
        accepted = accepted.model_copy(
            update={"expires_at": datetime.now(UTC) + timedelta(days=2)}
        )
    with pytest.raises(ValueError):
        authorize(proposal, accepted, datetime.now(UTC))


def test_daily_caps_include_already_consumed_organization_usage() -> None:
    with pytest.raises(ValueError):
        budget(prior_tokens_today=190000)
    with pytest.raises(ValueError):
        budget(prior_requests_today=999)


@pytest.mark.asyncio
async def test_provider_timeout_is_unknown_and_does_not_retry() -> None:
    class SlowProvider(Provider):
        async def complete(self, request: ProviderRequest) -> ProviderReply:
            self.calls += 1
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    clock, provider = Clock(), SlowProvider()
    llm = MeteredLLM(
        provider, budget(request_timeout_seconds=0.01), clock=clock, sleep=clock.sleep
    )
    with pytest.raises(BudgetStop):
        await llm.complete([])
    assert provider.calls == 1
    assert llm.attempts[0].status == "unknown"
    with pytest.raises(BudgetStop):
        await llm.complete([])
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_unicode_and_tools_are_included_in_prompt_admission() -> None:
    clock, provider = Clock(), Provider()
    llm = MeteredLLM(provider, budget(), clock=clock, sleep=clock.sleep)
    with pytest.raises(BudgetStop):
        await llm.complete(
            [Message(role="user", content="ðŸ§ª" * 1400)],
            tools=[{"description": "x" * 1000}],
        )
    assert provider.calls == 0


def test_offline_cli_never_constructs_a_provider(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import evals.live as live

    def forbidden() -> None:
        pytest.fail("No live provider may be constructed")

    monkeypatch.setattr(live, "live_provider", forbidden)
    monkeypatch.setattr("sys.argv", ["evals.live"])
    assert live.main() == 0
    assert "zero Groq calls" in capsys.readouterr().out
    monkeypatch.setattr("sys.argv", ["evals.live", "--execute"])
    assert live.main() == 2


def test_preflight_rejects_stale_source_and_held_out_or_protocol_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.live as live

    proposal = plan()
    monkeypatch.setattr(
        live, "source_state", lambda: {"dirty": False, "commit": "changed"}
    )
    with pytest.raises(ValueError, match="Source/data/runtime"):
        live.preflight(proposal)
    for case_id in ("unselected-reserved-case", "protocol-premature-eof"):
        with pytest.raises(ValueError):
            inputs_state("generation", [case_id])


@pytest.mark.asyncio
async def test_run_id_cannot_be_reused_and_receipt_precedes_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import evals.live as live

    proposal = plan()
    opened = 0
    monkeypatch.setattr(live, "source_state", lambda: proposal.source)

    @asynccontextmanager
    async def factory():
        nonlocal opened
        opened += 1
        assert (tmp_path / proposal.run_id / "receipt.json").exists()
        yield Provider()

    async def jobs(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"status": "complete", "attempts": [], "results": [], "reviews": []}

    monkeypatch.setattr(live, "live_provider", factory)
    monkeypatch.setattr(live, "run_jobs", jobs)
    assert (await live.execute(proposal, approval(proposal), tmp_path))[
        "status"
    ] == "complete"
    with pytest.raises(FileExistsError):
        await live.execute(proposal, approval(proposal), tmp_path)
    assert opened == 1
    assert not (tmp_path / "active.lock").exists()
    (tmp_path / "active.lock").write_text("another run")
    with pytest.raises(FileExistsError):
        await live.execute(proposal, approval(proposal), tmp_path)
    assert opened == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("cancelled", [False, True])
async def test_client_cleanup_failure_preserves_attempt_ledger(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, cancelled: bool
) -> None:
    import evals.live as live

    proposal = plan()
    monkeypatch.setattr(live, "source_state", lambda: proposal.source)

    @asynccontextmanager
    async def factory():
        yield Provider()
        if cancelled:
            raise asyncio.CancelledError()
        raise RuntimeError("secret-bearing cleanup failure")

    async def jobs(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "status": "complete",
            "attempts": [{"number": 1}],
            "results": [],
            "reviews": [],
        }

    monkeypatch.setattr(live, "live_provider", factory)
    monkeypatch.setattr(live, "run_jobs", jobs)
    if cancelled:
        with pytest.raises(asyncio.CancelledError):
            await live.execute(proposal, approval(proposal), tmp_path)
        result = json.loads((tmp_path / proposal.run_id / "result.json").read_text())
    else:
        result = await live.execute(proposal, approval(proposal), tmp_path)
    assert result["status"] == "stopped"
    saved = (tmp_path / proposal.run_id / "result.json").read_text()
    assert "secret-bearing" not in saved
    assert json.loads(saved)["attempts"] == [{"number": 1}]


def test_unknown_prior_run_charges_full_ceilings(tmp_path: Path) -> None:
    from evals.live import check_local_prior_usage

    proposal = plan()
    old = tmp_path / "old"
    old.mkdir()
    (old / "receipt.json").write_text(
        json.dumps(
            {
                "plan": proposal.model_dump(mode="json"),
                "started_at": (datetime.now(UTC) - timedelta(minutes=10)).isoformat(),
            }
        )
    )
    with pytest.raises(ValueError, match="prior usage"):
        check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))
    proposal = proposal.model_copy(
        update={"budget": budget(prior_requests_today=3, prior_tokens_today=18300)}
    )
    check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))


def pipeline_budget() -> Budget:
    limits = {
        "max_attempts": 5,
        "input_tokens": 100000,
        "output_tokens": 5120,
        "per_call_input": 20000,
        "per_call_output": 1024,
    }
    return budget(
        models={"openai/gpt-oss-120b": limits, "openai/gpt-oss-20b": limits},
        shared_tpm=50000,
        shared_tpd=1000000,
    )


def save_completed_receipt(
    directory: Path, started: datetime, finished: datetime
) -> None:
    old = directory / "prior"
    old.mkdir()
    (old / "receipt.json").write_text(
        json.dumps(
            {"plan": plan().model_dump(mode="json"), "started_at": started.isoformat()}
        )
    )
    (old / "result.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "finished_at": finished.isoformat(),
                "attempts": [
                    {
                        "reserved_input": 6000,
                        "reserved_output": 100,
                        "usage": {"total_tokens": 25},
                    }
                ],
            }
        )
    )


def test_completed_local_run_requires_minute_cooldown(tmp_path: Path) -> None:
    from evals.live import check_local_prior_usage

    now = datetime.now(UTC)
    save_completed_receipt(
        tmp_path, now - timedelta(seconds=5), now - timedelta(seconds=1)
    )
    proposal = plan().model_copy(
        update={"budget": budget(prior_requests_today=1, prior_tokens_today=6100)}
    )
    with pytest.raises(ValueError, match="cooldown"):
        check_local_prior_usage(proposal, tmp_path, now)


def test_prior_run_crossing_utc_midnight_counts_on_both_days(tmp_path: Path) -> None:
    from evals.live import check_local_prior_usage

    now = datetime(2026, 11, 4, 0, 3, tzinfo=UTC)
    save_completed_receipt(
        tmp_path, now - timedelta(minutes=4), now - timedelta(minutes=2)
    )
    with pytest.raises(ValueError, match="prior usage"):
        check_local_prior_usage(plan(), tmp_path, now)


def stopped_run(directory: Path) -> Path:
    from evals.budget import Attempt

    old = directory / "test-run"
    old.mkdir()
    proposal = plan()
    now = datetime.now(UTC)
    receipt = {
        "plan": proposal.model_dump(mode="json"),
        "started_at": (now - timedelta(minutes=10)).isoformat(),
        "approval": approval(proposal)
        .model_copy(update={"approved_at": now - timedelta(minutes=11)})
        .model_dump(mode="json"),
    }
    rows = [
        Attempt(
            number=1,
            task_id="case",
            model="openai/gpt-oss-120b",
            start_seconds=0,
            reserved_input=6000,
            reserved_output=100,
            request_sha256="0" * 64,
            status="reported",
            usage=Usage(prompt_tokens=20, completion_tokens=5, total_tokens=25),
            reported_model="openai/gpt-oss-120b",
            finished_seconds=1,
        ).model_dump(mode="json")
    ]
    result = {
        "kind": "live_eval_attempts",
        "plan_sha256": canonical_sha256(receipt["plan"]),
        "status": "stopped",
        "stop_reason": "incomplete_provider_output",
        "finished_at": (now - timedelta(minutes=5)).isoformat(),
        "attempts": rows,
        "ledger_sha256": canonical_sha256(rows),
    }
    (old / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    (old / "result.json").write_text(json.dumps(result), encoding="utf-8")
    return old


def test_explicit_known_stop_reconciliation_keeps_attempt_reservations(
    tmp_path: Path,
) -> None:
    from evals.live import build_known_stop_reconciliation, check_local_prior_usage

    old = stopped_run(tmp_path)
    original = [(old / name).read_bytes() for name in ("receipt.json", "result.json")]
    proposal = plan().model_copy(
        update={"budget": budget(prior_requests_today=1, prior_tokens_today=6100)}
    )
    with pytest.raises(ValueError, match="prior usage"):
        check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))
    record = build_known_stop_reconciliation(
        old,
        actor="TEST ONLY",
        reference="TEST ONLY explicit reconciliation",
        process_exit_verified=True,
    )
    assert record.charged_reserved_tokens == 6100
    assert record.reported_tokens == 25
    (old / "reconciliation.json").write_text(record.model_dump_json(), encoding="utf-8")
    check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))
    assert original == [
        (old / name).read_bytes() for name in ("receipt.json", "result.json")
    ]


@pytest.mark.parametrize(
    "reason", ["incomplete_provider_output", "task_error_or_deadline"]
)
def test_explicit_actual_usage_reconciliation(tmp_path: Path, reason: str) -> None:
    from evals.live import build_known_stop_reconciliation, check_local_prior_usage

    old = stopped_run(tmp_path)
    result = json.loads((old / "result.json").read_text())
    result["stop_reason"] = reason
    (old / "result.json").write_text(json.dumps(result))
    original = [(old / name).read_bytes() for name in ("receipt.json", "result.json")]
    proposal = plan().model_copy(
        update={
            "budget": budget(
                prior_requests_today=1,
                prior_tokens_today=25,
                visitor_rpm=0,
                visitor_tpm=0,
                visitor_rpd=0,
                visitor_tpd=0,
            )
        }
    )
    with pytest.raises(ValueError, match="prior usage"):
        check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))
    record = build_known_stop_reconciliation(
        old,
        actor="TEST ONLY",
        reference="TEST ONLY explicit actual-usage approval",
        process_exit_verified=True,
        actual_usage=True,
    )
    assert record.purpose == "explicit_reported_actual_usage"
    assert record.charged_reserved_tokens == 6100
    assert record.reported_tokens == 25
    path = old / "actual-usage-reconciliation.json"
    path.write_text(record.model_dump_json())
    check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))
    assert original == [
        (old / name).read_bytes() for name in ("receipt.json", "result.json")
    ]
    forged = record.model_dump(mode="json")
    forged["reported_tokens"] = 1
    path.write_text(json.dumps(forged))
    with pytest.raises(ValueError):
        check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))


def test_explicit_partial_reconciliation_keeps_unknown_reservation(
    tmp_path: Path,
) -> None:
    from evals.live import build_known_stop_reconciliation, check_local_prior_usage

    old = stopped_run(tmp_path)
    data = json.loads((old / "result.json").read_text())
    known = data["attempts"][0]
    data["attempts"].append(
        dict(
            known,
            number=2,
            start_seconds=2,
            status="unknown",
            usage=None,
            reported_model=None,
            finished_seconds=None,
        )
    )
    data["stop_reason"] = "provider_consumption_unknown"
    data["ledger_sha256"] = canonical_sha256(data["attempts"])
    (old / "result.json").write_text(json.dumps(data))
    original = (old / "result.json").read_bytes()
    record = build_known_stop_reconciliation(
        old,
        actor="TEST ONLY",
        reference="TEST ONLY actual-known plus reserved-unknown approval",
        process_exit_verified=True,
        actual_usage=True,
        preserve_unknown=True,
    )
    assert record.reported_tokens == 25
    assert record.unreported_reserved_tokens == 6100
    assert record.charged_reserved_tokens == 12200
    (old / "actual-usage-reconciliation.json").write_text(record.model_dump_json())
    proposal = plan().model_copy(
        update={"budget": budget(prior_requests_today=2, prior_tokens_today=6125)}
    )
    check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))
    with pytest.raises(ValueError, match="prior usage"):
        check_local_prior_usage(
            proposal.model_copy(
                update={"budget": budget(prior_requests_today=2, prior_tokens_today=25)}
            ),
            tmp_path,
            datetime.now(UTC),
        )
    assert (old / "result.json").read_bytes() == original


@pytest.mark.parametrize("fault", [None, "missing_recovery", "false_usage", "bad_time"])
def test_completed_recovery_reconciliation_preserves_unknowns(
    tmp_path: Path, fault: str | None
) -> None:
    from evals.live import build_known_stop_reconciliation, check_local_prior_usage

    old = stopped_run(tmp_path)
    receipt = json.loads((old / "receipt.json").read_text())
    receipt["plan"]["judge_recovery_attempts"] = 1
    receipt["approval"]["plan_sha256"] = canonical_sha256(receipt["plan"])
    (old / "receipt.json").write_text(json.dumps(receipt))
    data = json.loads((old / "result.json").read_text())
    good = data["attempts"][0]
    data.update(
        status="complete",
        stop_reason=None,
        plan_sha256=canonical_sha256(receipt["plan"]),
        recoveries=[
            {
                "attempt_number": 1,
                "task_id": good["task_id"],
                "reason": "provider_consumption_unknown",
            }
        ],
    )
    unknown = dict(good, status="unknown", usage=None, reported_model=None)
    data["attempts"] = [
        unknown,
        dict(good, number=2, start_seconds=2, finished_seconds=3),
    ]
    if fault == "missing_recovery":
        data["recoveries"] = []
    if fault == "false_usage":
        data["attempts"][0]["usage"] = good["usage"]
    if fault == "bad_time":
        data["attempts"][0]["finished_seconds"] = 4
    data["ledger_sha256"] = canonical_sha256(data["attempts"])
    (old / "result.json").write_text(json.dumps(data))
    if fault:
        with pytest.raises(ValueError):
            build_known_stop_reconciliation(
                old,
                actor="TEST ONLY",
                reference="TEST ONLY",
                process_exit_verified=True,
                actual_usage=True,
                preserve_unknown=True,
            )
        return
    rec = build_known_stop_reconciliation(
        old,
        actor="TEST ONLY",
        reference="TEST ONLY explicit actual accounting",
        process_exit_verified=True,
        actual_usage=True,
        preserve_unknown=True,
    )
    assert rec.reported_tokens == 25 and rec.unreported_reserved_tokens == 6100
    (old / "actual-usage-reconciliation.json").write_text(rec.model_dump_json())
    check_local_prior_usage(
        plan().model_copy(
            update={"budget": budget(prior_requests_today=2, prior_tokens_today=6125)}
        ),
        tmp_path,
        datetime.now(UTC),
    )


@pytest.mark.parametrize(
    "fault",
    [
        "unknown",
        "missing_usage",
        "usage_total",
        "wrong_reason",
        "no_attempts",
        "over_reservation",
        "duplicate_number",
        "plan_binding",
        "approval_binding",
        "reversed_wall",
        "negative_start",
        "reversed_attempt",
        "overlap",
    ],
)
@pytest.mark.parametrize(
    "actual_usage,preserve_unknown", [(False, False), (True, False), (True, True)]
)
def test_uncertain_stopped_runs_cannot_be_reconciled(
    tmp_path: Path, fault: str, actual_usage: bool, preserve_unknown: bool
) -> None:
    from evals.live import build_known_stop_reconciliation

    old = stopped_run(tmp_path)
    result = json.loads((old / "result.json").read_text())
    if fault == "unknown":
        result["attempts"][0]["status"] = "unknown"
    if fault == "missing_usage":
        result["attempts"][0]["usage"] = None
    if fault == "usage_total":
        result["attempts"][0]["usage"]["total_tokens"] = 99
    if fault == "wrong_reason":
        result["stop_reason"] = "client_lifecycle_or_consumption_unknown"
    if fault == "no_attempts":
        result["attempts"] = []
    if fault == "over_reservation":
        result["attempts"][0]["usage"] = {
            "prompt_tokens": 7000,
            "completion_tokens": 5,
            "total_tokens": 7005,
        }
    if fault == "duplicate_number":
        result["attempts"].append(result["attempts"][0])
    if fault == "plan_binding":
        result["plan_sha256"] = "0" * 64
    if fault == "approval_binding":
        receipt = json.loads((old / "receipt.json").read_text())
        receipt["approval"]["plan_sha256"] = "0" * 64
        (old / "receipt.json").write_text(json.dumps(receipt))
    if fault == "reversed_wall":
        result["finished_at"] = "2000-01-01T00:00:00+00:00"
    if fault == "negative_start":
        result["attempts"][0]["start_seconds"] = -1
    if fault == "reversed_attempt":
        result["attempts"][0]["start_seconds"] = 2
    if fault == "overlap":
        overlap = dict(
            result["attempts"][0], number=2, start_seconds=0.5, finished_seconds=1.5
        )
        result["attempts"].append(overlap)
    result["ledger_sha256"] = canonical_sha256(result["attempts"])
    (old / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError):
        build_known_stop_reconciliation(
            old,
            actor="TEST ONLY",
            reference="TEST ONLY",
            process_exit_verified=True,
            actual_usage=actual_usage,
            preserve_unknown=preserve_unknown,
        )


def test_stale_reconciliation_and_cooldown_fail_closed(tmp_path: Path) -> None:
    from evals.live import build_known_stop_reconciliation, check_local_prior_usage

    old = stopped_run(tmp_path)
    record = build_known_stop_reconciliation(
        old, actor="TEST ONLY", reference="TEST ONLY", process_exit_verified=True
    )
    (old / "reconciliation.json").write_text(record.model_dump_json(), encoding="utf-8")
    result = json.loads((old / "result.json").read_text())
    result["finished_at"] = datetime.now(UTC).isoformat()
    (old / "result.json").write_text(json.dumps(result), encoding="utf-8")
    proposal = plan().model_copy(
        update={"budget": budget(prior_requests_today=1, prior_tokens_today=6100)}
    )
    with pytest.raises(ValueError):
        check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))
    record = build_known_stop_reconciliation(
        old, actor="TEST ONLY", reference="TEST ONLY", process_exit_verified=True
    )
    (old / "reconciliation.json").write_text(record.model_dump_json(), encoding="utf-8")
    with pytest.raises(ValueError, match="cooldown"):
        check_local_prior_usage(proposal, tmp_path, datetime.now(UTC))


@pytest.mark.parametrize(
    "fault", ["active", "unverified_exit", "forged_charge", "ledger_hash"]
)
def test_reconciliation_requires_explicit_proof(tmp_path: Path, fault: str) -> None:
    from evals.live import build_known_stop_reconciliation, check_local_prior_usage

    old = stopped_run(tmp_path)
    if fault == "active":
        (tmp_path / "active.lock").write_text("runner still active")
    if fault == "ledger_hash":
        result = json.loads((old / "result.json").read_text())
        result["ledger_sha256"] = "0" * 64
        (old / "result.json").write_text(json.dumps(result))
    if fault != "forged_charge":
        with pytest.raises(ValueError):
            build_known_stop_reconciliation(
                old,
                actor="TEST ONLY",
                reference="TEST ONLY",
                process_exit_verified=fault != "unverified_exit",
            )
        return
    record = build_known_stop_reconciliation(
        old, actor="TEST ONLY", reference="TEST ONLY", process_exit_verified=True
    )
    data = record.model_dump(mode="json")
    data["charged_reserved_tokens"] = 25
    (old / "reconciliation.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="reservations"):
        check_local_prior_usage(plan(), tmp_path, datetime.now(UTC))


class ScriptProvider(Provider):
    def __init__(
        self, replies: list[str], *, tool_turn: int | None = None, failure: str = ""
    ) -> None:
        super().__init__(failure)
        self.replies = replies
        self.tool_turn = tool_turn

    async def complete(self, request: ProviderRequest) -> ProviderReply:
        from app.llm import ToolCall

        reply = await super().complete(request)
        tools = (
            [
                ToolCall(
                    id="call-test",
                    name="show_project_card",
                    arguments='{"project_id":"entropy-oj"}',
                )
            ]
            if self.calls == self.tool_turn
            else []
        )
        return reply.model_copy(
            update={
                "content": self.replies[self.calls - 1],
                "tool_calls": tools,
                "finish_reason": "tool_calls" if tools else "stop",
            }
        )


def inject_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    import evals.live as live

    clock = Clock()
    monkeypatch.setattr(
        live,
        "MeteredLLM",
        lambda provider, limits, default_model, reasoning_effort=None: MeteredLLM(
            provider,
            limits,
            default_model=default_model,
            reasoning_effort=reasoning_effort,
            clock=clock,
            sleep=clock.sleep,
        ),
    )


@pytest.mark.asyncio
async def test_judge_run_uses_explicit_settings_without_human_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.live as live
    from evals.calibration import JudgeConfiguration

    inject_clock(monkeypatch)
    reply = json.dumps(
        {
            "labels": {
                k: "pass" for k in ("support", "completeness", "behavior", "tone")
            },
            "rationale": "TEST ONLY synthetic judge output.",
        }
    )
    provider = ScriptProvider([reply] * 20)
    limits = {
        "max_attempts": 20,
        "input_tokens": 139520,
        "output_tokens": 20480,
        "per_call_input": 6976,
        "per_call_output": 1024,
    }
    proposal = LivePlan(
        run_id="test-judge",
        stage="judge_calibration",
        case_ids=[],
        budget=budget(
            models={"openai/gpt-oss-20b": limits},
            deadline_seconds=2700,
            visitor_tpm=0,
        ),
        source={"dirty": False},
        inputs_sha256="test-only",
        judge_configuration=JudgeConfiguration(max_completion_tokens=1024),
    )
    report = await live.run_jobs(proposal, provider)
    assert report["status"] == "complete"
    assert len(report["reviews"]) == provider.calls == 20
    assert report["judge_configuration"]["reasoning_effort"] == "low"
    assert all(
        r.reasoning_effort == "low" and r.max_completion_tokens == 1024
        for r in provider.requests
    )
    assert all(a["finish_reason"] == "stop" for a in report["attempts"])
    from evals.calibration import effective_judge_prompt_sha256

    assert report["effective_prompt_sha256"] == effective_judge_prompt_sha256()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_kind", ["contract", "transient", "auth"])
async def test_explicit_judge_recovery_preserves_budget_and_attempts(
    monkeypatch: pytest.MonkeyPatch, failure_kind: str
) -> None:
    import httpx
    from groq import APIStatusError

    import evals.live as live
    from evals.calibration import JudgeConfiguration

    inject_clock(monkeypatch)
    good = json.dumps(
        {
            "labels": {
                k: "pass" for k in ("support", "completeness", "behavior", "tone")
            },
            "rationale": "TEST ONLY fake reasons.",
        }
    )

    class Recovering(ScriptProvider):
        async def complete(self, request: ProviderRequest) -> ProviderReply:
            if failure_kind != "contract" and self.calls < 2:
                await Provider.complete(self, request)
                raise APIStatusError(
                    "secret-bearing message",
                    response=httpx.Response(
                        401 if failure_kind == "auth" else 400,
                        request=httpx.Request("POST", "https://example.invalid"),
                    ),
                    body={"error": {"code": "json_validate_failed"}},
                )
            return await super().complete(request)

    provider = Recovering(["bad JSON"] * 2 + [good] * 20)
    limits = {
        "max_attempts": 24,
        "input_tokens": 135424,
        "output_tokens": 24576,
        "per_call_input": 6976,
        "per_call_output": 1024,
    }
    proposal = LivePlan(
        run_id="test-recovery",
        stage="judge_calibration",
        budget=budget(
            models={"openai/gpt-oss-20b": limits},
            input_reservation="request_bound",
            visitor_tpm=0,
            deadline_seconds=2700,
        ),
        source={"dirty": False},
        inputs_sha256="TEST ONLY",
        judge_configuration=JudgeConfiguration(max_completion_tokens=1024),
        judge_recovery_attempts=4,
    )
    result = await live.run_jobs(proposal, provider)
    assert result["status"] == ("stopped" if failure_kind == "auth" else "complete")
    assert provider.calls == (1 if failure_kind == "auth" else 22)
    assert len(result["reviews"]) == (0 if failure_kind == "auth" else 20)
    assert len(result["recoveries"]) == (0 if failure_kind == "auth" else 2)
    assert sum(x["reserved_input"] for x in result["attempts"]) <= 135424
    assert sum(x["reserved_output"] for x in result["attempts"]) <= 24576
    assert "secret-bearing" not in json.dumps(result)
    if failure_kind == "transient":
        assert all(
            x["usage"] is None and x["status"] == "unknown"
            for x in result["attempts"][:2]
        )
        assert all(x["reserved_input"] > 0 for x in result["attempts"][:2])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        '{"support":"pass"}',
        '{"labels":{"support":"pass","completeness":"pass","behavior":"pass","tone":"pass"},"rationale":{"support":"explanation"}}',
        "not JSON",
    ],
)
async def test_bad_judge_contract_retains_diagnostics(
    monkeypatch: pytest.MonkeyPatch, payload: str
) -> None:
    import evals.live as live
    from evals.calibration import JudgeConfiguration

    inject_clock(monkeypatch)
    provider = ScriptProvider([payload])
    limits = {
        "max_attempts": 20,
        "input_tokens": 139520,
        "output_tokens": 20480,
        "per_call_input": 6976,
        "per_call_output": 1024,
    }
    proposal = LivePlan(
        run_id="test-diagnostics",
        stage="judge_calibration",
        budget=budget(
            models={"openai/gpt-oss-20b": limits},
            deadline_seconds=2700,
            visitor_tpm=0,
        ),
        source={"dirty": False},
        inputs_sha256="TEST ONLY",
        judge_configuration=JudgeConfiguration(max_completion_tokens=1024),
    )
    result = await live.run_jobs(proposal, provider)
    assert result["status"] == "stopped"
    assert result["stop_reason"] == "judge_contract_error"
    assert result["failure"]["error_type"] == "ValidationError"
    assert result["failed_judge_outputs"][0]["output"] == payload
    assert all(
        "input" not in issue and "ctx" not in issue
        for issue in result["failure"]["issues"]
    )
    assert provider.calls == 1
    assert result["reviews"] == []


def test_validation_cannot_mix_judge_output_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.live as live
    from evals.calibration import (
        AnnotationSet,
        JudgeConfiguration,
        JudgeSet,
        Labels,
        Review,
        effective_judge_prompt_sha256,
        load_packet,
        packet_fingerprint,
    )

    packet = load_packet()
    rows = [
        Review(
            item_id=x.id,
            item_sha256=x.sha256,
            labels=Labels(
                support="pass", completeness="pass", behavior="pass", tone="pass"
            ),
            rationale="TEST ONLY",
        )
        for x in packet.items
    ]
    human = AnnotationSet(
        packet_sha256=packet_fingerprint(packet),
        rubric_sha256=packet.rubric_sha256,
        reviewer="TEST ONLY",
        attestation="TEST ONLY",
        reviews=rows,
    )
    cal_ids = {x.id for x in packet.items if x.slice == "calibration"}
    prior = JudgeSet(
        packet_sha256=packet_fingerprint(packet),
        rubric_sha256=packet.rubric_sha256,
        prompt_sha256=packet.judge_prompt_sha256,
        effective_prompt_sha256=effective_judge_prompt_sha256(),
        configuration=JudgeConfiguration(max_completion_tokens=512),
        origin="live",
        model="openai/gpt-oss-20b",
        authorization_reference="TEST ONLY",
        ledger_sha256="0" * 64,
        reviews=[r for r in rows if r.item_id in cal_ids],
    )
    limits = {
        "max_attempts": 8,
        "input_tokens": 56000,
        "output_tokens": 2048,
        "per_call_input": 7000,
        "per_call_output": 256,
    }
    proposal = LivePlan(
        run_id="test-validation",
        stage="judge_validation",
        budget=budget(
            models={"openai/gpt-oss-20b": limits},
            deadline_seconds=2700,
            visitor_tpm=400,
        ),
        source={"dirty": False},
        inputs_sha256=canonical_sha256(
            inputs_state("judge_validation", [], human, prior)
        ),
        judge_configuration=JudgeConfiguration(max_completion_tokens=256),
    )
    monkeypatch.setattr(live, "source_state", lambda: proposal.source)
    with pytest.raises(ValueError, match="same judge settings"):
        live.preflight(proposal, human=human, prior=prior)


@pytest.mark.asyncio
async def test_real_chat_rewrite_and_both_tool_turns_share_one_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.live as live
    from app.retrieval.loader import FactLoader
    from app.retrieval.retriever import FakeRetriever

    inject_clock(monkeypatch)
    provider = ScriptProvider(
        ["Entropy-OJ Redis BullMQ queue design", "", "Aamir uses Redis and BullMQ."],
        tool_turn=2,
    )
    proposal = plan().model_copy(
        update={"case_ids": ["followup-entropy-stack"], "budget": pipeline_budget()}
    )
    facts = [
        f
        for f in FactLoader().load_all()
        if f.id in {"proj-entropy-oj-stack", "proj-entropy-oj-design"}
    ]
    report = await live.run_jobs(
        proposal, provider, retriever=FakeRetriever(default_facts=facts)
    )
    assert report["status"] == "complete"
    assert provider.calls == len(report["attempts"]) == 3
    assert [a["model"] for a in report["attempts"]] == [
        "openai/gpt-oss-20b",  # Coreference rewrite uses the utility model.
        "openai/gpt-oss-120b",
        "openai/gpt-oss-120b",
    ]
    assert report["results"][0]["output"]["cards"]
    assert (
        report["results"][0]["retrieval"][0]["query"]
        == "Entropy-OJ Redis BullMQ queue design"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("unknown_usage", [False, True])
async def test_fit_retries_count_and_uncertainty_stops_fallback(
    monkeypatch: pytest.MonkeyPatch, unknown_usage: bool
) -> None:
    import evals.live as live
    from app.retrieval.retriever import FakeRetriever

    inject_clock(monkeypatch)
    provider = ScriptProvider(
        ["invalid JSON", "invalid JSON"], failure="error" if unknown_usage else ""
    )
    proposal = plan().model_copy(
        update={"case_ids": ["fit-cloud-negative"], "budget": pipeline_budget()}
    )
    report = await live.run_jobs(proposal, provider, retriever=FakeRetriever())
    assert report["status"] == "stopped"
    assert provider.calls == len(report["attempts"]) == (1 if unknown_usage else 2)
    assert all(a["model"] == "openai/gpt-oss-20b" for a in report["attempts"])
    assert report["results"] == []


@pytest.mark.asyncio
async def test_fit_extraction_alignment_and_deterministic_gap_summary_are_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.live as live
    from app.retrieval.loader import FactLoader
    from app.retrieval.retriever import FakeRetriever

    inject_clock(monkeypatch)
    provider = ScriptProvider(
        [
            json.dumps(
                {
                    "role_title": "Test only",
                    "requirements": [
                        {
                            "id": "aws",
                            "text": "Production AWS operations",
                            "importance": "must_have",
                            "type": "skill",
                        }
                    ],
                }
            ),
            json.dumps(
                {
                    "judged": [
                        {
                            "requirement_id": "aws",
                            "verdict": "gap",
                            "evidence_chunk_ids": ["skill-not-claimed"],
                            "explanation": "Hands-on AWS not established.",
                        }
                    ]
                }
            ),
        ]
    )
    proposal = plan().model_copy(
        update={"case_ids": ["fit-cloud-negative"], "budget": pipeline_budget()}
    )
    facts = [f for f in FactLoader().load_all() if f.id == "skill-not-claimed"]
    first = await live.run_jobs(
        proposal, provider, retriever=FakeRetriever(default_facts=facts)
    )
    assert first["status"] == "complete"
    assert [a["model"] for a in first["attempts"]] == [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
    ]
    assert provider.calls == 2  # A gap summary requires no semantic generation.
    assert first["results"][0]["output"]["requirements"][0]["verdict"] == "gap"
    assert not first["results"][0]["output"]["cached"]
    second_provider = ScriptProvider(provider.replies)
    second = await live.run_jobs(
        proposal, second_provider, retriever=FakeRetriever(default_facts=facts)
    )
    assert second["status"] == "complete"
    assert second_provider.calls == 2


@pytest.mark.asyncio
async def test_guardrail_origin_and_expiry_deadline() -> None:
    import evals.live as live
    from app.retrieval.retriever import FakeRetriever

    provider = Provider()
    proposal = plan().model_copy(update={"case_ids": ["persona-override"]})
    report = await live.run_jobs(
        proposal,
        provider,
        retriever=FakeRetriever(),
        authorization_expires_at=datetime.now(UTC) + timedelta(seconds=1),
    )
    assert report["status"] == "complete"
    assert report["runtime_deadline_seconds"] <= 1
    assert report["results"][0]["origin"] == "guardrail"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_runtime_deadline_stops_at_utc_day_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evals.live as live
    from app.retrieval.retriever import FakeRetriever

    class NearMidnight(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            return datetime(2026, 11, 4, 23, 59, 59, tzinfo=UTC)

    monkeypatch.setattr(live, "datetime", NearMidnight)
    provider = Provider()
    proposal = plan().model_copy(update={"case_ids": ["persona-override"]})
    report = await live.run_jobs(proposal, provider, retriever=FakeRetriever())
    assert report["runtime_deadline_seconds"] == 1
    assert report["status"] == "complete"
    assert provider.calls == 0


@pytest.mark.asyncio
async def test_eval_client_pins_host_disables_retries_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import groq

    from evals.live import live_provider

    options: dict[str, Any] = {}
    closed = False

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            options.update(kwargs)

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *args: Any) -> None:
            nonlocal closed
            closed = True

    monkeypatch.setenv("GROQ_API_KEY", "fake-test-key")
    monkeypatch.setenv("GROQ_BASE_URL", "https://invalid.test")
    monkeypatch.setattr(groq, "AsyncGroq", FakeClient)
    async with live_provider():
        assert options["base_url"] == "https://api.groq.com"
        assert options["max_retries"] == 0
    assert closed


@pytest.mark.asyncio
async def test_cancellation_keeps_unknown_reservation_and_stops_reuse() -> None:
    class CancelProvider(Provider):
        async def complete(self, request: ProviderRequest) -> ProviderReply:
            self.calls += 1
            raise asyncio.CancelledError()

    clock, provider = Clock(), CancelProvider()
    llm = MeteredLLM(provider, budget(), clock=clock, sleep=clock.sleep)
    with pytest.raises(asyncio.CancelledError):
        await llm.complete([])
    assert llm.attempts[0].status == "unknown"
    with pytest.raises(BudgetStop):
        await llm.complete([])
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_concurrent_callers_share_one_reservation_ledger() -> None:
    clock, provider = Clock(), Provider()
    llm = MeteredLLM(provider, budget(), clock=clock, sleep=clock.sleep)
    outcomes = await asyncio.gather(
        *(llm.complete([]) for _ in range(4)), return_exceptions=True
    )
    assert provider.calls == 3
    assert sum(isinstance(x, BudgetStop) for x in outcomes) == 1
    assert [a.number for a in llm.attempts] == [1, 2, 3]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [200, 429])
@pytest.mark.parametrize("item20", [False, True])
async def test_actual_sdk_adapter_uses_mock_transport_without_hidden_retries(
    status: int,
    item20: bool,
) -> None:
    import httpx
    from groq import AsyncGroq

    from evals.calibration import load_packet
    from evals.live import GroqProvider, judge_messages, judge_response_format

    messages = judge_messages(load_packet(), "calibration-20") if item20 else []

    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        assert body["max_completion_tokens"] == (1024 if item20 else 100)
        assert body["stream"] is False
        assert body["reasoning_effort"] == "low"
        if item20:
            assert body["response_format"] == judge_response_format()
            schema = body["response_format"]["json_schema"]
            assert schema["strict"] is True
            assert schema["schema"]["required"] == ["labels", "rationale"]
            assert schema["schema"]["additionalProperties"] is False
            assert body["model"] == "openai/gpt-oss-20b"
            assert "reasoning_format" not in body and "tools" not in body
            item = next(i for i in load_packet().items if i.id == "calibration-20")
            data = json.loads(body["messages"][1]["content"])
            assert data["answer"] == item.answer
            assert data["evidence"] == [e.model_dump() for e in item.evidence]
            assert "labels" not in data
        if status == 429:
            return httpx.Response(429, json={"error": {"message": "synthetic"}})
        return httpx.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 0,
                "model": body["model"],
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "ok"},
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            },
        )

    clock = Clock()
    async with AsyncGroq(
        api_key="fake-test-key",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    ) as client:
        llm = MeteredLLM(
            GroqProvider(client),
            budget(
                models={
                    "openai/gpt-oss-20b": {
                        "max_attempts": 1,
                        "input_tokens": 6976,
                        "output_tokens": 1024,
                        "per_call_input": 6976,
                        "per_call_output": 1024,
                    }
                },
                visitor_tpm=0,
            )
            if item20
            else budget(),
            clock=clock,
            sleep=clock.sleep,
            reasoning_effort="low",
        )
        if status == 429:
            with pytest.raises(BudgetStop):
                await llm.complete(
                    messages,
                    model="openai/gpt-oss-20b" if item20 else None,
                    response_format=judge_response_format() if item20 else None,
                )
            assert llm.attempts[0].usage is None
        else:
            assert (
                await llm.complete(
                    messages,
                    model="openai/gpt-oss-20b" if item20 else None,
                    response_format=judge_response_format() if item20 else None,
                )
            ).content == "ok"
    assert calls == 1
