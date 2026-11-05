"""Request-local timing and usage without prompts, answers or recruiter text."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Literal
from zipfile import BadZipFile
from zlib import error as ZlibError

from pydantic import BaseModel, ConfigDict, Field

from app.llm import AssistantMessage, FakeLLM, LLMClient, Message, StreamUsage, ToolCall
from app.retrieval.artifacts import canonical_sha256, file_sha256
from app.retrieval.models import RetrievedChunk
from app.retrieval.retriever import Retriever


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ModelCall(Observation):
    stage: str
    configured_model: str | None = None
    reported_model: str | None = None
    duration_ms: float = Field(default=0, ge=0)
    status: Literal["running", "complete", "failed", "cancelled"] = "running"
    usage_source: Literal["reported", "fake", "unknown"] = "unknown"
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class RetrievedSource(Observation):
    id: str
    score: float
    rank: int = Field(ge=1)
    method: str


class RetrievalObservation(Observation):
    stage: str
    duration_ms: float = Field(ge=0)
    chunks: list[RetrievedSource]


class RequestTelemetry(Observation):
    version: Literal[1] = 1
    origin: Literal["fresh", "cache", "curated", "refused", "instant"] = "fresh"
    total_ms: float = Field(ge=0)
    first_text_ms: float | None = Field(default=None, ge=0)
    calls: list[ModelCall] = Field(default_factory=list)
    retrieval: list[RetrievalObservation] = Field(default_factory=list)
    stages_ms: dict[str, float] = Field(default_factory=dict)
    usage_complete: bool
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    prompt_sha256: str | None = None
    index_sha256: str | None = None
    index_built_at: str | None = None


class Trace:
    def __init__(self, clock: Callable[[], float] = time.perf_counter) -> None:
        self.clock = clock
        self.started = clock()
        self.first_text: float | None = None
        self.stage = "preparing"
        self.stage_started = self.started
        self.stages: dict[str, float] = {}
        self.calls: list[ModelCall] = []
        self.retrieval: list[RetrievalObservation] = []
        self.origin: Literal["fresh", "cache", "curated", "refused", "instant"] = (
            "fresh"
        )

    def set_stage(self, name: str) -> None:
        now = self.clock()
        self.stages[self.stage] = (
            self.stages.get(self.stage, 0) + (now - self.stage_started) * 1000
        )
        self.stage, self.stage_started = name, now

    def text(self) -> None:
        if self.first_text is None:
            self.first_text = (self.clock() - self.started) * 1000

    def snapshot(self) -> RequestTelemetry:
        now = self.clock()
        stages = {**self.stages}
        stages[self.stage] = (
            stages.get(self.stage, 0) + (now - self.stage_started) * 1000
        )
        complete = all(
            c.usage_source != "unknown" and c.status == "complete" for c in self.calls
        )
        return RequestTelemetry(
            origin=self.origin,
            total_ms=(now - self.started) * 1000,
            first_text_ms=self.first_text,
            calls=self.calls,
            retrieval=self.retrieval,
            stages_ms=stages,
            usage_complete=complete,
            input_tokens=sum(c.input_tokens or 0 for c in self.calls)
            if complete
            else None,
            output_tokens=sum(c.output_tokens or 0 for c in self.calls)
            if complete
            else None,
        )


active_trace: ContextVar[Trace | None] = ContextVar("request_trace", default=None)


def provenance() -> dict[str, str | None]:
    """Read tiny local metadata off-thread at the caller; missing index is unknown."""
    root = Path(__file__).parent
    from app.retrieval.artifacts import EmbeddingManifest

    result: dict[str, str | None] = {
        "prompt_sha256": canonical_sha256(
            {
                p.name: p.read_text(encoding="utf-8")
                for p in sorted((root / "prompts").glob("*.txt"))
            }
        ),
        "index_sha256": None,
        "index_built_at": None,
    }
    try:
        import numpy as np

        with np.load(
            root / "retrieval/facts_embeddings.npz", allow_pickle=False
        ) as archive:
            manifest = EmbeddingManifest.model_validate_json(
                str(archive["manifest"].item())
            )
        result.update(
            index_sha256=file_sha256(root / "retrieval/facts_embeddings.npz"),
            index_built_at=manifest.built_at.isoformat(),
        )
    except (OSError, ValueError, KeyError, BadZipFile, EOFError, ZlibError):
        pass
    return result


class ObservedLLM:
    def __init__(
        self,
        client: LLMClient,
        trace: Trace | None = None,
        main_model: str | None = None,
    ) -> None:
        self.client, self.trace, self.main_model = client, trace, main_model

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> AssistantMessage:
        trace = self.trace or active_trace.get()
        if trace is None:
            return await self.client.complete(
                messages, tools=tools, model=model, response_format=response_format
            )
        call = ModelCall(stage=trace.stage, configured_model=model or self.main_model)
        trace.calls.append(call)
        start = trace.clock()
        try:
            reply = await self.client.complete(
                messages, tools=tools, model=model, response_format=response_format
            )
            call.reported_model = reply.model
            if reply.usage_reported:
                call.usage_source = (
                    "fake" if isinstance(self.client, FakeLLM) else "reported"
                )
                call.input_tokens, call.output_tokens = (
                    reply.prompt_tokens,
                    reply.completion_tokens,
                )
            call.status = "complete"
            return reply
        except BaseException as exc:
            call.status = "failed" if isinstance(exc, Exception) else "cancelled"
            raise
        finally:
            call.duration_ms = (trace.clock() - start) * 1000

    async def stream(
        self, messages: list[Message], tools: list[dict[str, Any]] | None = None
    ) -> AsyncIterator[str | ToolCall]:
        trace = self.trace or active_trace.get()
        if trace is None:
            async for item in self.client.stream(messages, tools=tools):
                if not isinstance(item, StreamUsage):
                    yield item
            return
        call = ModelCall(stage=trace.stage, configured_model=self.main_model)
        trace.calls.append(call)
        start = trace.clock()
        try:
            async for item in self.client.stream(messages, tools=tools):
                if isinstance(item, StreamUsage):
                    call.reported_model = item.model
                    call.usage_source = "reported"
                    call.input_tokens, call.output_tokens = (
                        item.input_tokens,
                        item.output_tokens,
                    )
                else:
                    yield item
            call.status = "complete"
        except BaseException as exc:
            call.status = "failed" if isinstance(exc, Exception) else "cancelled"
            raise
        finally:
            call.duration_ms = (trace.clock() - start) * 1000


class ObservedRetriever:
    def __init__(self, retriever: Retriever, trace: Trace | None = None) -> None:
        self.retriever, self.trace = retriever, trace

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        trace = self.trace or active_trace.get()
        start = trace.clock() if trace else 0
        chunks = await self.retriever.retrieve(query, top_k=top_k)
        if trace:
            trace.retrieval.append(
                RetrievalObservation(
                    stage=trace.stage,
                    duration_ms=(trace.clock() - start) * 1000,
                    chunks=[
                        {
                            "id": r.chunk.id,
                            "score": r.score,
                            "rank": r.rank,
                            "method": r.retrieval_method,
                        }
                        for r in chunks
                        if not r.chunk.private and r.chunk.indexed
                    ],
                )
            )
        return chunks
