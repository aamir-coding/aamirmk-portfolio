"""Integration tests for POST /api/fit and GET /api/fit/presets endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from app.api.fit import set_fit_pipeline
from app.fit.pipeline import FitPipeline
from app.llm import FakeLLM, get_llm_client
from app.main import app
from app.retrieval.models import FactChunk
from app.retrieval.retriever import FakeRetriever, get_retriever, set_retriever
from app.safety.rate_limiter import get_fit_rate_limiter


@pytest.fixture(autouse=True)
def reset_dependencies() -> None:
    """Reset dependency overrides and fit pipeline instance after every test."""
    app.dependency_overrides.clear()
    fake_ret = FakeRetriever()
    set_retriever(fake_ret)
    app.dependency_overrides[get_retriever] = lambda: fake_ret
    set_fit_pipeline(None)
    fit_limiter = get_fit_rate_limiter()
    fit_limiter.reset()
    yield
    app.dependency_overrides.clear()
    set_retriever(None)
    set_fit_pipeline(None)


def test_get_fit_presets_returns_curated_roles() -> None:
    """Verify GET /api/fit/presets returns all 4 sample roles with required fields."""
    with TestClient(app) as client:
        response = client.get("/api/fit/presets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert data[0]["id"] == "01-fullstack-ai-engineer"
        assert "text" in data[0]
        assert data[0]["match_expectation"] == "Strong Match"


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


def test_post_fit_streaming_success() -> None:
    """Verify POST /api/fit yields SSE stream with progress and complete events."""
    extraction_json = json.dumps(
        {
            "role_title": "Full-Stack AI Engineer",
            "requirements": [
                {
                    "id": "req-1",
                    "text": "FastAPI development",
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
                    "explanation": "Built FastAPI backend.",
                    "ramp_up": None,
                }
            ]
        }
    )
    summary_text = (
        "Aamir is a strong match for this FastAPI development role. "
        "No significant gaps identified in core backend competencies. "
        "Recommended for interview."
    )

    fake_llm = FakeLLM(canned_replies=[extraction_json, judging_json, summary_text])
    fake_retriever = FakeRetriever(
        default_facts=[
            FactChunk(
                id="chunk-fastapi",
                type="project",
                title="FastAPI Backend",
                content="Async REST APIs and SSE streaming built in FastAPI.",
                source_section="J1",
            )
        ]
    )

    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    app.dependency_overrides[get_retriever] = lambda: fake_retriever

    payload = {
        "jd_text": (
            "We are seeking a Full-Stack AI Engineer with solid FastAPI "
            "experience to build our next generation APIs and web apps."
        ),
        "role_title": "Full-Stack AI Engineer",
    }

    with TestClient(app) as client:
        response = client.post("/api/fit", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        body_text = response.text
        assert "event: progress" in body_text
        assert "event: complete" in body_text
        assert "Full-Stack AI Engineer" in body_text
        assert "chunk-fastapi" in body_text


def test_post_fit_rate_limit_enforcement() -> None:
    """Verify fit rate limiter stops requests after exceeding daily limit."""
    limiter = get_fit_rate_limiter()
    limiter.requests_per_window = 2  # Set window capacity to 2 for test

    pipeline = FitPipeline(
        llm=FakeLLM(reply="{}"),
        retriever=FakeRetriever(),
    )
    set_fit_pipeline(pipeline)

    payload = {
        "jd_text": (
            "Looking for a Python Developer with experience in web backends "
            "and database optimization for microservices."
        )
    }

    with TestClient(app) as client:
        # Request 1: allowed
        res1 = client.post("/api/fit", json=payload)
        assert res1.status_code == 200

        # Request 2: allowed
        res2 = client.post("/api/fit", json=payload)
        assert res2.status_code == 200

        # Request 3: blocked with 429
        res3 = client.post("/api/fit", json=payload)
        assert res3.status_code == 429
        assert "Retry-After" in res3.headers
        assert "Daily JD Fit Report limit reached" in res3.json()["error"]["message"]
