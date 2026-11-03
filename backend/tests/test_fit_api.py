"""Integration tests for POST /api/fit and GET /api/fit/presets endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.fit import set_fit_pipeline
from app.fit.models import FitReport, FitScoreSummary
from app.fit.pipeline import FitPipeline
from app.fit.sample_jds import load_sample_jds
from app.llm import FakeLLM
from app.main import app
from app.retrieval.models import FactChunk, RetrievedChunk
from app.retrieval.retriever import FakeRetriever, set_retriever
from app.safety.rate_limiter import SlidingWindowRateLimiter, get_fit_rate_limiter


@pytest.fixture(autouse=True)
def setup_test_pipeline() -> None:
    """Ensure a clean, lightweight fake retriever for test isolation."""
    fake_ret = FakeRetriever(canned_chunks=[])
    set_retriever(fake_ret)
    yield
    set_fit_pipeline(None)
    app.dependency_overrides.clear()


def test_get_fit_presets_returns_curated_roles() -> None:
    """Verify GET /api/fit/presets returns all 4 sample roles with reports."""
    with TestClient(app) as client:
        response = client.get("/api/fit/presets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert data[0]["id"] == "01-fullstack-ai-engineer"
        assert "text" in data[0]
        assert data[0]["match_expectation"] == "Partial Match"
        assert "report" in data[0]
        assert data[0]["report"]["score"]["overall_fit"] == "Partial Match"


def test_post_fit_returns_pre_seeded_cache_hit_instantly() -> None:
    """Verify POST /api/fit hits pre-seeded cache without invoking LLM."""
    sample = load_sample_jds()[0]

    with TestClient(app) as client:
        response = client.post(
            "/api/fit",
            json={"jd_text": sample.text, "role_title": sample.title},
        )
        assert response.status_code == 200
        content = response.text
        assert "event: progress" in content
        assert "cache_hit" in content
        assert "event: complete" in content


def test_post_fit_rejects_payload_too_short() -> None:
    """Verify POST /api/fit returns 422 for job description under 50 characters."""
    with TestClient(app) as client:
        response = client.post(
            "/api/fit",
            json={"jd_text": "Too short JD"},
        )
        assert response.status_code == 422

        data = response.json()
        assert data["error"]["code"] == 422


def test_post_fit_whitespace_validation_returns_serializable_422() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/fit", json={"jd_text": " " * 50})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == 422
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert error["details"][0]["loc"] == ["body", "jd_text"]
    assert "ctx" not in error["details"][0]


def test_post_fit_rejects_payload_too_long() -> None:
    """Verify POST /api/fit returns 422 for job description over 6,000 characters."""
    with TestClient(app) as client:
        response = client.post(
            "/api/fit",
            json={"jd_text": "A" * 6001},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == 422


def test_post_fit_streams_progress_and_completion_events() -> None:
    """Verify POST /api/fit streams SSE events with valid schema on custom JD."""
    canned_extraction = (
        '{"requirements": [{"id": "r1", "text": "Python 3", '
        '"importance": "must_have", "type": "skill"}]}'
    )
    canned_judging = (
        '{"judged": [{"requirement_id": "r1", "verdict": "strong", '
        '"evidence_chunk_ids": ["test-chunk"], "explanation": "Direct match"}]}'
    )
    canned_summary = (
        "Candidate meets requirements. Excellent candidate fit. Proceed to interview."
    )

    fake_llm = FakeLLM(
        canned_replies=[canned_extraction, canned_judging, canned_summary]
    )

    fake_fact = FactChunk(
        id="test-chunk",
        title="Test Chunk",
        type="skill",
        source_section="S1",
        content="Python 3 async expert with FastAPI.",
    )
    fake_chunk = RetrievedChunk(
        chunk=fake_fact,
        score=0.95,
        rank=1,
        retrieval_method="fake",
    )
    fake_retriever = FakeRetriever(canned_chunks=[fake_chunk])

    pipeline = FitPipeline(llm=fake_llm, retriever=fake_retriever, cache={})
    set_fit_pipeline(pipeline)

    sample_jd = (
        "Seeking a Senior Python Backend Engineer with 5+ years of async FastAPI "
        "and PostgreSQL experience building high-scale microservices."
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/fit",
            json={"jd_text": sample_jd, "role_title": "Senior Python Engineer"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        content = response.text
        assert "event: progress" in content
        assert "event: complete" in content
        assert "Senior Python Engineer" in content


def test_post_fit_enforces_daily_rate_limit() -> None:
    """Verify POST /api/fit enforces daily fit limit of 5 per client IP."""
    limiter = SlidingWindowRateLimiter(requests_per_window=2, window_seconds=86400.0)
    app.dependency_overrides[get_fit_rate_limiter] = lambda: limiter

    fake_report = FitReport(
        role_title="Test Role",
        jd_hash="a" * 64,
        score=FitScoreSummary(
            must_have_total=1,
            must_have_strong=1,
            must_have_partial=0,
            must_have_gap=0,
            nice_to_have_total=0,
            nice_to_have_strong=0,
            nice_to_have_partial=0,
            nice_to_have_gap=0,
            total_requirements=1,
            overall_fit="Strong Match",
            headline="Match",
        ),
        requirements=[],
        summary="Good match summary.",
    )
    pipeline = FitPipeline(
        llm=FakeLLM(), retriever=FakeRetriever(), cache={"a" * 64: fake_report}
    )
    set_fit_pipeline(pipeline)

    sample_payload = {"jd_text": "B" * 60, "role_title": "Test Role"}

    with TestClient(app) as client:
        # First 2 requests succeed
        res1 = client.post(
            "/api/fit", json=sample_payload, headers={"X-Forwarded-For": "1.2.3.4"}
        )
        assert res1.status_code == 200

        res2 = client.post(
            "/api/fit", json=sample_payload, headers={"X-Forwarded-For": "1.2.3.4"}
        )
        assert res2.status_code == 200

        # 3rd request from same IP is rate-limited (429)
        res3 = client.post(
            "/api/fit", json=sample_payload, headers={"X-Forwarded-For": "1.2.3.4"}
        )
        assert res3.status_code == 429
        data = res3.json()
        assert data["error"]["code"] == 429
        assert "Daily JD Fit Report limit reached" in data["error"]["message"]
