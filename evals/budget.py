"""Per-attempt conservative admission for the standalone eval runner only."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import asdict
from typing import Any, Literal, Protocol, Self

from pydantic import Field, model_validator

from app.llm import AssistantMessage, Message, ToolCall, normalize_llm_text
from evals.checks import ReplayModel

MAIN = "openai/gpt-oss-120b"
UTILITY = "openai/gpt-oss-20b"
Model = Literal["openai/gpt-oss-120b", "openai/gpt-oss-20b"]


class ModelBudget(ReplayModel):
    max_attempts: int = Field(gt=0, strict=True)
    input_tokens: int = Field(gt=0, strict=True)
    output_tokens: int = Field(gt=0, strict=True)
    per_call_input: int = Field(gt=0, strict=True)
    per_call_output: int = Field(gt=0, le=1024, strict=True)


class Budget(ReplayModel):
    input_reservation: Literal["full_cap", "request_bound"] = "full_cap"
    models: dict[Model, ModelBudget] = Field(min_length=1)
    shared_rpm: int = Field(gt=0, strict=True)
    shared_tpm: int = Field(gt=0, strict=True)
    shared_rpd: int = Field(gt=0, strict=True)
    shared_tpd: int = Field(gt=0, strict=True)
    prior_requests_today: int = Field(ge=0, strict=True)
    prior_tokens_today: int = Field(ge=0, strict=True)
    visitor_rpm: int = Field(ge=0, strict=True)
    visitor_tpm: int = Field(ge=0, strict=True)
    visitor_rpd: int = Field(ge=0, strict=True)
    visitor_tpd: int = Field(ge=0, strict=True)
    min_interval_seconds: float = Field(gt=0)
    deadline_seconds: float = Field(gt=0, le=3600)
    request_timeout_seconds: float = Field(gt=0, le=60)

    @model_validator(mode="after")
    def conservative_allowance(self) -> Self:
        if self.visitor_rpm >= self.shared_rpm or self.visitor_tpm >= self.shared_tpm:
            raise ValueError("Minute visitor allowance leaves no eval capacity")
        if (
            sum(b.max_attempts for b in self.models.values())
            + self.visitor_rpd
            + self.prior_requests_today
            > self.shared_rpd
        ):
            raise ValueError(
                "Run attempts plus visitor headroom exceed daily allowance"
            )
        if (
            sum(b.input_tokens + b.output_tokens for b in self.models.values())
            + self.visitor_tpd
            + self.prior_tokens_today
            > self.shared_tpd
        ):
            raise ValueError(
                "Run token ceilings plus visitor headroom exceed daily allowance"
            )
        if any(
            b.per_call_input > b.input_tokens
            or b.per_call_output > b.output_tokens
            or b.per_call_input + b.per_call_output > self.shared_tpm - self.visitor_tpm
            for b in self.models.values()
        ):
            raise ValueError(
                "A single full reservation exceeds the run/minute allowance"
            )
        return self


class Usage(ReplayModel):
    prompt_tokens: int = Field(ge=0, strict=True)
    completion_tokens: int = Field(ge=0, strict=True)
    total_tokens: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def reconciles(self) -> Self:
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("Reported total usage does not reconcile")
        return self


class ProviderRequest(ReplayModel):
    model: Model
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] | None
    response_format: dict[str, Any] | None
    max_completion_tokens: int
    timeout_seconds: float
    reasoning_effort: Literal["low"] | None = None


class ProviderReply(ReplayModel):
    content: str
    model: str
    usage: Usage | None
    finish_reason: str
    tool_calls: list[ToolCall] = Field(default_factory=list)


class CompletionProvider(Protocol):
    async def complete(self, request: ProviderRequest) -> ProviderReply: ...


class ProviderFailure(ReplayModel):
    exception_type: str
    status_code: int | None = Field(default=None, ge=100, le=599, strict=True)
    code: (
        Literal[
            "json_validate_failed", "context_length_exceeded", "rate_limit_exceeded"
        ]
        | None
    ) = None


class Attempt(ReplayModel):
    number: int
    task_id: str
    model: str
    start_seconds: float
    reserved_input: int
    reserved_output: int
    request_sha256: str
    status: Literal["reserved", "reported", "unknown"] = "reserved"
    usage: Usage | None = None
    reported_model: str | None = None
    finished_seconds: float | None = None
    finish_reason: str | None = None
    provider_error: ProviderFailure | None = None


class BudgetStop(RuntimeError):
    """Safe reason codes only; never propagate secret-bearing provider messages."""


def request_payload(
    messages: list[Message],
    tools: list[dict[str, Any]] | None = None,
    response_format: dict[str, Any] | None = None,
) -> dict[str, Any]:
    formatted = []
    for message in messages:
        data = {k: v for k, v in asdict(message).items() if v is not None}
        if message.tool_calls is not None:
            data["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments,
                    },
                }
                for tc in message.tool_calls
            ]
        formatted.append(data)
    return {"messages": formatted, "tools": tools, "response_format": response_format}


def input_reservation_bound(payload: dict[str, Any]) -> int:
    return (
        len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        + 1024
        + 64 * len(payload["messages"])
    )


class MeteredLLM:
    """All production completion paths cross this one sequential admission seam.

    Reservations are never refunded, even after known usage. This intentionally
    spends the approved ceiling faster than reported usage and bounds retries.
    """

    def __init__(
        self,
        provider: CompletionProvider,
        budget: Budget,
        *,
        default_model: str = MAIN,
        reasoning_effort: Literal["low"] | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.provider = provider
        self.budget = budget
        self.default_model = default_model
        self.reasoning_effort = reasoning_effort
        self.clock = clock
        self.sleep = sleep
        self.started = clock()
        self.attempts: list[Attempt] = []
        self.stop_reason: str | None = None
        self.task_id = "unassigned"
        self._lock = asyncio.Lock()

    def stop(self, reason: str) -> None:
        self.stop_reason = self.stop_reason or reason
        raise BudgetStop(self.stop_reason)

    def remaining(self) -> float:
        return self.budget.deadline_seconds - (self.clock() - self.started)

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> AssistantMessage:
        from app.retrieval.artifacts import canonical_sha256

        async with self._lock:
            if self.stop_reason:
                raise BudgetStop(self.stop_reason)
            target = model or self.default_model
            if target not in self.budget.models:
                self.stop("model_not_approved")
            cap = self.budget.models[target]
            payload = request_payload(messages, tools, response_format)
            # Conservative byte policy, not a tokenizer measurement. Reserve the
            # entire approved input cap and stop if provider usage exceeds it.
            byte_bound = input_reservation_bound(payload)
            if byte_bound > cap.per_call_input:
                self.stop("prompt_reservation_exceeded")
            reserved_input = (
                byte_bound
                if self.budget.input_reservation == "request_bound"
                else cap.per_call_input
            )
            previous = [a for a in self.attempts if a.model == target]
            if (
                len(previous) >= cap.max_attempts
                or sum(a.reserved_input for a in previous) + reserved_input
                > cap.input_tokens
                or sum(a.reserved_output for a in previous) + cap.per_call_output
                > cap.output_tokens
            ):
                self.stop("run_budget_exhausted")
            reservation = reserved_input + cap.per_call_output
            while True:
                now = self.clock()
                if self.remaining() <= 0:
                    self.stop("deadline")
                recent = [
                    a
                    for a in self.attempts
                    if now
                    - (
                        a.finished_seconds
                        if a.finished_seconds is not None
                        else a.start_seconds
                    )
                    < 60
                ]
                delay = max(
                    0.0,
                    (
                        self.attempts[-1].start_seconds
                        + self.budget.min_interval_seconds
                        - now
                    )
                    if self.attempts
                    else 0.0,
                )
                if (
                    len(recent) >= self.budget.shared_rpm - self.budget.visitor_rpm
                    or sum(a.reserved_input + a.reserved_output for a in recent)
                    + reservation
                    > self.budget.shared_tpm - self.budget.visitor_tpm
                ):
                    anchor = recent[0].finished_seconds
                    delay = max(
                        delay,
                        (anchor if anchor is not None else recent[0].start_seconds)
                        + 60
                        - now,
                    )
                if delay <= 0:
                    break
                if delay >= self.remaining():
                    self.stop("deadline_before_admission")
                await self.sleep(delay)
            request = ProviderRequest(
                model=target,
                messages=payload["messages"],
                tools=tools,
                response_format=response_format,
                max_completion_tokens=cap.per_call_output,
                reasoning_effort=self.reasoning_effort,
                timeout_seconds=min(
                    self.budget.request_timeout_seconds, self.remaining()
                ),
            )
            attempt = Attempt(
                number=len(self.attempts) + 1,
                task_id=self.task_id,
                model=target,
                start_seconds=self.clock(),
                reserved_input=reserved_input,
                reserved_output=cap.per_call_output,
                request_sha256=canonical_sha256(request.model_dump(mode="json")),
            )
            self.attempts.append(attempt)
            try:
                async with asyncio.timeout(request.timeout_seconds):
                    reply = await self.provider.complete(request)
            except BaseException as exc:
                # Preserve status and selected safe codes, never provider messages,
                # request headers/body or failed-generation/hidden-reasoning text.
                status = getattr(exc, "status_code", None)
                body = getattr(exc, "body", None)
                error = body.get("error", body) if isinstance(body, dict) else {}
                code = error.get("code") if isinstance(error, dict) else None
                diagnostic = ProviderFailure(
                    exception_type=type(exc).__name__,
                    status_code=status
                    if type(status) is int and 100 <= status <= 599
                    else None,
                    code=code
                    if code
                    in (
                        "json_validate_failed",
                        "context_length_exceeded",
                        "rate_limit_exceeded",
                    )
                    else None,
                )
                self.attempts[-1] = attempt.model_copy(
                    update={"status": "unknown", "provider_error": diagnostic}
                )
                self.stop_reason = "provider_consumption_unknown"
                if isinstance(
                    exc, KeyboardInterrupt | SystemExit | asyncio.CancelledError
                ):
                    raise
                raise BudgetStop(self.stop_reason) from None
            self.attempts[-1] = attempt.model_copy(
                update={
                    "status": "reported" if reply.usage is not None else "unknown",
                    "usage": reply.usage,
                    "reported_model": reply.model,
                    "finished_seconds": self.clock(),
                    "finish_reason": reply.finish_reason,
                }
            )
            if reply.usage is None:
                self.stop("provider_usage_missing")
            if (
                reply.usage.prompt_tokens > reserved_input
                or reply.usage.completion_tokens > cap.per_call_output
            ):
                self.stop("provider_reservation_exceeded")
            if reply.model != target:
                self.stop("provider_model_mismatch")
            if reply.finish_reason not in {"stop", "tool_calls"}:
                self.stop("incomplete_provider_output")
            if self.remaining() <= 0:
                self.stop("deadline")
            return AssistantMessage(
                content=reply.content
                if response_format
                else normalize_llm_text(reply.content),
                model=reply.model,
                prompt_tokens=reply.usage.prompt_tokens,
                completion_tokens=reply.usage.completion_tokens,
                total_tokens=reply.usage.total_tokens,
                tool_calls=reply.tool_calls,
            )

    async def stream(
        self, messages: list[Message], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str | ToolCall]:
        # Eval generation uses the production nonstreaming chat path so that
        # missing stream usage cannot silently become known zero usage.
        self.stop("streaming_not_enabled_for_live_evals")
        yield ""  # pragma: no cover
