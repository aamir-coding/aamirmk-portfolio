"""Generate precomputed embeddings matrix for production fact chunks.

Produces backend/app/retrieval/facts_embeddings.npz so that the server
never needs to embed all knowledge chunks at runtime, eliminating the 1.2GB
memory spike that caused Render's 512MB OOM crash.
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

# Ensure backend directory is in path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.retrieval.loader import FactLoader  # noqa: E402
from fastembed import TextEmbedding  # noqa: E402


def generate_embeddings() -> Path:
    loader = FactLoader()
    chunks = loader.load_all(include_private=False, include_unindexed=False)
    print(f"Loaded {len(chunks)} production fact chunks.")

    texts = [f"{c.title} {' '.join(c.tags)} {c.content}" for c in chunks]
    chunk_ids = [c.id for c in chunks]

    print("Embedding texts with TextEmbedding(threads=1, batch_size=16)...")
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", threads=1)
    raw_embeddings = list(model.embed(texts, batch_size=16))

    mat = np.array(raw_embeddings, dtype=np.float32)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-9)
    normalized_mat = mat / norms

    out_path = backend_dir / "app" / "retrieval" / "facts_embeddings.npz"
    np.savez_compressed(out_path, ids=np.array(chunk_ids), matrix=normalized_mat)
    print(
        f"Saved precomputed index to {out_path} ({out_path.stat().st_size / 1024:.1f} KB)."
    )
    return out_path


if __name__ == "__main__":
    generate_embeddings()
