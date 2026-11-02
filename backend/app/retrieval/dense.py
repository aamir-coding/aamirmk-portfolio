"""Dense semantic retrieval index using fastembed ONNX embeddings and NumPy."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from app.retrieval.models import FactChunk, RetrievedChunk

if TYPE_CHECKING:
    from fastembed import TextEmbedding

# Default CPU-optimized ONNX model (384 dimensions, ~130MB on disk)
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Default precomputed embeddings matrix path (saves 1.2GB RAM and 12s CPU at boot)
DEFAULT_EMBEDDINGS_PATH = Path(__file__).resolve().parent / "facts_embeddings.npz"


class DenseIndex:
    """In-process semantic vector index using fastembed and NumPy dot-products."""

    def __init__(
        self,
        chunks: list[FactChunk] | None = None,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        embedding_model: Any | None = None,
        cache_dir: str | None = None,
        embeddings_path: str | Path | None = DEFAULT_EMBEDDINGS_PATH,
    ) -> None:
        """Initialize dense index.

        Args:
            chunks: Optional list of FactChunks to index immediately.
            model_name: Model identifier on HuggingFace Hub / fastembed.
            embedding_model: Optional injected TextEmbedding instance.
            cache_dir: Optional custom directory to cache the ONNX model files.
            embeddings_path: Path to precomputed .npz file containing IDs and matrix.
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.embeddings_path = Path(embeddings_path) if embeddings_path else None
        self._model = embedding_model
        self.chunks: list[FactChunk] = []
        self._matrix: np.ndarray | None = None

        if chunks:
            self.index(chunks)

    def _get_model(self) -> TextEmbedding:
        """Lazy-initialize the Fastembed ONNX model with single-thread arena."""
        if self._model is None:
            from fastembed import TextEmbedding

            # Single thread prevents multi-core arena memory explosion (>512MB)
            self._model = TextEmbedding(
                model_name=self.model_name,
                cache_dir=self.cache_dir,
                threads=1,
            )
        return self._model

    def _embed_texts(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        """Embed a list of text strings into an L2-normalized 2D numpy array."""
        model = self._get_model()
        try:
            raw_embeddings = list(model.embed(texts, batch_size=batch_size))
        except TypeError:
            raw_embeddings = list(model.embed(texts))
        mat = np.array(raw_embeddings, dtype=np.float32)

        # L2-normalize vectors so dot product equals cosine similarity
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-9)
        return mat / norms

    def index(self, chunks: list[FactChunk]) -> None:
        """Build or load normalized dense embedding matrix over fact chunks."""
        self.chunks = list(chunks)
        if not self.chunks:
            self._matrix = None
            return

        # Fast path: load precomputed embeddings if available and matching
        if (
            self.embeddings_path
            and self.embeddings_path.exists()
            and self._model is None
        ):
            try:
                data = np.load(self.embeddings_path)
                saved_ids = [str(x) for x in data["ids"]]
                saved_matrix = data["matrix"]
                id_to_row = {cid: saved_matrix[i] for i, cid in enumerate(saved_ids)}

                if all(c.id in id_to_row for c in self.chunks):
                    self._matrix = np.array(
                        [id_to_row[c.id] for c in self.chunks], dtype=np.float32
                    )
                    return
            except Exception:
                # If precomputed load fails or is incompatible, fallback to computing
                pass

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

        # Embed single query text with single-threaded ONNX session
        q_mat = self._embed_texts([clean_query], batch_size=1)
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
