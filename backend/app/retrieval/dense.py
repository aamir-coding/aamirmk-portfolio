"""Dense semantic retrieval index using fastembed ONNX embeddings and NumPy."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from app.retrieval.artifacts import (
    EmbeddingManifest,
    IndexArtifactError,
    embedding_text,
    load_embedding_artifact,
    model_assets_sha256,
)
from app.retrieval.models import FactChunk, RetrievedChunk

if TYPE_CHECKING:
    from fastembed import TextEmbedding

# Default CPU-optimized ONNX model (384 dimensions, ~130MB on disk)
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Default precomputed embeddings matrix path (saves 1.2GB RAM and 12s CPU at boot)
DEFAULT_EMBEDDINGS_PATH = Path(__file__).resolve().parent / "facts_embeddings.npz"

# Persistent model cache directory inside repository root
# Avoids data loss on platforms like Render where /tmp is discarded across build/deploy
DEFAULT_PROJECT_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "fastembed"


def resolve_cache_dir(explicit: str | Path | None = None) -> str | None:
    """Resolve local model cache directory with persistence fallback.

    Precedence:
    1. Explicitly passed cache_dir.
    2. FASTEMBED_CACHE_PATH environment variable.
    3. Persistent repository cache at backend/.cache/fastembed (if it exists).
    4. System temporary directory (fastembed_cache) if it exists.
    5. Persistent repository cache default.
    """
    if explicit is not None:
        return str(explicit)
    if env_path := os.environ.get("FASTEMBED_CACHE_PATH"):
        return env_path
    if DEFAULT_PROJECT_CACHE_DIR.is_dir() and any(DEFAULT_PROJECT_CACHE_DIR.iterdir()):
        return str(DEFAULT_PROJECT_CACHE_DIR)
    temp_dir = Path(tempfile.gettempdir()) / "fastembed_cache"
    if temp_dir.is_dir() and any(temp_dir.iterdir()):
        return str(temp_dir)
    return str(DEFAULT_PROJECT_CACHE_DIR)


def ensure_model_cached(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    cache_dir: str | Path | None = None,
) -> None:
    """Ensure ONNX embedding model assets exist locally before strictly local loading.

    If cached files are missing (e.g. ephemeral container startup where build-time /tmp
    was discarded by the hosting provider), provisions them with single-thread arena.
    """
    resolved = resolve_cache_dir(cache_dir)
    from fastembed import TextEmbedding

    try:
        model = TextEmbedding(
            model_name=model_name,
            cache_dir=resolved,
            threads=1,
            local_files_only=True,
        )
        model_assets_sha256(model)
        return
    except Exception:
        pass

    if resolved:
        Path(resolved).mkdir(parents=True, exist_ok=True)
    model = TextEmbedding(
        model_name=model_name,
        cache_dir=resolved,
        threads=1,
        local_files_only=False,
    )
    model_assets_sha256(model)


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
        self.cache_dir = resolve_cache_dir(cache_dir)
        self.embeddings_path = Path(embeddings_path) if embeddings_path else None
        self._model = embedding_model
        self._injected_model = embedding_model is not None
        self._manifest: EmbeddingManifest | None = None
        self._model_assets_sha256: str | None = None
        self.chunks: list[FactChunk] = []
        self._matrix: np.ndarray | None = None

        if chunks:
            self.index(chunks)

    def _get_model(self) -> TextEmbedding:
        """Lazy-initialize the Fastembed ONNX model with single-thread arena."""
        if self._model is None:
            from fastembed import TextEmbedding

            try:
                model = TextEmbedding(
                    model_name=self.model_name,
                    cache_dir=self.cache_dir,
                    threads=1,
                    local_files_only=True,
                )
                fingerprint = model_assets_sha256(model)
            except Exception as exc:
                raise IndexArtifactError(
                    "Cannot load cached local embedding model assets; "
                    "provision them at build time."
                ) from exc
            self._model = model
            self._model_assets_sha256 = fingerprint
        if not self._injected_model and (
            self._manifest is None
            or self._model_assets_sha256 != self._manifest.model_assets_sha256
        ):
            raise IndexArtifactError(
                "Cached model assets differ from the embedding index build."
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
        if not chunks:
            self.chunks = []
            self._matrix = None
            self._manifest = None
            return

        if self._injected_model:
            matrix = self._embed_texts([embedding_text(chunk) for chunk in chunks])
            manifest = None
        else:
            if self.embeddings_path is None:
                raise IndexArtifactError(
                    "A precomputed embedding artifact is required."
                )
            matrix, manifest = load_embedding_artifact(
                self.embeddings_path,
                chunks,
                model_name=self.model_name,
            )
        self.chunks = list(chunks)
        self._matrix = matrix
        self._manifest = manifest

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
