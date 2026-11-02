"""Unit tests for Reciprocal Rank Fusion, Retriever protocol, and HybridRetriever."""

from __future__ import annotations

import pytest

from app.retrieval.hybrid import HybridRetriever, reciprocal_rank_fusion
from app.retrieval.loader import FactLoader
from app.retrieval.models import FactChunk, RetrievedChunk
from app.retrieval.retriever import FakeRetriever, Retriever


def _make_chunk(cid: str) -> FactChunk:
    return FactChunk(
        id=cid,
        type="project",
        title=f"Title {cid}",
        content=f"Content for {cid}",
    )


def test_reciprocal_rank_fusion_math():
    """RRF correctly aggregates 1 / (60 + rank) across multiple rankers."""
    c1 = _make_chunk("c1")
    c2 = _make_chunk("c2")
    c3 = _make_chunk("c3")

    # List A: c1 at rank 1, c2 at rank 2
    list_a = [
        RetrievedChunk(chunk=c1, score=10.0, rank=1, retrieval_method="bm25"),
        RetrievedChunk(chunk=c2, score=5.0, rank=2, retrieval_method="bm25"),
    ]

    # List B: c2 at rank 1, c3 at rank 2
    list_b = [
        RetrievedChunk(chunk=c2, score=0.9, rank=1, retrieval_method="dense"),
        RetrievedChunk(chunk=c3, score=0.8, rank=2, retrieval_method="dense"),
    ]

    fused = reciprocal_rank_fusion([list_a, list_b], rrf_k=60)

    # c2 in both: 1/62 + 1/61 = ~0.032522
    # c1 in A: 1/61 = ~0.016393
    # c3 in B: 1/62 = ~0.016129
    assert len(fused) == 3
    assert fused[0].chunk.id == "c2"
    assert fused[0].rank == 1
    assert pytest.approx(fused[0].score, abs=0.0001) == 0.032522

    assert fused[1].chunk.id == "c1"
    assert fused[1].rank == 2
    assert pytest.approx(fused[1].score, abs=0.0001) == 0.016393

    assert fused[2].chunk.id == "c3"
    assert fused[2].rank == 3
    assert pytest.approx(fused[2].score, abs=0.0001) == 0.016129


def test_reciprocal_rank_fusion_empty_inputs():
    """RRF safely handles empty input lists."""
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


def test_retriever_protocol_conformance():
    """Both FakeRetriever and HybridRetriever satisfy runtime Retriever protocol."""
    fake = FakeRetriever()
    assert isinstance(fake, Retriever)

    hybrid = HybridRetriever()
    assert isinstance(hybrid, Retriever)


@pytest.mark.asyncio
async def test_fake_retriever_behavior():
    """FakeRetriever records queries and returns deterministic canned results."""
    c1 = _make_chunk("c1")
    retrieved = RetrievedChunk(chunk=c1, score=1.0, rank=1, retrieval_method="fake")
    fake = FakeRetriever(canned_chunks=[retrieved])

    res = await fake.retrieve("test query", top_k=5)
    assert len(res) == 1
    assert res[0].chunk.id == "c1"
    assert fake.recorded_queries == ["test query"]


@pytest.fixture(scope="module")
def production_facts() -> list[FactChunk]:
    """Loads all production fact chunks."""
    loader = FactLoader()
    return loader.load_all(include_private=False, include_unindexed=False)


@pytest.mark.asyncio
async def test_hybrid_retriever_production_retrieval(
    production_facts: list[FactChunk],
):
    """HybridRetriever successfully fuses BM25 and Dense on production facts."""
    retriever = HybridRetriever(chunks=production_facts)

    # 1. Exact + semantic query
    results_bug = await retriever.retrieve("hardest bug Redis ETIMEDOUT", top_k=3)
    assert len(results_bug) > 0
    top_ids = [r.chunk.id for r in results_bug]
    assert any("hardest-bug" in tid or "debug-story" in tid for tid in top_ids)
    assert results_bug[0].retrieval_method == "hybrid_rrf"
    assert results_bug[0].rank == 1

    # 2. Academic CGPA query
    results_cgpa = await retriever.retrieve("Aamir's academic CGPA", top_k=3)
    assert len(results_cgpa) > 0
    cgpa_ids = [r.chunk.id for r in results_cgpa]
    assert any(
        "education-degree" in cid or "academic-excellence" in cid for cid in cgpa_ids
    )

    # 3. Blank query returns empty
    assert await retriever.retrieve("", top_k=5) == []
    assert await retriever.retrieve("   ", top_k=5) == []
    assert await retriever.retrieve("FastAPI", top_k=0) == []
