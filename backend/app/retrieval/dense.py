"""Dense semantic retrieval index using fastembed ONNX embeddings and NumPy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from app.retrieval.models import FactChunk, RetrievedChunk

if TYPE_CHECKING:
    from fastembed import TextEmbedding

# Default CPU-optimized ONNX model (384 dimensions, ~130MB on disk)
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


class DenseIndex:
    """In-process semantic vector index using fastembed and NumPy dot-products."""

    def __init__(
        self,
        chunks: list[FactChunk] | None = None,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        embedding_model: Any | None = None,
        cache_dir: str | None = None,
    ) -> None:
        """Initialize dense index.

        Args:
            chunks: Optional list of FactChunks to index immediately.
            model_name: Model identifier on HuggingFace Hub / fastembed.
            embedding_model: Optional injected TextEmbedding instance.
            cache_dir: Optional custom directory to cache the ONNX model files.
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model = embedding_model
        self.chunks: list[FactChunk] = []
        self._matrix: np.ndarray | None = None

        if chunks:
            self.index(chunks)

    def _get_model(self) -> TextEmbedding:
        """Lazy-initialize the Fastembed ONNX model on first access."""
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(
                model_name=self.model_name,
                cache_dir=self.cache_dir,
            )
        return self._model

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed a list of text strings into an L2-normalized 2D numpy array."""
        model = self._get_model()
        raw_embeddings = list(model.embed(texts))
        mat = np.array(raw_embeddings, dtype=np.float32)

        # L2-normalize vectors so dot product equals cosine similarity
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-9)
        return mat / norms

    def index(self, chunks: list[FactChunk]) -> None:
        """Build normalized dense embedding matrix over fact chunks."""
        self.chunks = list(chunks)
        if not self.chunks:
            self._matrix = None
            return

        texts: list[str] = []
        for chunk in self.chunks:
            tag_str = " ".join(chunk.tags)
            texts.append(f"{chunk.title} {tag_str} {chunk.content}")

        self._matrix = self._embed_texts(texts)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Search chunks by cosine similarity to the query embedding."""
        if not self.chunks or self._matrix is None or top_k <= 0:
            return []

        clean_query = query.strip()
        if not clean_query:
            return []

        # Embed single query text
        q_mat = self._embed_texts([clean_query])
        q_vec = q_mat[0]

        # Compute cosine similarity across all document vectors via dot product
        scores = np.dot(self._matrix, q_vec)

        # Rank indices descending by score
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        results: list[RetrievedChunk] = []
        for rank_idx, idx in enumerate(ranked_indices, start=1):
            results.append(
                RetrievedChunk(
                    chunk=self.chunks[idx],
                    score=round(float(scores[idx]), 4),
                    rank=rank_idx,
                    retrieval_method="dense",
                )
            )

        return results
