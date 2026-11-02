"""Unit and integration tests for FitPipeline using zero-cost test fakes."""

import json

import pytest

from app.fit.models import FitRequest
from app.fit.pipeline import FitPipeline
from app.llm import FakeLLM, LLMRateLimitError
from app.retrieval.models import FactChunk
from app.retrieval.retriever import FakeRetriever


@pytest.fixture
def fake_retriever() -> FakeRetriever:
    """Fixture providing a deterministic FakeRetriever with verified chunks."""
    facts = [
        FactChunk(
            id="chunk-fastapi",
            type="project",
            title="FastAPI Portfolio Architecture",
            content="Built async REST API with FastAPI and SSE streaming.",
            source_section="J1",
        ),
        FactChunk(
            id="chunk-docker",
            type="skill",
            title="Docker Containerization",
            content="Configured multi-container Docker worker sandboxes in Entropy-OJ.",
            source_section="S1",
        ),
        FactChunk(
            id="chunk-react",
            type="skill",
            title="React and TypeScript",
            content="Developed responsive frontend in React and TypeScript.",
            source_section="S1",
        ),
    ]
    return FakeRetriever(default_facts=facts)


@pytest.mark.asyncio
async def test_fit_pipeline_end_to_end_success(
    fake_retriever: FakeRetriever,
) -> None:
    """Verify full 5-stage pipeline emits proper SSE events and valid report."""
    extraction_json = json.dumps(
        {
            "role_title": "Full-Stack AI Engineer",
            "requirements": [
                {
                    "id": "req-1",
                    "text": "Async Python API development with FastAPI",
                    "importance": "must_have",
                    "type": "skill",
                },
                {
                    "id": "req-2",
                    "text": "Docker containerization and worker setup",
                    "importance": "must_have",
                    "type": "skill",
                },
                {
                    "id": "req-3",
                    "text": "5+ years of enterprise Kubernetes administration",
                    "importance": "must_have",
                    "type": "skill",
                },
            ],
        }
    )

    judging_json = json.dumps(
        {
            "judged": [
                {
                    "requirement_id": "req-1",
                    "verdict": "strong",
                    "evidence_chunk_ids": ["chunk-fastapi"],
                    "explanation": "Built async FastAPI backend with SSE streaming.",
                    "ramp_up": None,
                },
                {
                    "requirement_id": "req-2",
                    "verdict": "strong",
                    "evidence_chunk_ids": ["chunk-docker"],
                    "explanation": "Docker sandboxes in Entropy-OJ.",
                    "ramp_up": None,
                },
                {
                    "requirement_id": "req-3",
                    "verdict": "gap",
                    "evidence_chunk_ids": [],
                    "explanation": "No hands-on Kubernetes administration.",
                    "ramp_up": "Ramp up via Minikube container orchestration.",
                },
            ]
        }
    )

    summary_text = (
        "Aamir demonstrates strong alignment on FastAPI backend and Docker. "
        "Enterprise Kubernetes represents an honest gap with rapid ramp-up readiness. "
        "A technical architecture interview is recommended."
    )

    fake_llm = FakeLLM(canned_replies=[extraction_json, judging_json, summary_text])

    pipeline = FitPipeline(llm=fake_llm, retriever=fake_retriever)
    request = FitRequest(
        jd_text=(
            "Looking for a Full-Stack AI Engineer with strong FastAPI, "
            "Docker containerization, and enterprise Kubernetes experience."
        )
    )

    events: list[dict] = []
    async for event in pipeline.run(request):
        events.append(event)

    # Verify event progression
    event_names = [e["event"] for e in events]
    assert "progress" in event_names
    assert event_names[-1] == "complete"

    complete_data = events[-1]["data"]
    assert complete_data["role_title"] == "Full-Stack AI Engineer"
    assert complete_data["score"]["must_have_strong"] == 2
    assert complete_data["score"]["must_have_gap"] == 1
    assert complete_data["score"]["overall_fit"] == "Partial Match"
    assert len(complete_data["requirements"]) == 3
    assert complete_data["summary"] == summary_text


@pytest.mark.asyncio
async def test_fit_pipeline_content_hash_caching(
    fake_retriever: FakeRetriever,
) -> None:
    """Verify repeat requests are served instantly from cache at 0 token cost."""
    extraction_json = json.dumps(
        {
            "role_title": "Backend Dev",
            "requirements": [
                {
                    "id": "req-1",
                    "text": "Python API",
                    "importance": "must_have",
                    "type": "skill",
                }
            ],
        }
    )
    judging_json = json.dumps(
        {
            "judged": [
                {
                    "requirement_id": "req-1",
                    "verdict": "strong",
                    "evidence_chunk_ids": ["chunk-fastapi"],
                    "explanation": "FastAPI expert",
                    "ramp_up": None,
                }
            ]
        }
    )
    fake_llm = FakeLLM(canned_replies=[extraction_json, judging_json, "Great fit."])
    pipeline = FitPipeline(llm=fake_llm, retriever=fake_retriever)

    req = FitRequest(
        jd_text="Looking for a Python API engineer to build scalable services."
    )

    # First run: uncached
    first_events = [e async for e in pipeline.run(req)]
    assert first_events[-1]["event"] == "complete"
    first_call_count = fake_llm.call_count

    # Second run: cached
    second_events = [e async for e in pipeline.run(req)]
    assert second_events[0]["data"]["step"] == "cache_hit"
    assert second_events[-1]["event"] == "complete"
    # Zero new LLM calls made!
    assert fake_llm.call_count == first_call_count


@pytest.mark.asyncio
async def test_fit_pipeline_downgrades_uncited_claims(
    fake_retriever: FakeRetriever,
) -> None:
    """Verify anti-overclaiming: uncited claims are downgraded to gap."""
    extraction_json = json.dumps(
        {
            "role_title": "AI Architect",
            "requirements": [
                {
                    "id": "req-1",
                    "text": "Kubernetes administration",
                    "importance": "must_have",
                    "type": "skill",
                }
            ],
        }
    )
    # Judge tries to claim 'strong' with an unverified invented chunk ID!
    judging_json = json.dumps(
        {
            "judged": [
                {
                    "requirement_id": "req-1",
                    "verdict": "strong",
                    "evidence_chunk_ids": ["bogus-invented-chunk"],
                    "explanation": "Candidate claims to know Kubernetes.",
                    "ramp_up": None,
                }
            ]
        }
    )
    fake_llm = FakeLLM(canned_replies=[extraction_json, judging_json, "Summary."])
    pipeline = FitPipeline(llm=fake_llm, retriever=fake_retriever)

    req = FitRequest(
        jd_text="Senior Architect needed with Kubernetes cluster leadership."
    )
    events = [e async for e in pipeline.run(req)]

    report = events[-1]["data"]
    judged_req = report["requirements"][0]
    # Downgrade invariant enforced!
    assert judged_req["verdict"] == "gap"
    assert judged_req["downgraded"] is True
    assert "[Downgraded to gap" in judged_req["explanation"]
    assert report["score"]["must_have_strong"] == 0
    assert report["score"]["must_have_gap"] == 1


@pytest.mark.asyncio
async def test_fit_pipeline_handles_llm_error_gracefully(
    fake_retriever: FakeRetriever,
) -> None:
    """Verify rate limit or provider error yields error frame without crashing."""
    fake_llm = FakeLLM(error_to_raise=LLMRateLimitError("Groq 429 rate limit exceeded"))
    pipeline = FitPipeline(llm=fake_llm, retriever=fake_retriever)

    req = FitRequest(
        jd_text=(
            "Looking for an experienced Python Developer to build "
            "asynchronous web APIs with FastAPI."
        )
    )
    events = [e async for e in pipeline.run(req)]

    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 1
    assert error_events[0]["data"]["code"] == "upstream_error"
