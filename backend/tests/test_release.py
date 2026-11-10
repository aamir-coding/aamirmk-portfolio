"""Release identity must describe validated assets, never a guessed deployment."""

import json
from pathlib import Path

import pytest

from app.release import ReleaseInfo, load_release, verify_release


def test_missing_or_corrupt_release_is_unknown(tmp_path: Path) -> None:
    path = tmp_path / "release.json"
    assert load_release(path).revision is None
    path.write_text('{"revision":"<script>"}')
    assert load_release(path).revision is None


def test_release_checks_cached_assets_without_rebuilding(tmp_path: Path) -> None:
    path = tmp_path / "release.json"
    info = verify_release("a" * 40, path)
    assert info.revision == "a" * 40
    assert len(info.index_sha256 or "") == 64
    assert load_release(path) == info
    assert json.loads(path.read_text())["revision"] == "a" * 40


def test_invalid_revision_cannot_write_release(tmp_path: Path) -> None:
    path = tmp_path / "release.json"
    with pytest.raises(ValueError):
        verify_release("main", path)
    assert not path.exists()


def test_release_schema_rejects_extra_fields() -> None:
    with pytest.raises(ValueError):
        ReleaseInfo.model_validate({"revision": "a" * 40, "secret": "no"})
