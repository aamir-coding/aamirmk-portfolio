"""Content-addressed index loading must never repair itself with model calls."""

from pathlib import Path

import numpy as np
import pytest

from app.retrieval.artifacts import (
    IndexArtifactError,
    load_embedding_artifact,
    write_embedding_artifact,
)
from app.retrieval.dense import DenseIndex
from app.retrieval.models import FactChunk


@pytest.fixture
def chunks() -> list[FactChunk]:
    return [
        FactChunk(id="python", type="skill", title="Python", content="Working Python"),
        FactChunk(id="aws", type="skill", title="AWS", content="No hands-on AWS"),
    ]


def write_index(path: Path, chunks: list[FactChunk]) -> None:
    write_embedding_artifact(
        path,
        chunks,
        np.eye(2, dtype=np.float32),
        model_name="test/model",
        model_assets_sha256="a" * 64,
    )


def test_valid_index_can_be_loaded_in_caller_order(
    tmp_path: Path,
    chunks: list[FactChunk],
) -> None:
    path = tmp_path / "index.npz"
    write_index(path, chunks)
    matrix, manifest = load_embedding_artifact(
        path, list(reversed(chunks)), model_name="test/model"
    )
    np.testing.assert_array_equal(matrix, np.eye(2, dtype=np.float32)[::-1])
    assert manifest.model_assets_sha256 == "a" * 64
    assert manifest.chunk_ids == ["python", "aws"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("content", "Actually different evidence"),
        ("title", "A different title"),
        ("tags", ["new-tag"]),
        ("draft", False),
        ("source_url", "https://example.test/changed"),
    ],
)
def test_same_id_edits_invalidate_index(
    tmp_path: Path,
    chunks: list[FactChunk],
    field: str,
    value: object,
) -> None:
    path = tmp_path / "index.npz"
    write_index(path, chunks)
    changed = [chunks[0].model_copy(update={field: value}), chunks[1]]
    with pytest.raises(IndexArtifactError, match="corpus|input"):
        load_embedding_artifact(path, changed, model_name="test/model")


def test_model_change_invalidates_index(
    tmp_path: Path, chunks: list[FactChunk]
) -> None:
    path = tmp_path / "index.npz"
    write_index(path, chunks)
    with pytest.raises(IndexArtifactError, match="model"):
        load_embedding_artifact(path, chunks, model_name="other/model")


@pytest.mark.parametrize(
    "kind", ["missing", "legacy", "corrupt", "truncated", "matrix", "ids"]
)
def test_unproven_artifacts_fail_explicitly(
    tmp_path: Path,
    chunks: list[FactChunk],
    kind: str,
) -> None:
    path = tmp_path / "index.npz"
    if kind == "legacy":
        np.savez_compressed(path, ids=[c.id for c in chunks], matrix=np.eye(2))
    elif kind == "corrupt":
        path.write_bytes(b"not an npz")
    elif kind == "truncated":
        write_index(path, chunks)
        path.write_bytes(path.read_bytes()[:-30])
    elif kind in {"matrix", "ids"}:
        write_index(path, chunks)
        with np.load(path, allow_pickle=False) as archive:
            data = {key: archive[key] for key in archive.files}
        if kind == "matrix":
            data["matrix"] = data["matrix"][::-1]
        else:
            data["ids"] = np.array(["python", "python"])
        np.savez_compressed(path, **data)
    with pytest.raises(IndexArtifactError, match="rebuild|Rebuild"):
        load_embedding_artifact(path, chunks, model_name="test/model")


@pytest.mark.parametrize(
    "matrix",
    [
        np.array([[np.nan, 0], [0, 1]], dtype=np.float32),
        np.array([[0, 0], [0, 1]], dtype=np.float32),
        np.array([[2, 0], [0, 1]], dtype=np.float32),
        np.ones((1, 2), dtype=np.float32),
    ],
)
def test_builder_rejects_invalid_vectors(
    tmp_path: Path,
    chunks: list[FactChunk],
    matrix: np.ndarray,
) -> None:
    with pytest.raises(IndexArtifactError):
        write_embedding_artifact(
            tmp_path / "index.npz",
            chunks,
            matrix,
            model_name="test/model",
            model_assets_sha256="a" * 64,
        )


def test_runtime_never_embeds_missing_or_stale_corpus(
    tmp_path: Path,
    chunks: list[FactChunk],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import fastembed

    def unexpected_model(**kwargs: object) -> None:
        pytest.fail("Invalid artifacts must fail before any model initialization")

    monkeypatch.setattr(fastembed, "TextEmbedding", unexpected_model)
    path = tmp_path / "index.npz"
    with pytest.raises(IndexArtifactError):
        DenseIndex(chunks, embeddings_path=path)
    write_index(path, chunks)
    with pytest.raises(IndexArtifactError):
        DenseIndex(
            chunks,
            model_name="test/model",
            embeddings_path=path.with_suffix(".missing"),
        )
    with pytest.raises(IndexArtifactError):
        DenseIndex([chunks[0]], model_name="test/model", embeddings_path=path)


def test_runtime_model_load_is_local_and_checks_model_assets(
    tmp_path: Path,
    chunks: list[FactChunk],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import fastembed

    path = tmp_path / "index.npz"
    write_index(path, chunks)
    seen: dict[str, object] = {}

    def unavailable_model(**kwargs: object) -> None:
        seen.update(kwargs)
        raise ValueError("cached assets absent")

    monkeypatch.setattr(fastembed, "TextEmbedding", unavailable_model)
    index = DenseIndex(chunks, model_name="test/model", embeddings_path=path)
    with pytest.raises(IndexArtifactError, match="local|cached"):
        index.search("python")
    assert seen["local_files_only"] is True


def test_model_asset_change_cannot_query_existing_index(
    tmp_path: Path,
    chunks: list[FactChunk],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import fastembed

    path = tmp_path / "index.npz"
    write_index(path, chunks)
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"different model")

    class UnexpectedQueryModel:
        model = type("CachedModel", (), {"_model_dir": model_dir})()

        def embed(self, texts: list[str], **kwargs: object) -> None:
            pytest.fail("Changed weights must be rejected before query embedding")

    monkeypatch.setattr(
        fastembed, "TextEmbedding", lambda **kwargs: UnexpectedQueryModel()
    )
    index = DenseIndex(chunks, model_name="test/model", embeddings_path=path)
    with pytest.raises(IndexArtifactError, match="model assets"):
        index.search("python")
