"""Unit and integration tests for DenseIndex semantic vector retrieval."""

from __future__ import annotations

import numpy as np
import pytest

from app.retrieval.dense import DenseIndex
from app.retrieval.loader import FactLoader
from app.retrieval.models import FactChunk


class MockEmbeddingModel:
    """Fast, deterministic mock for unit testing DenseIndex without ONNX runtime."""

    def __init__(self, vocab_map: dict[str, list[float]]) -> None:
        self.vocab_map = vocab_map

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        results: list[np.ndarray] = []
        for text in texts:
            matched = False
            for key, vec in self.vocab_map.items():
                if key.lower() in text.lower():
                    results.append(np.array(vec, dtype=np.float32))
                    matched = True
                    break
            if not matched:
                results.append(np.array([0.1, 0.1, 0.1], dtype=np.float32))
        return results


def test_dense_index_with_mock_embedding():
    """DenseIndex normalizes and ranks mock embeddings by cosine similarity."""
    mock_model = MockEmbeddingModel(
        {
            "fastapi": [1.0, 0.0, 0.0],
            "react": [0.0, 1.0, 0.0],
            "docker": [0.0, 0.0, 1.0],
        }
    )

    c1 = FactChunk(id="c1", type="skill", title="FastAPI", content="FastAPI")
    c2 = FactChunk(id="c2", type="skill", title="React", content="React")
    c3 = FactChunk(id="c3", type="skill", title="Docker", content="Docker")

    index = DenseIndex(chunks=[c1, c2, c3], embedding_model=mock_model)

    # Search for FastAPI -> should match c1 with score ~1.0
    results = index.search("fastapi backend", top_k=2)
    assert len(results) == 2
    assert results[0].chunk.id == "c1"
    assert results[0].rank == 1
    assert results[0].retrieval_method == "dense"
    assert pytest.approx(results[0].score, abs=0.01) == 1.0


def test_dense_index_edge_cases():
    """DenseIndex handles empty index, blank query, and zero top_k cleanly."""
    mock_model = MockEmbeddingModel({"a": [1.0, 0.0]})
    empty_index = DenseIndex(embedding_model=mock_model)
    assert empty_index.search("test") == []

    chunk = FactChunk(id="c1", type="skill", title="A", content="A")
    index = DenseIndex(chunks=[chunk], embedding_model=mock_model)
    assert index.search("") == []
    assert index.search("   ") == []
    assert index.search("test", top_k=0) == []
    assert index.search("test", top_k=-1) == []


@pytest.fixture(scope="module")
def production_facts() -> list[FactChunk]:
    """Loads all production fact chunks."""
    loader = FactLoader()
    return loader.load_all(include_private=False, include_unindexed=False)


def test_dense_semantic_retrieval_production(production_facts: list[FactChunk]):
    """DenseIndex retrieves conceptual matches on production facts."""
    index = DenseIndex(chunks=production_facts)

    # 1. Semantic query on networking/timeout issue (no exact ETIMEDOUT keyword)
    results_timeout = index.search(
        "How did Aamir troubleshoot network connection drops between services?",
        top_k=3,
    )
    assert len(results_timeout) > 0
    top_ids = [r.chunk.id for r in results_timeout]
    assert any("hardest-bug" in tid or "debug-story" in tid for tid in top_ids)

    # 2. Semantic query on insurance prediction ML (conceptual match)
    results_ml = index.search(
        "What machine learning model was used to calculate insurance quotes?",
        top_k=3,
    )
    assert len(results_ml) > 0
    ml_ids = [r.chunk.id for r in results_ml]
    assert any("health-premium" in tid for tid in ml_ids)

    # 3. Semantic query on competitive contest placement
    results_contest = index.search(
        "Did Aamir win any programming competitions or algorithmic tournaments?",
        top_k=3,
    )
    assert len(results_contest) > 0
    contest_ids = [r.chunk.id for r in results_contest]
    assert "achieve-graph-contest" in contest_ids

    # Verify score range and ranking integrity
    for r in results_contest:
        assert r.retrieval_method == "dense"
        assert -1.0 <= r.score <= 1.0
        assert r.rank >= 1
