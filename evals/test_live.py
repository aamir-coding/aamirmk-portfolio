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
            [Message(role="user", content="🧪" * 1400)],
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
        lambda provider, limits, default_model: MeteredLLM(
            provider,
            limits,
            default_model=default_model,
            clock=clock,
            sleep=clock.sleep,
        ),
    )


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
    assert all(a["model"] == "openai/gpt-oss-120b" for a in report["attempts"])
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
async def test_fit_extraction_alignment_and_summary_use_isolated_real_pipeline(
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
            "Hands-on AWS operations remain a gap.",
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
        "openai/gpt-oss-120b",
    ]
    assert not first["results"][0]["output"]["cached"]
    second_provider = ScriptProvider(provider.replies)
    second = await live.run_jobs(
        proposal, second_provider, retriever=FakeRetriever(default_facts=facts)
    )
    assert second["status"] == "complete"
    assert second_provider.calls == 3


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
async def test_actual_sdk_adapter_uses_mock_transport_without_hidden_retries(
    status: int,
) -> None:
    import httpx
    from groq import AsyncGroq

    from evals.live import GroqProvider

    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        assert body["max_completion_tokens"] == 100
        assert body["stream"] is False
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
        llm = MeteredLLM(GroqProvider(client), budget(), clock=clock, sleep=clock.sleep)
        if status == 429:
            with pytest.raises(BudgetStop):
                await llm.complete([])
            assert llm.attempts[0].usage is None
        else:
            assert (await llm.complete([])).content == "ok"
    assert calls == 1
