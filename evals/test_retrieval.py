"""Retrieval evaluation suite and latency benchmarks.

Evaluates the in-process hybrid retriever against the 45 labeled test queries
in evals/seed_questions.yaml, asserting Hit Rate@5 >= 90%, MRR >= 0.80, and
average CPU latency < 25ms.
"""

from __future__ import annotations

import sys
import time
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
    """Benchmark full retrieval suite asserting Hit Rate@5, MRR, and latency targets."""
    # Warm up ONNX session so benchmark measures steady-state latency
    await retriever.retrieve("warmup query", top_k=1)

    hits = 0
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []
    category_stats: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []

    for item in _QUESTIONS:
        q_id = item["id"]
        query = item["question"]
        expected = item.get("expected_chunk_ids", [])
        intent = item.get("intent_tag", "other")

        t_start = time.perf_counter()
        results = await retriever.retrieve(query, top_k=5)
        elapsed_ms = (time.perf_counter() - t_start) * 1000
        latencies_ms.append(elapsed_ms)

        retrieved_ids = [r.chunk.id for r in results]

        first_rank: int | None = None
        for rank, r_id in enumerate(retrieved_ids, start=1):
            if r_id in expected:
                first_rank = rank
                break

        if first_rank is not None:
            hits += 1
            rr = 1.0 / first_rank
        else:
            rr = 0.0
            failures.append(
                {
                    "id": q_id,
                    "query": query,
                    "expected": expected,
                    "retrieved": retrieved_ids,
                }
            )

        reciprocal_ranks.append(rr)

        if intent not in category_stats:
            category_stats[intent] = {"total": 0, "hits": 0, "rr_sum": 0.0}
        category_stats[intent]["total"] += 1
        if first_rank is not None:
            category_stats[intent]["hits"] += 1
        category_stats[intent]["rr_sum"] += rr

    total = len(_QUESTIONS)
    hit_rate = hits / total
    mrr = sum(reciprocal_ranks) / total
    latencies_ms.sort()
    avg_latency = sum(latencies_ms) / total
    p50 = latencies_ms[int(total * 0.50)]
    p95 = latencies_ms[int(total * 0.95)]
    p99 = latencies_ms[int(total * 0.99)]

    print(f"\n{'=' * 68}")
    print(f"RETRIEVAL BENCHMARK REPORT ({total} Queries)")
    print(f"{'=' * 68}")
    print(f"Hit Rate@5:  {hits}/{total} = {hit_rate:.2%}  (Target: >= 90.0%)")
    print(f"MRR:         {mrr:.4f}           (Target: >= 0.8000)")
    print(
        f"Latency:     avg={avg_latency:.2f}ms, p50={p50:.2f}ms, p95={p95:.2f}ms, p99={p99:.2f}ms (Target: < 25.0ms)"
    )
    print(f"{'-' * 68}")
    print("Breakdown by Intent:")
    for intent, stats in sorted(category_stats.items()):
        cat_rate = stats["hits"] / stats["total"]
        cat_mrr = stats["rr_sum"] / stats["total"]
        print(
            f"  {intent:15s}: {stats['hits']:2d}/{stats['total']:2d} ({cat_rate:6.1%})  MRR={cat_mrr:.3f}"
        )
    print(f"{'=' * 68}")

    assert hit_rate >= 0.90, f"Hit Rate@5 ({hit_rate:.1%}) below 90% target"
    assert mrr >= 0.80, f"MRR ({mrr:.4f}) below 0.80 target"
    assert avg_latency < 25.0, (
        f"Average latency ({avg_latency:.2f}ms) exceeded 25ms limit"
    )
    assert len(failures) == 0, f"Failed queries: {failures}"


@pytest.mark.asyncio
@pytest.mark.parametrize("item", _QUESTIONS, ids=_QUESTION_IDS)
async def test_retrieval_query_hit(
    retriever: HybridRetriever, item: dict[str, Any]
) -> None:
    """Verify each individual evaluation query retrieves at least one expected chunk in top 5."""
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
