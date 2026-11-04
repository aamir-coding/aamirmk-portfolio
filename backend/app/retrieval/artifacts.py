"""Validated embedding artifacts shared by the offline builder and runtime loader."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Literal
from zipfile import BadZipFile
from zlib import error as ZlibError

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from app.retrieval.models import FactChunk

Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
REBUILD_HINT = (
    "Rebuild with python scripts/generate_embeddings.py using cached model assets."
)


class IndexArtifactError(ValueError):
    """The index or local model cannot establish compatible build provenance."""


class EmbeddingManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    input_format: Literal["title-tags-content-v1"] = "title-tags-content-v1"
    model_name: str
    fastembed_version: str
    model_assets_sha256: Sha256
    corpus_sha256: Sha256
    inputs_sha256: Sha256
    matrix_sha256: Sha256
    chunk_ids: list[str]
    dimensions: int = Field(gt=0)
    built_at: datetime
    source_commit: str | None = None
    source_dirty: bool | None = None


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def embedding_text(chunk: FactChunk) -> str:
    return f"{chunk.title} {' '.join(chunk.tags)} {chunk.content}"


def corpus_sha256(chunks: list[FactChunk]) -> str:
    return canonical_sha256(
        [chunk.model_dump(mode="json") for chunk in sorted(chunks, key=lambda c: c.id)]
    )


def _inputs_sha256(chunks: list[FactChunk], model_name: str) -> str:
    return canonical_sha256(
        {
            "model": model_name,
            "format": "title-tags-content-v1",
            "inputs": {chunk.id: embedding_text(chunk) for chunk in chunks},
        }
    )


def model_assets_sha256(model: object) -> str:
    # FastEmbed 0.9.1 exposes no public accessor for its resolved snapshot directory.
    directory = getattr(getattr(model, "model", None), "_model_dir", None)
    if directory is None or not Path(directory).is_dir():
        raise IndexArtifactError(f"Cannot inspect local model assets. {REBUILD_HINT}")
    directory = Path(directory)
    files = {
        path.relative_to(directory).as_posix(): file_sha256(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file()
        and not any(part.startswith(".") for part in path.relative_to(directory).parts)
    }
    if not any(name.endswith(".onnx") for name in files):
        raise IndexArtifactError(f"Missing local ONNX model assets. {REBUILD_HINT}")
    return canonical_sha256(files)


def _validate_matrix(matrix: NDArray[np.float32], rows: int) -> None:
    if (
        matrix.dtype != np.float32
        or matrix.ndim != 2
        or matrix.shape[0] != rows
        or matrix.shape[1] == 0
        or not np.isfinite(matrix).all()
        or not np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-5)
    ):
        raise IndexArtifactError(
            f"Invalid normalized float32 embedding matrix. {REBUILD_HINT}"
        )


def write_embedding_artifact(
    path: Path,
    chunks: list[FactChunk],
    matrix: NDArray[np.float32],
    *,
    model_name: str,
    model_assets_sha256: str,
    source_commit: str | None = None,
    source_dirty: bool | None = None,
) -> EmbeddingManifest:
    ids = [chunk.id for chunk in chunks]
    if not ids or len(ids) != len(set(ids)):
        raise IndexArtifactError(
            "Embedding inputs must have nonempty, unique chunk IDs."
        )
    _validate_matrix(matrix, len(chunks))
    manifest = EmbeddingManifest(
        model_name=model_name,
        fastembed_version=version("fastembed"),
        model_assets_sha256=model_assets_sha256,
        corpus_sha256=corpus_sha256(chunks),
        inputs_sha256=_inputs_sha256(chunks, model_name),
        matrix_sha256=hashlib.sha256(matrix.tobytes(order="C")).hexdigest(),
        chunk_ids=ids,
        dimensions=matrix.shape[1],
        built_at=datetime.now(UTC),
        source_commit=source_commit,
        source_dirty=source_dirty,
    )
    temporary = path.with_suffix(".npz.tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(
            stream,
            ids=np.array(ids),
            matrix=matrix,
            manifest=np.array(manifest.model_dump_json()),
        )
    temporary.replace(path)
    return manifest


def load_embedding_artifact(
    path: Path,
    chunks: list[FactChunk],
    *,
    model_name: str,
) -> tuple[NDArray[np.float32], EmbeddingManifest]:
    try:
        with np.load(path, allow_pickle=False) as archive:
            manifest = EmbeddingManifest.model_validate_json(
                str(archive["manifest"].item())
            )
            ids = archive["ids"].tolist()
            matrix = archive["matrix"]
        current_ids = [chunk.id for chunk in chunks]
        if (
            ids != manifest.chunk_ids
            or len(ids) != len(set(ids))
            or len(current_ids) != len(set(current_ids))
            or set(ids) != set(current_ids)
        ):
            raise ValueError("chunk IDs differ from the indexed corpus")
        if manifest.model_name != model_name or manifest.fastembed_version != version(
            "fastembed"
        ):
            raise ValueError("embedding model or FastEmbed version differs")
        if manifest.corpus_sha256 != corpus_sha256(chunks):
            raise ValueError("corpus fingerprint differs")
        if manifest.inputs_sha256 != _inputs_sha256(chunks, model_name):
            raise ValueError("embedding input fingerprint differs")
        _validate_matrix(matrix, len(ids))
        if (
            matrix.shape[1] != manifest.dimensions
            or hashlib.sha256(matrix.tobytes(order="C")).hexdigest()
            != manifest.matrix_sha256
        ):
            raise ValueError("matrix fingerprint or dimensions differ")
        positions = {cid: position for position, cid in enumerate(ids)}
        return matrix[[positions[cid] for cid in current_ids]], manifest
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        BadZipFile,
        EOFError,
        ZlibError,
    ) as exc:
        raise IndexArtifactError(
            f"Unusable embedding artifact: {exc}. {REBUILD_HINT}"
        ) from exc
