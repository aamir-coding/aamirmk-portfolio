"""Result-backed public counts fail closed on stale, mixed or partial evidence."""

import json
import sys
from pathlib import Path

import pytest

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.eval_summary import (  # noqa: E402
    DEFAULT_ARTIFACT,
    PublicArtifact,
    load_summary,
)
from app.retrieval.artifacts import canonical_sha256  # noqa: E402
from evals.dataset import DEFAULT_ROOT, load_manifest  # noqa: E402
from evals.publish import project  # noqa: E402
from evals.results import OfflineResult  # noqa: E402


def test_public_projection_and_endpoint_match_actual_result(client) -> None:
    result = OfflineResult.model_validate_json(
        (DEFAULT_ROOT / "results.json").read_text(encoding="utf-8")
    )
    artifact = PublicArtifact.model_validate_json(
        DEFAULT_ARTIFACT.read_text(encoding="utf-8")
    )
    assert artifact == project(result)
    response = client.get("/api/eval-summary")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["badge"] == artifact.report.badge
    assert body["report"] == artifact.report.model_dump(mode="json")
    assert body["report"]["judge_validation"]["status"] == "failed"
    assert body["report"]["generation_accuracy_available"] is False
    assert response.headers["cache-control"] == "no-store"


def test_projection_redacts_held_out_and_raw_data() -> None:
    artifact = PublicArtifact.model_validate_json(
        DEFAULT_ARTIFACT.read_text(encoding="utf-8")
    )
    raw = artifact.model_dump_json()
    for case in load_manifest().cases:
        if case.split == "held_out":
            assert case.id not in raw
    for field in ("conversation", "rationale", "answer", "jd_text", "evidence_text"):
        assert f'"{field}"' not in raw
    assert len(artifact.report.judge_validation.disagreements) == 5


def test_projection_rejects_changed_index(monkeypatch: pytest.MonkeyPatch) -> None:
    import evals.publish

    current = evals.publish.input_fingerprints()
    monkeypatch.setattr(
        evals.publish, "input_fingerprints", lambda: {**current, "index": "a" * 64}
    )
    result = OfflineResult.model_validate_json(
        (DEFAULT_ROOT / "results.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ValueError, match="Stale result inputs"):
        project(result)


@pytest.mark.parametrize("payload", ["{", "{}", '{"schema_version":1,"kind":"live"}'])
def test_missing_or_invalid_artifact_unavailable(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "result.json"
    assert load_summary(path).status == "unavailable"
    path.write_text(payload, encoding="utf-8")
    assert load_summary(path).report is None


def test_changed_runtime_never_serves_old_numbers(tmp_path: Path) -> None:
    data = json.loads(DEFAULT_ARTIFACT.read_text(encoding="utf-8"))
    data["report"]["runtime_sha256"] = "a" * 64
    data["report_sha256"] = canonical_sha256(data["report"])
    path = tmp_path / "stale.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    summary = load_summary(path)
    assert summary.status == "stale"
    assert summary.report is None
    assert "8/8" not in summary.badge


def test_changed_counts_and_mixed_mode_fail_closed(tmp_path: Path) -> None:
    for key, value in (
        ("replay", {"passed": 7, "total": 8}),
        ("kind", "live_accuracy"),
    ):
        data = json.loads(DEFAULT_ARTIFACT.read_text(encoding="utf-8"))
        data["report"][key] = value
        data["report_sha256"] = canonical_sha256(data["report"])
        path = tmp_path / "invalid.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        assert load_summary(path).status == "unavailable"
