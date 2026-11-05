"""Artifact compatibility and critical regressions cannot hide in averages."""

import pytest
from pydantic import ValidationError

from evals.dataset import DEFAULT_ROOT
from evals.results import Baseline, OfflineResult, gate


@pytest.fixture
def result() -> OfflineResult:
    return OfflineResult.model_validate_json(
        (DEFAULT_ROOT / "results.json").read_text(encoding="utf-8")
    )


def baseline(result: OfflineResult) -> Baseline:
    return Baseline(
        review_reference="test",
        fingerprints=result.fingerprints,
        scores=result.scores(),
    )


def test_saved_result_and_compatible_baseline(result: OfflineResult) -> None:
    assert gate(result, baseline(result)) == []
    assert result.provider_calls == 0
    assert result.generation_accuracy_available is False
    assert result.split_ids["held_out"]


def test_changed_inputs_require_review(result: OfflineResult) -> None:
    changed = baseline(result).model_copy(
        update={"fingerprints": {"checker": "a" * 64}}
    )
    assert any("incompatible_baseline" in f for f in gate(result, changed))


def test_more_than_two_points_blocks(result: OfflineResult) -> None:
    base = baseline(result)
    scores = {**base.scores, "legacy_development.hit_at_3": 0.94}
    assert "regression:legacy_development.hit_at_3" in gate(
        result, base.model_copy(update={"scores": scores})
    )


def test_one_critical_failure_blocks_even_small_regression(
    result: OfflineResult,
) -> None:
    row = result.replay.results[0].model_copy(update={"passed": False})
    replay = result.replay.model_copy(
        update={
            "results": [row, *result.replay.results[1:]],
            "checks_passed": result.replay.checks_passed - 1,
        }
    )
    changed = result.model_copy(update={"replay": replay})
    assert f"critical:{row.id}" in gate(changed, baseline(result))


def test_tampered_counts_rejected(result: OfflineResult) -> None:
    data = result.model_dump(mode="json")
    data["replay"]["checks_passed"] -= 1
    with pytest.raises(ValidationError, match="counts"):
        OfflineResult.model_validate(data)
