"""Case validation and split integrity; no generation or answer scoring."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from evals.dataset import load_cases, verify_dataset
from evals.schemas import CaseSuite, EvalCase


@pytest.fixture
def case_data() -> dict[str, Any]:
    return {
        "id": "example",
        "version": 1,
        "group_id": "example-topic",
        "split": "development",
        "category": "factual",
        "target": "chat",
        "origin": {"kind": "authored", "reference": "synthetic regression"},
        "conversation": [{"role": "user", "content": "What is supported?"}],
        "checks": {
            "sources": {"mode": "all_relevant", "ids": ["source-one"]},
            "support_expectations": ["Only say what the evidence supports."],
        },
    }


@pytest.mark.parametrize(
    "mutation",
    [
        {"id": " "},
        {"version": 0},
        {"category": "invented"},
        {"split": "training"},
        {"unexpected": True},
        {"conversation": []},
        {"conversation": [{"role": "assistant", "content": "Answer"}]},
        {"conversation": [{"role": "user", "content": "  "}]},
        {"label_status": "human_calibrated"},
    ],
)
def test_invalid_case_is_rejected(
    case_data: dict[str, Any],
    mutation: dict[str, Any],
) -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate({**case_data, **mutation})


@pytest.mark.parametrize(
    "sources",
    [
        {"mode": "none", "ids": ["source-one"]},
        {"mode": "any_of", "ids": []},
        {"mode": "all_relevant", "ids": ["source-one", "source-one"]},
    ],
)
def test_ambiguous_source_labels_are_rejected(
    case_data: dict[str, Any],
    sources: dict[str, Any],
) -> None:
    case_data["checks"]["sources"] = sources
    with pytest.raises(ValidationError):
        EvalCase.model_validate(case_data)


@pytest.mark.parametrize("overlap", ["id", "group", "conversation"])
def test_splits_cannot_leak_examples(case_data: dict[str, Any], overlap: str) -> None:
    other = deepcopy(case_data)
    other.update(id="other", group_id="other-topic", split="held_out")
    other["conversation"][0]["content"] = "A different question?"
    if overlap == "id":
        other["id"] = case_data["id"]
    elif overlap == "group":
        other["group_id"] = case_data["group_id"]
    else:
        other["conversation"] = case_data["conversation"]
    with pytest.raises(ValidationError, match="Duplicate|overlap"):
        CaseSuite.model_validate({"version": "phase8-v1", "cases": [case_data, other]})


def test_seed_cannot_be_rebranded_as_held_out(case_data: dict[str, Any]) -> None:
    case_data.update(
        split="held_out", origin={"kind": "legacy_seed", "reference": "eval-01"}
    )
    with pytest.raises(ValidationError, match="seed"):
        EvalCase.model_validate(case_data)


def test_human_review_requires_provenance(case_data: dict[str, Any]) -> None:
    case_data["label_status"] = "human_reviewed"
    with pytest.raises(ValidationError, match="review"):
        EvalCase.model_validate(case_data)


def test_default_loading_does_not_expose_held_out_cases() -> None:
    cases = load_cases()
    assert len(cases) >= 40
    assert {case.split for case in cases} == {"development"}
    assert {case.label_status for case in cases} == {"provisional"}


def test_frozen_dataset_integrity_without_scoring() -> None:
    summary = verify_dataset(include_held_out=True)
    assert summary["development"] == 40
    assert summary["held_out"] == 10
    assert summary["public_chunks"] == summary["draft_chunks"] == 76


def test_case_changes_require_a_new_frozen_manifest(tmp_path: Path) -> None:
    import shutil

    root = Path(__file__).resolve().parent
    shutil.copytree(root / "cases", tmp_path / "cases")
    shutil.copytree(root / "manifests", tmp_path / "manifests")
    development = tmp_path / "cases" / "development.yaml"
    development.write_text(
        development.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="hash|fingerprint"):
        load_cases(tmp_path)


def test_unknown_fact_label_is_rejected(case_data: dict[str, Any]) -> None:
    from evals.dataset import validate_source_ids

    case = EvalCase.model_validate(case_data)
    with pytest.raises(ValueError, match="source-one"):
        validate_source_ids([case], {"some-other-source"})


def test_freeze_rejects_wrong_file_split_before_writing_snapshots(
    tmp_path: Path,
) -> None:
    import shutil

    import yaml

    from evals.dataset import freeze_dataset

    root = Path(__file__).resolve().parent
    shutil.copytree(root / "cases", tmp_path / "cases")
    held_out = tmp_path / "cases" / "held_out.yaml"
    payload = yaml.safe_load(held_out.read_text(encoding="utf-8"))
    for case in payload["cases"]:
        case["split"] = "development"
    held_out.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="split"):
        freeze_dataset(tmp_path)
    assert not list((tmp_path / "manifests").glob("*.json"))


def test_freeze_rejects_rebranded_legacy_question(tmp_path: Path) -> None:
    import shutil

    import yaml

    from evals.dataset import freeze_dataset

    root = Path(__file__).resolve().parent
    shutil.copytree(root / "cases", tmp_path / "cases")
    held_out = tmp_path / "cases" / "held_out.yaml"
    payload = yaml.safe_load(held_out.read_text(encoding="utf-8"))
    legacy = yaml.safe_load((root / "seed_questions.yaml").read_text(encoding="utf-8"))
    # A known legacy question not copied into the new development YAML.
    payload["cases"][0]["conversation"][0]["content"] = legacy["questions"][43][
        "question"
    ]
    held_out.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="legacy|seed"):
        freeze_dataset(tmp_path)
    assert not list((tmp_path / "manifests").glob("*.json"))


def test_development_loader_never_parses_reserved_file(tmp_path: Path) -> None:
    import shutil

    root = Path(__file__).resolve().parent
    shutil.copytree(root / "cases", tmp_path / "cases")
    shutil.copytree(root / "manifests", tmp_path / "manifests")
    (tmp_path / "cases" / "held_out.yaml").write_text(
        "not even valid YAML: [", encoding="utf-8"
    )
    assert len(load_cases(tmp_path)) == 40


def test_dataset_covers_required_behavior_categories() -> None:
    assert {case.category for case in load_cases()} == {
        "factual",
        "hr",
        "technical",
        "off_topic",
        "refusal",
        "adversarial",
        "false_premise",
        "follow_up",
        "fit",
        "protocol",
    }


def test_git_line_ending_conversion_preserves_manifest_validity(tmp_path: Path) -> None:
    import shutil

    root = Path(__file__).resolve().parent
    shutil.copytree(root / "cases", tmp_path / "cases")
    shutil.copytree(root / "manifests", tmp_path / "manifests")
    for directory in (tmp_path / "cases", tmp_path / "manifests"):
        for path in directory.iterdir():
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    assert verify_dataset(tmp_path)["validated_cases"] == 40


def test_freeze_refuses_to_replace_existing_split(tmp_path: Path) -> None:
    import shutil

    from evals.dataset import freeze_dataset

    root = Path(__file__).resolve().parent
    shutil.copytree(root / "cases", tmp_path / "cases")
    shutil.copytree(root / "manifests", tmp_path / "manifests")
    path = tmp_path / "manifests" / "dataset-v1.json"
    original = path.read_bytes()
    with pytest.raises(FileExistsError, match="already frozen"):
        freeze_dataset(tmp_path)
    assert path.read_bytes() == original
