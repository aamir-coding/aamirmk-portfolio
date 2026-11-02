"""Retriever protocol seam and deterministic test fake.

Defines the core interface decoupling endpoint logic from retrieval implementations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.retrieval.models import FactChunk, RetrievedChunk


@runtime_checkable
class Retriever(Protocol):
    """Deep module interface for factual context retrieval."""

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Retrieve top-k relevant fact chunks for a recruiter query."""
        ...


class FakeRetriever:
    """Deterministic, zero-cost fake retriever for fast test isolation."""

    def __init__(
        self,
        canned_chunks: list[RetrievedChunk] | None = None,
        default_facts: list[FactChunk] | None = None,
    ) -> None:
        """Initialize FakeRetriever with optional canned results."""
        self.canned_chunks = canned_chunks
        self.default_facts = default_facts or []
        self.recorded_queries: list[str] = []

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Record the query and return canned or mocked results."""
        self.recorded_queries.append(query)

        if self.canned_chunks is not None:
            return self.canned_chunks[:top_k]

        results: list[RetrievedChunk] = []
        for rank_idx, fact in enumerate(self.default_facts[:top_k], start=1):
            results.append(
                RetrievedChunk(
                    chunk=fact,
                    score=round(1.0 / rank_idx, 4),
                    rank=rank_idx,
                    retrieval_method="fake",
                )
            )
        return results


_retriever_instance: Retriever | None = None


def get_retriever() -> Retriever:
    """FastAPI dependency supplying the active Retriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        from app.retrieval.hybrid import HybridRetriever
        from app.retrieval.loader import FactLoader

        loader = FactLoader()
        chunks = loader.load_all(include_private=False, include_unindexed=False)
        _retriever_instance = HybridRetriever(chunks=chunks)
    return _retriever_instance


def set_retriever(retriever: Retriever | None) -> None:
    """Set or override the active Retriever instance."""
    global _retriever_instance
    _retriever_instance = retriever
