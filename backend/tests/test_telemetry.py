"""Real observation seams with fake providers, deterministic clocks and concurrency."""

import asyncio
import json
from collections.abc import AsyncIterator

import httpx
import pytest

from app.api.chat import stream_with_heartbeat
from app.fit.models import FitRequest
from app.fit.pipeline import FitPipeline
from app.llm import FakeLLM, GroqLLM, Message, ToolCall
from app.retrieval.models import FactChunk, RetrievedChunk
from app.retrieval.retriever import FakeRetriever
from app.settings import Settings
from app.telemetry import (
    ObservedLLM,
    ObservedRetriever,
    Trace,
    active_trace,
    provenance,
)


@pytest.mark.asyncio
async def test_complete_aggregation_and_clock() -> None:
    now = [1.0]
    trace = Trace(clock=lambda: now[0])
    llm = ObservedLLM(FakeLLM(), trace)
    now[0] = 1.1
    trace.set_stage("rewrite")
    first = await llm.complete([Message("user", "private recruiter query")])
    trace.set_stage("answer")
    second = await llm.complete([])
    now[0] = 1.4
    trace.text()
    now[0] = 1.5
    receipt = trace.snapshot()
    assert receipt.total_ms == 500
    assert receipt.first_text_ms == pytest.approx(400)
    assert receipt.input_tokens == first.prompt_tokens + second.prompt_tokens
    assert [c.stage for c in receipt.calls] == ["rewrite", "answer"]
    assert all(c.usage_source == "fake" for c in receipt.calls)
    assert "private recruiter query" not in receipt.model_dump_json()


@pytest.mark.asyncio
async def test_missing_stream_usage_is_unknown() -> None:
    trace = Trace()
    llm = ObservedLLM(FakeLLM(stream_chunks=["Aamir"]), trace)
    assert [item async for item in llm.stream([])] == ["Aamir"]
    receipt = trace.snapshot()
    assert not receipt.usage_complete
    assert receipt.input_tokens is receipt.output_tokens is None
    assert receipt.calls[0].status == "complete"


@pytest.mark.asyncio
async def test_real_sdk_stream_reports_final_usage_and_closes() -> None:
    from groq import AsyncGroq

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream_options"] == {"include_usage": True}
        base = {
            "id": "fake",
            "created": 0,
            "model": "reported-model",
            "object": "chat.completion.chunk",
        }
        frames = [
            {**base, "choices": [{"index": 0, "delta": {"content": "Aamir"}}]},
            {
                **base,
                "choices": [],
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 3,
                    "total_tokens": 15,
                },
            },
        ]
        data = (
            "".join(f"data: {json.dumps(f)}\n\n" for f in frames) + "data: [DONE]\n\n"
        )
        return httpx.Response(
            200, text=data, headers={"content-type": "text/event-stream"}
        )

    adapter = GroqLLM(Settings(GROQ_API_KEY="fake-test-key"))
    await adapter._client.close()
    adapter._client = AsyncGroq(
        api_key="fake-test-key",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    trace = Trace()
    try:
        observed = ObservedLLM(adapter, trace, main_model="configured-model")
        assert [text async for text in observed.stream([])] == ["Aamir"]
        receipt = trace.snapshot()
        assert receipt.usage_complete
        assert (receipt.input_tokens, receipt.output_tokens) == (12, 3)
        assert receipt.calls[0].reported_model == "reported-model"
        assert receipt.calls[0].configured_model == "configured-model"
    finally:
        await adapter._client.close()


@pytest.mark.asyncio
async def test_cancelled_stream_is_incomplete() -> None:
    started = asyncio.Event()

    class WaitingFake(FakeLLM):
        async def stream(
            self, messages: list[Message], tools=None
        ) -> AsyncIterator[str | ToolCall]:
            yield "first"
            started.set()
            await asyncio.Event().wait()

    trace = Trace()
    observed = ObservedLLM(WaitingFake(), trace)

    async def consume() -> None:
        async for _ in observed.stream([]):
            pass

    task = asyncio.create_task(consume())
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert trace.snapshot().calls[0].status == "cancelled"
    assert trace.snapshot().input_tokens is None


@pytest.mark.asyncio
async def test_private_chunks_never_appear_in_receipt() -> None:
    trace = Trace()
    chunks = [
        RetrievedChunk(
            chunk=FactChunk(
                id="private",
                type="personal",
                title="Private",
                content="secret",
                private=True,
            ),
            score=1,
            rank=1,
        )
    ]
    retriever = ObservedRetriever(FakeRetriever(canned_chunks=chunks), trace)
    await retriever.retrieve("private query")
    assert trace.snapshot().retrieval[0].chunks == []
    assert "secret" not in trace.snapshot().model_dump_json()


@pytest.mark.asyncio
async def test_shared_fit_pipeline_context_isolation_across_heartbeat_tasks() -> None:
    llm = FakeLLM(canned_replies=["invalid"] * 8)
    pipeline = FitPipeline(llm, FakeRetriever(canned_chunks=[]), cache={})

    async def run(text: str):
        return [
            e
            async for e in stream_with_heartbeat(pipeline.run(FitRequest(jd_text=text)))
        ]

    first, second = await asyncio.gather(run("a" * 60), run("b" * 60))
    for events in (first, second):
        receipt = events[-1]["data"]["telemetry"]
        assert len(receipt["calls"]) == 2
        assert all(c["stage"] == "extracting_requirements" for c in receipt["calls"])
    assert active_trace.get() is None


def test_actual_index_provenance_available() -> None:
    metadata = provenance()
    assert metadata["index_built_at"]
    assert len(metadata["index_sha256"]) == 64
