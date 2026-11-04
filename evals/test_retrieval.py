"""Retrieval evaluation suite and latency benchmarks.

Evaluates the hybrid retriever against all 45 legacy development queries.
Portable quality gates are separate from machine-dependent latency reports.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

# Ensure backend package is in python search path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.retrieval.hybrid import HybridRetriever  # noqa: E402
from app.retrieval.loader import FactLoader  # noqa: E402
from evals.run import evaluate_suite, load_legacy_cases  # noqa: E402


def _load_seed_questions() -> list[dict[str, Any]]:
    """Load labeled evaluation questions from seed_questions.yaml."""
    seed_path = _REPO_ROOT / "evals" / "seed_questions.yaml"
    with open(seed_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["questions"]


_QUESTIONS = _load_seed_questions()
_QUESTION_IDS = [q["id"] for q in _QUESTIONS]


@pytest.fixture(scope="module")
def retriever() -> HybridRetriever:
    """Session/module scoped HybridRetriever instance indexing all public facts."""
    loader = FactLoader()
    chunks = loader.load_all(include_private=False, include_unindexed=False)
    assert len(chunks) > 0, "No facts loaded from knowledge base"
    return HybridRetriever(chunks=chunks)


@pytest.mark.asyncio
async def test_retrieval_benchmark_aggregate(retriever: HybridRetriever) -> None:
    """Keep every legacy top-five hit and add the approved top-three quality gate."""
    report = await evaluate_suite(load_legacy_cases(), retriever, require_all_hit5=True)
    print("Legacy development retrieval metrics:", report.metrics.model_dump())
    print(
        "Per-category metrics:",
        {name: item.model_dump() for name, item in report.by_category.items()},
    )
    print("Warm retrieval latency (informational):", report.latency.model_dump())
    assert report.evaluated_cases == len(_QUESTIONS) == 45
    assert report.metrics.recall_at_3.value is None, (
        "Legacy alternative IDs are not exhaustive relevance labels"
    )
    assert report.quality_passed, (
        f"Failed quality gates: {report.failed_quality_checks}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("item", _QUESTIONS, ids=_QUESTION_IDS)
async def test_retrieval_query_hit(
    retriever: HybridRetriever, item: dict[str, Any]
) -> None:
    """Preserve the individual top-five hit regression for every legacy query."""
    query = item["question"]
    expected = item.get("expected_chunk_ids", [])
    results = await retriever.retrieve(query, top_k=5)
    retrieved_ids = [r.chunk.id for r in results]

    intersection = set(retrieved_ids) & set(expected)
    assert len(intersection) > 0, (
        f"Query '{query}' failed to retrieve any expected chunk in top 5.\n"
        f"Expected: {expected}\n"
        f"Retrieved: {retrieved_ids}"
    )


@pytest.mark.asyncio
async def test_adversarial_queries_retrieve_ground_truth(
    retriever: HybridRetriever,
) -> None:
    """Verify adversarial queries retrieve fact chunks that correct false premises."""
    # 1. 35% latency claim
    results_35 = await retriever.retrieve(
        "Did Aamir reduce API latency by 35%?", top_k=5
    )
    ids_35 = [r.chunk.id for r in results_35]
    assert any(
        cid in ids_35
        for cid in ["exp-algouniversity-hardest-bug", "proj-entropy-oj-debug-story"]
    )
    matching_chunk = next(
        r.chunk
        for r in results_35
        if r.chunk.id
        in ["exp-algouniversity-hardest-bug", "proj-entropy-oj-debug-story"]
    )
    assert "35%" in matching_chunk.content
    assert "ETIMEDOUT" in matching_chunk.content

    # 2. False Google employment claim
    results_google = await retriever.retrieve(
        "Aamir worked at Google, correct?", top_k=5
    )
    ids_google = [r.chunk.id for r in results_google]
    assert any(
        cid in ids_google
        for cid in ["achieve-google-cloud-hackathon", "skill-not-claimed"]
    )
    google_chunk = next(
        r.chunk
        for r in results_google
        if r.chunk.id in ["achieve-google-cloud-hackathon", "skill-not-claimed"]
    )
    assert "Google" in google_chunk.content


@pytest.mark.asyncio
async def test_phone_number_recruiter_retrieval(retriever: HybridRetriever) -> None:
    """Verify recruiter requesting contact retrieves profile-contact at rank 1."""
    results = await retriever.retrieve(
        "Can I get Aamir's phone number to schedule a call?", top_k=5
    )
    assert len(results) > 0
    assert results[0].chunk.id == "profile-contact"
