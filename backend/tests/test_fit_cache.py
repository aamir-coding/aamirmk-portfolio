"""Bounded fit caching preserves complete input/provenance identity and live bypass."""

import pytest

from app.fit.cache import ReportCache
from app.fit.models import FitRequest
from app.fit.sample_jds import load_sample_jds


def sample_report():
    report = load_sample_jds()[0].report
    assert report is not None
    return report


def test_cache_separates_role_title_case_and_runtime_identity() -> None:
    request = FitRequest(jd_text="Python API engineering " * 4, role_title="First")
    cache = ReportCache(identity="one", include_curated=False)
    cache.put(request, sample_report())
    assert cache.get(request) is not None
    assert cache.get(request.model_copy(update={"role_title": "Second"})) is None
    assert (
        cache.get(request.model_copy(update={"jd_text": request.jd_text.lower()}))
        is None
    )
    assert ReportCache(identity="two", include_curated=False).key(request) != cache.key(
        request
    )


def test_generated_cache_bounds_preserve_authored_presets() -> None:
    now = [0.0]
    cache = ReportCache(
        identity="test", max_entries=1, ttl_seconds=10, clock=lambda: now[0]
    )
    one = FitRequest(jd_text="A" * 60)
    two = FitRequest(jd_text="B" * 60)
    cache.put(one, sample_report())
    cache.put(two, sample_report())
    assert cache.get(one) is None
    assert cache.get(two) is not None
    now[0] = 10
    assert cache.get(two) is None
    preset = load_sample_jds()[0]
    assert cache.get(FitRequest(jd_text=preset.text))[1] == "curated"


def test_force_live_bypasses_generated_and_curated_entries() -> None:
    cache = ReportCache(identity="test")
    sample = load_sample_jds()[0]
    request = FitRequest(jd_text=sample.text)
    assert cache.get(request) is not None
    assert cache.get(request.model_copy(update={"force_live": True})) is None


@pytest.mark.parametrize("option", [{"max_entries": 0}, {"ttl_seconds": -1}])
def test_invalid_cache_bounds_rejected(option) -> None:
    with pytest.raises(ValueError):
        ReportCache(identity="test", **option)


def test_edited_sample_cannot_reuse_an_old_curated_report(monkeypatch) -> None:
    from dataclasses import replace

    import app.fit.cache as cache_module

    sample = load_sample_jds()[0]
    edited = replace(sample, text=sample.text + "\nMandatory: embedded firmware.")
    monkeypatch.setattr(cache_module, "load_sample_jds", lambda: [edited])
    cache = ReportCache(identity="test")
    assert cache.get(FitRequest(jd_text=edited.text)) is None


def test_changed_facts_disable_authored_reports_in_cache_and_preset_projection(
    monkeypatch,
) -> None:
    import app.fit.cache as cache_module

    hashes = cache_module.curated_source_hashes()
    monkeypatch.setattr(
        cache_module,
        "curated_source_hashes",
        lambda: {
            **hashes,
            "facts_sha256": "0" * 64,
        },
    )
    sample = load_sample_jds()[0]
    cache = ReportCache(identity="changed")
    assert cache.get(FitRequest(jd_text=sample.text)) is None
    assert all(preset.report is None for preset in cache.presets())
