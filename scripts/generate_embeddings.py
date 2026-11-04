"""Rebuild the public fact index and provenance using cached ONNX assets only."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

# Ensure backend directory is in path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastembed import TextEmbedding  # noqa: E402

from app.retrieval.artifacts import (  # noqa: E402
    embedding_text,
    model_assets_sha256,
    write_embedding_artifact,
)
from app.retrieval.dense import DEFAULT_EMBEDDING_MODEL  # noqa: E402
from app.retrieval.loader import FactLoader  # noqa: E402


def generate_embeddings(cache_dir: str | None = None) -> Path:
    loader = FactLoader()
    chunks = loader.load_all(include_private=False, include_unindexed=False)
    print(f"Loaded {len(chunks)} production fact chunks.")

    texts = [embedding_text(chunk) for chunk in chunks]

    print("Embedding texts with TextEmbedding(threads=1, batch_size=16)...")
    model = TextEmbedding(
        model_name=DEFAULT_EMBEDDING_MODEL,
        threads=1,
        cache_dir=cache_dir,
        local_files_only=True,
    )
    raw_embeddings = list(model.embed(texts, batch_size=16))

    mat = np.array(raw_embeddings, dtype=np.float32)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-9)
    normalized_mat = mat / norms

    out_path = backend_dir / "app" / "retrieval" / "facts_embeddings.npz"
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo_root, text=True
        ).strip()
    )
    manifest = write_embedding_artifact(
        out_path,
        chunks,
        normalized_mat,
        model_name=DEFAULT_EMBEDDING_MODEL,
        model_assets_sha256=model_assets_sha256(model),
        source_commit=commit,
        source_dirty=dirty,
    )
    print(
        f"Saved precomputed index to {out_path} "
        f"({out_path.stat().st_size / 1024:.1f} KB)."
    )
    print(f"Corpus SHA-256: {manifest.corpus_sha256}")
    print(f"Model assets SHA-256: {manifest.model_assets_sha256}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rebuild embeddings using cached local assets only."
    )
    parser.add_argument("--cache-dir", help="Existing FastEmbed model cache directory")
    generate_embeddings(cache_dir=parser.parse_args().cache_dir)
