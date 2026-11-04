"""Capture real endpoint contracts with fake adapters; no live-generation mode."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.fit import get_fit_pipeline  # noqa: E402
from app.fit.models import FitReport  # noqa: E402
from app.fit.pipeline import FitPipeline  # noqa: E402
from app.llm import (  # noqa: E402
    AssistantMessage,
    FakeLLM,
    LLMUnavailableError,
    Message,
    ToolCall,
    get_llm_client,
)
from app.main import create_app  # noqa: E402
from app.retrieval.artifacts import canonical_sha256, corpus_sha256  # noqa: E402
from app.retrieval.loader import FactLoader  # noqa: E402
from app.retrieval.models import FactChunk, RetrievedChunk  # noqa: E402
from app.retrieval.retriever import FakeRetriever, get_retriever  # noqa: E402
from app.safety.quota import (  # noqa: E402
    DailyQuotaGuard,
    check_daily_quota,
    get_quota_guard,
)
from app.safety.rate_limiter import (  # noqa: E402
    RateLimitResult,
    check_fit_rate_limit,
    check_rate_limit,
)
from app.settings import Settings, get_settings  # noqa: E402
from app.tools.registry import ToolRegistry, get_tool_registry  # noqa: E402
from evals.checks import (  # noqa: E402
    CaptureBundle,
    CaseReference,
    RecordedUsage,
    Recording,
    ReplayChecks,
    prompt_files_fingerprint,
)
from evals.dataset import (  # noqa: E402
    DEFAULT_ROOT,
    REPO_ROOT,
    case_fingerprint,
    load_cases,
    load_manifest,
    verify_dataset,
)

DEFAULT_RECORDINGS = DEFAULT_ROOT / "recordings" / "endpoints-v1.json"


class TraceFakeLLM(FakeLLM):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.complete_attempts = 0
        self.stream_attempts = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> AssistantMessage:
        self.complete_attempts += 1
        reply = await super().complete(messages, tools, model, response_format)
        self.prompt_tokens += reply.prompt_tokens
        self.completion_tokens += reply.completion_tokens
        return reply

    async def stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str | ToolCall]:
        self.stream_attempts += 1
        async for item in super().stream(messages, tools):
            yield item


class CaptureRetriever(FakeRetriever):
    def __init__(
        self,
        chunks: list[FactChunk],
        by_query: dict[str, list[FactChunk]] | None = None,
    ) -> None:
        super().__init__()
        self.chunks = chunks
        self.by_query = by_query or {}
        self.evidence: dict[str, list[str]] = {}

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        self.recorded_queries.append(query)
        chosen = self.by_query.get(query, self.chunks)[:top_k]
        self.evidence[query] = [chunk.id for chunk in chosen]
        return [
            RetrievedChunk(chunk=chunk, rank=i, score=1 / i, retrieval_method="fake")
            for i, chunk in enumerate(chosen, 1)
        ]


def _capture_app(
    llm: TraceFakeLLM, retriever: CaptureRetriever, pipeline: FitPipeline | None = None
) -> FastAPI:
    settings = Settings(ENVIRONMENT="test", GROQ_API_KEY="")
    app = create_app(settings=settings)
    registry = ToolRegistry()
    quota = DailyQuotaGuard()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_llm_client] = lambda: llm
    app.dependency_overrides[get_retriever] = lambda: retriever
    app.dependency_overrides[get_tool_registry] = lambda: registry
    app.dependency_overrides[get_quota_guard] = lambda: quota
    app.dependency_overrides[check_daily_quota] = lambda: None
    app.dependency_overrides[check_rate_limit] = lambda: RateLimitResult(
        True, 10, 9, 60
    )
    app.dependency_overrides[check_fit_rate_limit] = lambda: None
    if pipeline is not None:
        app.dependency_overrides[get_fit_pipeline] = lambda: pipeline
    return app


def capture_contracts() -> CaptureBundle:
    verify_dataset()
    facts = {chunk.id: chunk for chunk in FactLoader().load_all()}
    cases = {case.id: case for case in load_cases()}
    records: list[Recording] = []

    def reference(case_id: str) -> CaseReference:
        case = cases[case_id]
        return CaseReference(
            id=case.id, version=case.version, sha256=case_fingerprint(case)
        )

    def chat(
        cid: str,
        case_id: str,
        llm: TraceFakeLLM,
        source_ids: list[str],
        checks: ReplayChecks,
    ) -> None:
        case = cases[case_id]
        retriever = CaptureRetriever([facts[source_id] for source_id in source_ids])
        app = _capture_app(llm, retriever)
        payload = {
            "message": case.conversation[-1].content,
            "conversation_id": f"replay-{cid}",
            "history": [turn.model_dump() for turn in case.conversation[:-1]],
        }
        # Contract capture owns injected dependencies and skips production lifespan.
        with closing(TestClient(app)) as client:
            response = client.post("/api/chat/stream", json=payload)
        response.raise_for_status()
        records.append(
            Recording(
                id=cid,
                transport="chat_sse",
                origin="fake",
                delivery="fresh",
                model=llm.model,
                case=reference(case_id),
                raw_sse=response.text,
                checks=checks,
                retrieved_chat_ids=[
                    chunk_id for ids in retriever.evidence.values() for chunk_id in ids
                ],
                retrieval_queries=retriever.recorded_queries,
                adapter_complete_calls=llm.complete_attempts,
                adapter_stream_calls=llm.stream_attempts,
            )
        )

    chat(
        "chat-project",
        "eval-07-entropy-oj-pitch",
        TraceFakeLLM(
            stream_chunks=[
                "Aamir",
                ":",
                " Entropy-OJ — a competitive programming platform "
                "using Redis and BullMQ.",
            ],
            tool_calls=[
                ToolCall(
                    id="fixture-card",
                    name="show_project_card",
                    arguments='{"project_id":"entropy-oj"}',
                )
            ],
        ),
        ["proj-entropy-oj-pitch", "proj-entropy-oj-stack"],
        ReplayChecks(
            must_include=["Aamir:", "Entropy-OJ", "BullMQ"],
            must_not_include=["Google employee"],
            max_chars=1000,
        ),
    )
    chat(
        "chat-followup",
        "followup-entropy-stack",
        TraceFakeLLM(
            canned_replies=["Entropy-OJ Redis BullMQ queue design"],
            stream_chunks=[
                "Entropy-OJ uses Redis and BullMQ "
                "to decouple execution from HTTP requests."
            ],
        ),
        ["proj-entropy-oj-stack", "proj-entropy-oj-design"],
        ReplayChecks(must_include=["Redis", "BullMQ"]),
    )
    chat(
        "chat-refusal",
        "persona-override",
        TraceFakeLLM(),
        [],
        ReplayChecks(expect_refusal=True),
    )
    chat(
        "chat-error",
        "eval-07-entropy-oj-pitch",
        TraceFakeLLM(error_to_raise=LLMUnavailableError("synthetic")),
        ["proj-entropy-oj-pitch"],
        ReplayChecks(expected_error="chat_error"),
    )

    requirements = [
        {
            "id": "req-python",
            "text": "Python API development",
            "importance": "must_have",
            "type": "skill",
        },
        {
            "id": "req-aws",
            "text": "Production AWS operations",
            "importance": "must_have",
            "type": "skill",
        },
    ]
    llm = TraceFakeLLM(
        canned_replies=[
            json.dumps(
                {"role_title": "Replay test role", "requirements": requirements}
            ),
            json.dumps(
                {
                    "judged": [
                        {
                            "requirement_id": "req-python",
                            "verdict": "strong",
                            "evidence_chunk_ids": ["skill-programming-languages"],
                            "explanation": "Recorded Python programming evidence.",
                        },
                        {
                            "requirement_id": "req-aws",
                            "verdict": "gap",
                            "evidence_chunk_ids": ["skill-not-claimed"],
                            "explanation": (
                                "Hands-on AWS operations are not established."
                            ),
                            "ramp_up": (
                                "Future learning plan only; not existing experience."
                            ),
                        },
                    ]
                }
            ),
            "Aamir has documented Python programming experience. "
            "Hands-on AWS operations remain a gap. "
            "Discuss the requirements and evidence directly.",
        ]
    )
    retriever = CaptureRetriever(
        [],
        by_query={
            "Python API development": [facts["skill-programming-languages"]],
            "Production AWS operations": [
                facts["skill-not-claimed"],
                facts["skill-ramp-up-narratives"],
            ],
        },
    )
    settings = Settings(ENVIRONMENT="test", GROQ_API_KEY="")
    pipeline = FitPipeline(llm, retriever, settings=settings, cache={})
    app = _capture_app(llm, retriever, pipeline)
    case_id = "fit-cloud-negative"
    checks = ReplayChecks(
        must_include=["Python", "gap"],
        must_not_include=[
            "Aamir has production AWS experience",
            "actively studying for CKA",
        ],
        negative_rules=[
            {
                "requirement_contains": "AWS",
                "negative_evidence_ids": [
                    "skill-not-claimed",
                    "skill-ramp-up-narratives",
                ],
            }
        ],
    )
    with closing(TestClient(app)) as client:
        for delivery in ("fresh", "cached"):
            calls, prompt, completion = (
                llm.complete_attempts,
                llm.prompt_tokens,
                llm.completion_tokens,
            )
            response = client.post(
                "/api/fit",
                json={
                    "jd_text": cases[case_id].conversation[0].content,
                    "role_title": "Replay test role",
                },
            )
            response.raise_for_status()
            records.append(
                Recording(
                    id=f"fit-{delivery}",
                    transport="fit_sse",
                    origin="fake",
                    delivery=delivery,
                    model=llm.model,
                    case=reference(case_id),
                    raw_sse=response.text,
                    checks=checks,
                    evidence_by_requirement={
                        req["id"]: retriever.evidence[req["text"]]
                        for req in requirements
                    },
                    retrieval_queries=list(retriever.recorded_queries),
                    usage=RecordedUsage(
                        source="fake",
                        prompt_tokens=llm.prompt_tokens - prompt,
                        completion_tokens=llm.completion_tokens - completion,
                    ),
                    adapter_complete_calls=llm.complete_attempts - calls,
                )
            )
        preset = client.get("/api/fit/presets").json()[0]["report"]
        records.append(
            Recording(
                id="fit-preset",
                transport="preset_json",
                origin="curated",
                delivery="preset",
                preset_report=FitReport.model_validate(preset),
            )
        )
    llm = TraceFakeLLM(canned_replies=["not JSON", "still not JSON"])
    retriever = CaptureRetriever([])
    app = _capture_app(
        llm, retriever, FitPipeline(llm, retriever, settings=settings, cache={})
    )
    with closing(TestClient(app)) as client:
        response = client.post(
            "/api/fit", json={"jd_text": cases[case_id].conversation[0].content}
        )
    response.raise_for_status()
    records.append(
        Recording(
            id="fit-extraction-error",
            transport="fit_sse",
            origin="fake",
            delivery="fresh",
            model=llm.model,
            case=reference(case_id),
            raw_sse=response.text,
            adapter_complete_calls=llm.complete_attempts,
            checks=ReplayChecks(expected_error="extraction_error"),
        )
    )
    capture_sources = [
        Path(__file__),
        DEFAULT_ROOT / "checks.py",
        *sorted((REPO_ROOT / "backend/app/api").glob("*.py")),
    ]
    return CaptureBundle(
        captured_at=datetime.now(UTC),
        commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip(),
        dirty=bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True
            ).strip()
        ),
        corpus_sha256=corpus_sha256(list(facts.values())),
        dataset_manifest_sha256=canonical_sha256(
            load_manifest().model_dump(mode="json")
        ),
        prompt_files_sha256=prompt_files_fingerprint(),
        capture_source_sha256=canonical_sha256(
            {
                p.relative_to(REPO_ROOT).as_posix(): p.read_text(encoding="utf-8")
                for p in capture_sources
            }
        ),
        records=records,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Explicitly regenerate the reviewed fake/curated endpoint fixtures",
    )
    args = parser.parse_args()
    bundle = capture_contracts()
    if args.write:
        DEFAULT_RECORDINGS.parent.mkdir(exist_ok=True)
        DEFAULT_RECORDINGS.write_text(
            bundle.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    else:
        saved = CaptureBundle.model_validate_json(
            DEFAULT_RECORDINGS.read_text(encoding="utf-8")
        )
        if (
            saved.records != bundle.records
            or saved.prompt_files_sha256 != bundle.prompt_files_sha256
            or saved.corpus_sha256 != bundle.corpus_sha256
        ):
            raise ValueError(
                "Endpoint fixture drift; review and explicitly regenerate the capture"
            )
    print(
        f"Validated {len(bundle.records)} fake/curated endpoint captures; "
        "zero live Groq calls."
    )


if __name__ == "__main__":
    main()
