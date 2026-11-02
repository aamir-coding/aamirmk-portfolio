"""Tests for GET /api/debug/retrieve inspection endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.retrieval.models import FactChunk, RetrievedChunk
from app.retrieval.retriever import FakeRetriever, get_retriever
from app.settings import Settings


@pytest.fixture
def fake_retriever() -> FakeRetriever:
    canned = [
        RetrievedChunk(
            chunk=FactChunk(
                id="proj-entropy-oj-pitch",
                type="project",
                title="Entropy Online Judge",
                content="Flagship competitive programming platform in Linux sandbox.",
                source_section="J1",
                source_url="https://github.com/aamir-coding/entropy-oj",
                tags=["entropy-oj"],
                draft=False,
            ),
            score=0.98,
            rank=1,
            retrieval_method="hybrid",
        )
    ]
    return FakeRetriever(canned_chunks=canned)


def test_debug_retrieve_returns_chunks_in_dev(fake_retriever: FakeRetriever):
    """Verify that in dev mode, /api/debug/retrieve returns chunks and scores."""
    settings = Settings(ENVIRONMENT="development")
    app = create_app(settings=settings)
    app.dependency_overrides[get_retriever] = lambda: fake_retriever

    with TestClient(app) as client:
        res = client.get("/api/debug/retrieve?q=entropy")
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == "entropy"
        assert data["count"] == 1
        assert len(data["results"]) == 1

        first = data["results"][0]
        assert first["id"] == "proj-entropy-oj-pitch"
        assert first["source_url"] == "https://github.com/aamir-coding/entropy-oj"
        assert first["score"] == 0.98
        assert first["rank"] == 1
        assert "Flagship" in first["snippet"]


def test_debug_retrieve_disabled_in_production(fake_retriever: FakeRetriever):
    """Verify that in production without flag, /api/debug/retrieve returns 404."""
    settings = Settings(ENVIRONMENT="production", ENABLE_DEBUG_RETRIEVAL=False)
    app = create_app(settings=settings)
    app.dependency_overrides[get_retriever] = lambda: fake_retriever

    with TestClient(app) as client:
        res = client.get("/api/debug/retrieve?q=entropy")
        assert res.status_code == 404
        assert "disabled" in res.json()["error"]["message"]


def test_debug_retrieve_enabled_in_production_with_flag(fake_retriever: FakeRetriever):
    """Verify that in production mode with ENABLE_DEBUG_RETRIEVAL=True, it responds."""
    settings = Settings(ENVIRONMENT="production", ENABLE_DEBUG_RETRIEVAL=True)
    app = create_app(settings=settings)
    app.dependency_overrides[get_retriever] = lambda: fake_retriever

    with TestClient(app) as client:
        res = client.get("/api/debug/retrieve?q=entropy")
        assert res.status_code == 200
        assert res.json()["count"] == 1
