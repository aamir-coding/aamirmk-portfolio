"""Load frozen development cases; held-out content requires explicit opt-in."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from app.retrieval.artifacts import EmbeddingManifest, Sha256, file_sha256
from evals.schemas import CaseModel, CaseSuite, EvalCase, Identifier, Split, Text

DEFAULT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = DEFAULT_ROOT.parent
CASE_FILES = {"development": "development.yaml", "held_out": "held_out.yaml"}


def _text_sha256(path: Path) -> str:
    # Git converts CRLF/LF between Windows checkouts and Linux CI.
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _case_sha256(case: EvalCase) -> str:
    return hashlib.sha256(
        json.dumps(
            case.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


class FrozenCase(CaseModel):
    id: Identifier
    version: int = Field(ge=1)
    group_id: Identifier
    split: Split
    sha256: Sha256


class CorpusChunk(CaseModel):
    id: Identifier
    draft: bool


class CorpusSnapshot(CaseModel):
    schema_version: Literal[1] = 1
    scope: Literal["public_indexed_including_drafts"] = (
        "public_indexed_including_drafts"
    )
    approval_status: Literal["not_factually_approved"] = "not_factually_approved"
    corpus_sha256: Sha256
    chunks: list[CorpusChunk]


class IndexSnapshot(CaseModel):
    artifact_sha256: Sha256
    manifest: EmbeddingManifest


class LegacyQuestion(BaseModel):
    id: Text
    question: Text


class LegacySeeds(BaseModel):
    questions: list[LegacyQuestion]


def _validate_legacy_overlap(cases: list[EvalCase]) -> None:
    reserved = [case for case in cases if case.split == "held_out"]
    if not reserved:
        return
    seeds = LegacySeeds.model_validate(
        yaml.safe_load(
            (DEFAULT_ROOT / "seed_questions.yaml").read_text(encoding="utf-8")
        )
    )
    known = {" ".join(seed.question.casefold().split()) for seed in seeds.questions}
    if any(
        " ".join(case.conversation[-1].content.casefold().split()) in known
        for case in reserved
    ):
        raise ValueError("Held-out inquiry overlaps a known legacy development seed")


class DatasetManifest(CaseModel):
    schema_version: Literal[1] = 1
    text_hash_format: Literal["utf8-universal-newlines-v1"] = (
        "utf8-universal-newlines-v1"
    )
    suite_version: Text
    frozen_at: datetime
    case_files: dict[Literal["development.yaml", "held_out.yaml"], Sha256]
    cases: list[FrozenCase] = Field(min_length=1)
    legacy_seed_sha256: Sha256
    corpus_snapshot_sha256: Sha256
    index_snapshot_sha256: Sha256

    @model_validator(mode="after")
    def disjoint_groups(self) -> DatasetManifest:
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Duplicate frozen case IDs")
        groups = {
            split: {c.group_id for c in self.cases if c.split == split}
            for split in CASE_FILES
        }
        if groups["development"] & groups["held_out"]:
            raise ValueError("Frozen group overlap")
        if set(self.case_files) != set(CASE_FILES.values()):
            raise ValueError("Expected exactly the development and held-out case files")
        return self


def load_manifest(root: Path = DEFAULT_ROOT) -> DatasetManifest:
    return DatasetManifest.model_validate_json(
        (root / "manifests" / "dataset-v1.json").read_text(encoding="utf-8")
    )


def load_cases(
    root: Path = DEFAULT_ROOT, *, include_held_out: bool = False
) -> list[EvalCase]:
    manifest = load_manifest(root)
    selected = (
        CASE_FILES if include_held_out else {"development": CASE_FILES["development"]}
    )
    cases: list[EvalCase] = []
    for split, filename in selected.items():
        path = root / "cases" / filename
        if _text_sha256(path) != manifest.case_files[filename]:
            raise ValueError(f"Case file hash differs from frozen manifest: {filename}")
        suite = CaseSuite.model_validate(
            yaml.safe_load(path.read_text(encoding="utf-8"))
        )
        if suite.version != manifest.suite_version or any(
            c.split != split for c in suite.cases
        ):
            raise ValueError("Case version/split differs from frozen manifest")
        actual = [
            FrozenCase(
                id=c.id,
                version=c.version,
                group_id=c.group_id,
                split=c.split,
                sha256=_case_sha256(c),
            )
            for c in suite.cases
        ]
        if actual != [c for c in manifest.cases if c.split == split]:
            raise ValueError("Case fingerprint differs from frozen manifest")
        cases.extend(suite.cases)
    cases = CaseSuite(version=manifest.suite_version, cases=cases).cases
    _validate_legacy_overlap(cases)
    return cases


def validate_source_ids(cases: list[EvalCase], public_ids: set[str]) -> None:
    for case in cases:
        unknown = set(case.checks.sources.ids) - public_ids
        if unknown:
            raise ValueError(
                f"Unknown/nonpublic sources in {case.id}: {sorted(unknown)}"
            )


def _current_snapshots() -> tuple[CorpusSnapshot, IndexSnapshot]:
    from app.retrieval.artifacts import corpus_sha256, load_embedding_artifact
    from app.retrieval.dense import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDINGS_PATH
    from app.retrieval.loader import FactLoader

    chunks = FactLoader().load_all()
    _, index = load_embedding_artifact(
        DEFAULT_EMBEDDINGS_PATH, chunks, model_name=DEFAULT_EMBEDDING_MODEL
    )
    corpus = CorpusSnapshot(
        corpus_sha256=corpus_sha256(chunks),
        chunks=[
            CorpusChunk(id=c.id, draft=c.draft)
            for c in sorted(chunks, key=lambda c: c.id)
        ],
    )
    index_snapshot = IndexSnapshot(
        artifact_sha256=file_sha256(DEFAULT_EMBEDDINGS_PATH),
        manifest=index,
    )
    return corpus, index_snapshot


def freeze_dataset(root: Path = DEFAULT_ROOT) -> None:
    """Create once; revisions require a reviewed version, never silent refreezing."""
    directory = root / "manifests"
    directory.mkdir(exist_ok=True)
    target = directory / "dataset-v1.json"
    if target.exists():
        raise FileExistsError("Dataset already frozen; review a new version instead")
    suites = []
    for split, name in CASE_FILES.items():
        selected = CaseSuite.model_validate(
            yaml.safe_load((root / "cases" / name).read_text(encoding="utf-8"))
        )
        if any(case.split != split for case in selected.cases):
            raise ValueError(f"Incorrect case file split: {name}")
        suites.append(selected)
    if suites[0].version != suites[1].version:
        raise ValueError("Case file versions differ")
    suite = CaseSuite(
        version=suites[0].version, cases=[c for s in suites for c in s.cases]
    )
    _validate_legacy_overlap(suite.cases)
    corpus, index = _current_snapshots()
    validate_source_ids(suite.cases, {c.id for c in corpus.chunks})
    for name, snapshot in (("corpus-v1.json", corpus), ("index-v1.json", index)):
        (directory / name).write_text(
            snapshot.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
    manifest = DatasetManifest(
        suite_version=suite.version,
        frozen_at=datetime.now(UTC),
        case_files={
            name: _text_sha256(root / "cases" / name) for name in CASE_FILES.values()
        },
        cases=[
            FrozenCase(
                id=c.id,
                version=c.version,
                group_id=c.group_id,
                split=c.split,
                sha256=_case_sha256(c),
            )
            for c in suite.cases
        ],
        legacy_seed_sha256=_text_sha256(DEFAULT_ROOT / "seed_questions.yaml"),
        corpus_snapshot_sha256=_text_sha256(directory / "corpus-v1.json"),
        index_snapshot_sha256=_text_sha256(directory / "index-v1.json"),
    )
    target.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")


def verify_dataset(
    root: Path = DEFAULT_ROOT, *, include_held_out: bool = False
) -> dict[str, int]:
    manifest = load_manifest(root)
    cases = load_cases(root, include_held_out=include_held_out)
    for filename, expected in (
        ("corpus-v1.json", manifest.corpus_snapshot_sha256),
        ("index-v1.json", manifest.index_snapshot_sha256),
    ):
        if _text_sha256(root / "manifests" / filename) != expected:
            raise ValueError(f"Snapshot hash differs: {filename}")
    if (
        _text_sha256(DEFAULT_ROOT / "seed_questions.yaml")
        != manifest.legacy_seed_sha256
    ):
        raise ValueError("Legacy development seed fingerprint changed")
    corpus, index = _current_snapshots()
    for filename, current in (("corpus-v1.json", corpus), ("index-v1.json", index)):
        saved = type(current).model_validate_json(
            (root / "manifests" / filename).read_text(encoding="utf-8")
        )
        if saved != current:
            raise ValueError(
                f"Current corpus/index differs from frozen snapshot: {filename}"
            )
    validate_source_ids(cases, {c.id for c in corpus.chunks})
    return {
        "development": sum(c.split == "development" for c in manifest.cases),
        "held_out": sum(c.split == "held_out" for c in manifest.cases),
        "validated_cases": len(cases),
        "public_chunks": len(corpus.chunks),
        "draft_chunks": sum(c.draft for c in corpus.chunks),
    }
