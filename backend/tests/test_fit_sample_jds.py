"""Unit tests for sample job descriptions loader and schemas."""

from app.fit.models import FitRequest
from app.fit.sample_jds import load_sample_jds


def test_load_sample_jds_loads_all_curated_roles() -> None:
    sample_jds = load_sample_jds()
    assert len(sample_jds) == 4

    ids = [jd.id for jd in sample_jds]
    assert "01-fullstack-ai-engineer" in ids
    assert "02-backend-python-engineer" in ids
    assert "03-genai-application-developer" in ids
    assert "04-embedded-firmware-engineer" in ids

    for jd in sample_jds:
        assert len(jd.title) > 0
        assert len(jd.company) > 0
        assert jd.match_expectation in ("Strong Match", "Partial Match", "Low Match")
        # Every sample JD must be a valid FitRequest payload
        req = FitRequest(jd_text=jd.text, role_title=jd.title)
        assert len(req.jd_text) >= 50
        assert len(req.compute_hash()) == 64
