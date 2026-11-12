"""Hybrid retrieval engine combining BM25 keyword search and dense semantic search.

Uses Cormack's Reciprocal Rank Fusion (RRF, k=60) to combine ranked lists without
requiring score scale calibration. CPU-bound searches are dispatched to worker threads.
"""

from __future__ import annotations

import asyncio

from app.retrieval.bm25 import BM25Index
from app.retrieval.dense import DenseIndex
from app.retrieval.models import FactChunk, RetrievedChunk


def reciprocal_rank_fusion(
    ranked_lists: list[list[RetrievedChunk]],
    rrf_k: int = 60,
) -> list[RetrievedChunk]:
    """Combine multiple ranked lists using Reciprocal Rank Fusion.

    Formula:
        RRF_score(d) = sum_{m in methods} ( 1.0 / (rrf_k + rank_m(d)) )

    Args:
        ranked_lists: Lists of RetrievedChunk results from distinct search methods.
        rrf_k: Smoothing constant (default 60, per Cormack et al. 2009).

    Returns:
        Consolidated list of RetrievedChunks sorted descending by RRF score.
    """
    scores: dict[str, float] = {}
    chunk_map: dict[str, FactChunk] = {}
    dense_similarities: dict[str, float] = {}

    for ranked_list in ranked_lists:
        for item in ranked_list:
            cid = item.chunk.id
            chunk_map[cid] = item.chunk
            if item.retrieval_method == "dense":
                dense_similarities[cid] = item.score
            # rank is 1-based
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + item.rank))

    # Sort descending by aggregated RRF score
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    fused_results: list[RetrievedChunk] = []
    for rank_idx, (cid, score) in enumerate(sorted_items, start=1):
        fused_results.append(
            RetrievedChunk(
                chunk=chunk_map[cid],
                score=round(score, 6),
                rank=rank_idx,
                retrieval_method="hybrid_rrf",
                dense_similarity=dense_similarities.get(cid),
            )
        )

    return fused_results


class HybridRetriever:
    """In-process hybrid retriever satisfying the Retriever protocol seam."""

    def __init__(
        self,
        chunks: list[FactChunk] | None = None,
        bm25: BM25Index | None = None,
        dense: DenseIndex | None = None,
        rrf_k: int = 60,
        candidates_multiplier: int = 4,
    ) -> None:
        """Initialize hybrid retriever.

        Args:
            chunks: Fact chunks to index if bm25 or dense indexes are not provided.
            bm25: Optional pre-configured BM25Index.
            dense: Optional pre-configured DenseIndex.
            rrf_k: Smoothing constant for Reciprocal Rank Fusion (default 60).
            candidates_multiplier: Multiplier to fetch deeper candidates for fusion.
        """
        self.rrf_k = rrf_k
        self.candidates_multiplier = candidates_multiplier

        if bm25 is not None:
            self.bm25 = bm25
        elif chunks is not None:
            self.bm25 = BM25Index(chunks)
        else:
            self.bm25 = BM25Index()

        if dense is not None:
            self.dense = dense
        elif chunks is not None:
            self.dense = DenseIndex(chunks)
        else:
            self.dense = DenseIndex()

    def _sync_retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Perform synchronous BM25 and dense searches, then fuse with RRF."""
        if top_k <= 0 or not query.strip():
            return []

        # Retrieve a wider candidate pool from both indexes to ensure overlap
        candidate_k = max(top_k * self.candidates_multiplier, 20)

        bm25_results = self.bm25.search(query, top_k=candidate_k)
        dense_results = self.dense.search(query, top_k=candidate_k)

        fused = reciprocal_rank_fusion([bm25_results, dense_results], rrf_k=self.rrf_k)
        return fused[:top_k]

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Retrieve top-k relevant fact chunks using hybrid RRF fusion.

        Offloads CPU-bound tokenization and ONNX inference to a thread pool to avoid
        blocking the ASGI event loop.
        """
        return await asyncio.to_thread(self._sync_retrieve, query, top_k)
