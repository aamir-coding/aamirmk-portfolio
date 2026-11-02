"""Unit tests for Okapi BM25 lexical keyword retrieval."""

from __future__ import annotations

import pytest

from app.retrieval.bm25 import BM25Index, tokenize
from app.retrieval.loader import FactLoader
from app.retrieval.models import FactChunk


def test_tokenize_preserves_technical_identifiers():
    """Tokenize preserves compounds (C++, Node.js, 9.77) and emits sub-tokens."""
    text = "C++17, C++, Python 3.11, Node.js, BullMQ, ETIMEDOUT, 9.77/10.0, full-stack"
    tokens = tokenize(text)

    # Exact compound checks
    assert "c++17" in tokens
    assert "c++" in tokens
    assert "17" in tokens
    assert "python" in tokens
    assert "3.11" in tokens
    assert "node.js" in tokens
    assert "node" in tokens
    assert "js" in tokens
    assert "bullmq" in tokens
    assert "etimedout" in tokens
    assert "9.77" in tokens
    assert "full-stack" in tokens
    assert "full" in tokens
    assert "stack" in tokens


def test_tokenize_handles_empty_and_whitespace():
    """Tokenize safely returns empty list for blank inputs."""
    assert tokenize("") == []
    assert tokenize("   ") == []
    assert tokenize("!!! ??? ---") == []


def test_bm25_empty_index_and_query():
    """BM25Index handles empty index and queries safely."""
    empty_index = BM25Index()
    assert empty_index.search("FastAPI") == []

    chunk = FactChunk(
        id="c1",
        type="project",
        title="Sample",
        content="Testing FastAPI and Python.",
    )
    index = BM25Index([chunk])
    assert index.search("") == []
    assert index.search("   ") == []
    assert index.search("Rust", top_k=5) == []
    assert index.search("FastAPI", top_k=0) == []


def test_bm25_document_length_normalization():
    """Shorter document matching term ranks higher than diluted long document."""
    short_doc = FactChunk(
        id="short",
        type="skill",
        title="FastAPI Skill",
        content="FastAPI backend development.",
    )
    long_doc = FactChunk(
        id="long",
        type="skill",
        title="General Architecture",
        content=(
            "FastAPI is mentioned here among many other general concepts like "
            "microservices, message queues, containerization, relational databases, "
            "frontend frameworks, distributed logging, cloud virtual machines, "
            "continuous integration pipelines, and deployment strategies."
        ),
    )
    index = BM25Index([short_doc, long_doc])
    results = index.search("FastAPI", top_k=2)

    assert len(results) == 2
    assert results[0].chunk.id == "short"
    assert results[0].score > results[1].score
    assert results[0].rank == 1
    assert results[1].rank == 2


def test_bm25_term_frequency_saturation():
    """Document mentioning term twice scores higher following saturation curve."""
    doc_single = FactChunk(
        id="single",
        type="project",
        title="Docker Project",
        content="This project uses Docker for deployment.",
    )
    doc_double = FactChunk(
        id="double",
        type="project",
        title="Docker Optimization",
        content="Docker containerization with custom Docker build caching.",
    )
    index = BM25Index([doc_single, doc_double])
    results = index.search("Docker", top_k=2)

    assert results[0].chunk.id == "double"
    assert results[0].score > results[1].score


@pytest.fixture(scope="module")
def production_facts() -> list[FactChunk]:
    """Loads all production fact chunks."""
    loader = FactLoader()
    return loader.load_all(include_private=False, include_unindexed=False)


def test_bm25_exact_technical_retrieval(production_facts: list[FactChunk]):
    """BM25 reliably retrieves exact technical keywords on production facts."""
    index = BM25Index(production_facts)

    # 1. Hardest bug query
    results_bug = index.search("hardest bug ETIMEDOUT", top_k=3)
    assert len(results_bug) > 0
    top_ids = [r.chunk.id for r in results_bug]
    expected_ids = {"exp-algouniversity-hardest-bug", "proj-entropy-oj-hardest-bug"}
    assert any(eid in top_ids for eid in expected_ids)

    # 2. CGPA exact query
    results_cgpa = index.search("What is Aamir's CGPA 9.77?", top_k=3)
    assert len(results_cgpa) > 0
    assert results_cgpa[0].chunk.id in (
        "education-degree",
        "achieve-academic-excellence",
    )

    # 3. Google Cloud hackathon query
    results_hackathon = index.search("Google Cloud hackathon VayuSetu", top_k=3)
    assert len(results_hackathon) > 0
    assert any(
        "hackathon" in r.chunk.id or "vayusetu" in r.chunk.id for r in results_hackathon
    )

    # 4. Streamlit XGBoost ML query
    results_ml = index.search("Streamlit XGBoost regression premium predictor", top_k=3)
    assert len(results_ml) > 0
    assert "proj-health-premium-overview" in [r.chunk.id for r in results_ml]

    # Verify ranking metadata consistency
    for r in results_ml:
        assert r.retrieval_method == "bm25"
        assert r.score > 0.0
        assert r.rank >= 1
