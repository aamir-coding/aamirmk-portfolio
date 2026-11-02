"""Unit tests for JD Fit Report domain models and deterministic scoring engine."""

import pytest
from pydantic import ValidationError

from app.fit.models import (
    FitRequest,
    JudgedRequirement,
    Requirement,
    RequirementExtraction,
)
from app.fit.scorer import compute_fit_summary, validate_and_downgrade_verdicts


class TestFitModels:
    """Test validation invariants on Fit domain models."""

    def test_fit_request_valid_and_hash(self) -> None:
        raw_jd = (
            "  Looking for a Senior Python and FastAPI Engineer with experience "
            "in RAG systems and Docker containerization.  "
        )
        req = FitRequest(jd_text=raw_jd)
        assert len(req.jd_text) >= 50
        jd_hash = req.compute_hash()
        assert len(jd_hash) == 64
        # Hash is deterministic and whitespace-insensitive
        req2 = FitRequest(
            jd_text=(
                "Looking for a Senior Python and FastAPI Engineer with experience "
                "in RAG systems and Docker containerization."
            )
        )
        assert req.compute_hash() == req2.compute_hash()

    def test_fit_request_rejects_too_short(self) -> None:
        with pytest.raises(ValidationError):
            FitRequest(jd_text="Too short JD text")

    def test_requirement_extraction_caps_at_eight(self) -> None:
        items = [
            Requirement(
                id=f"req-{i}",
                text=f"Requirement number {i}",
                importance="must_have",
                type="skill",
            )
            for i in range(12)
        ]
        extraction = RequirementExtraction(
            role_title="Lead AI Engineer", requirements=items
        )
        assert len(extraction.requirements) == 8
        assert extraction.requirements[0].id == "req-0"
        assert extraction.requirements[7].id == "req-7"

    def test_requirement_extraction_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            RequirementExtraction(role_title="Dev", requirements=[])


class TestAntiOverclaimingEngine:
    """Verify the iron law: no verified evidence = automatic downgrade to gap."""

    def test_strong_verdict_retained_when_evidence_valid(self) -> None:
        req = Requirement(
            id="req-1",
            text="FastAPI development",
            importance="must_have",
            type="skill",
        )
        judged = [
            JudgedRequirement(
                requirement=req,
                verdict="strong",
                evidence_chunk_ids=["chunk-fastapi-1", "chunk-fastapi-2"],
                explanation="Built async REST API in FastAPI with SSE streaming.",
                ramp_up=None,
            )
        ]
        valid_chunks = {"chunk-fastapi-1", "chunk-fastapi-2", "chunk-python"}
        sanitized = validate_and_downgrade_verdicts(judged, valid_chunks)

        assert len(sanitized) == 1
        assert sanitized[0].verdict == "strong"
        assert sanitized[0].downgraded is False
        assert sanitized[0].evidence_chunk_ids == [
            "chunk-fastapi-1",
            "chunk-fastapi-2",
        ]

    def test_strong_verdict_downgraded_when_no_evidence_cited(self) -> None:
        req = Requirement(
            id="req-2",
            text="10 years of Kubernetes administration",
            importance="must_have",
            type="skill",
        )
        judged = [
            JudgedRequirement(
                requirement=req,
                verdict="strong",
                evidence_chunk_ids=[],  # Hallucinated strong verdict without receipts!
                explanation="Candidate has strong architecture knowledge.",
                ramp_up=None,
            )
        ]
        sanitized = validate_and_downgrade_verdicts(
            judged, valid_chunk_ids={"chunk-fastapi-1"}
        )

        assert len(sanitized) == 1
        assert sanitized[0].verdict == "gap"
        assert sanitized[0].downgraded is True
        assert "[Downgraded to gap" in sanitized[0].explanation
        assert sanitized[0].ramp_up is not None

    def test_partial_verdict_downgraded_when_cited_chunks_do_not_exist(self) -> None:
        req = Requirement(
            id="req-3",
            text="Rust firmware development",
            importance="must_have",
            type="skill",
        )
        judged = [
            JudgedRequirement(
                requirement=req,
                verdict="partial",
                evidence_chunk_ids=["chunk-invented-by-llm"],  # Hallucinated ID!
                explanation="Has basic systems programming awareness.",
                ramp_up="Take Rust course",
            )
        ]
        sanitized = validate_and_downgrade_verdicts(
            judged, valid_chunk_ids={"chunk-fastapi-1", "chunk-python"}
        )

        assert len(sanitized) == 1
        assert sanitized[0].verdict == "gap"
        assert sanitized[0].downgraded is True
        assert sanitized[0].evidence_chunk_ids == []

    def test_partial_verdict_keeps_only_valid_subset_of_chunks(self) -> None:
        req = Requirement(
            id="req-4",
            text="PostgreSQL and SQL optimization",
            importance="must_have",
            type="skill",
        )
        judged = [
            JudgedRequirement(
                requirement=req,
                verdict="partial",
                evidence_chunk_ids=["chunk-postgres-real", "chunk-fake-bogus"],
                explanation="Used PostgreSQL in Auction System.",
                ramp_up=None,
            )
        ]
        sanitized = validate_and_downgrade_verdicts(
            judged, valid_chunk_ids={"chunk-postgres-real"}
        )

        assert len(sanitized) == 1
        assert sanitized[0].verdict == "partial"
        assert sanitized[0].downgraded is False
        assert sanitized[0].evidence_chunk_ids == ["chunk-postgres-real"]


class TestDeterministicScoring:
    """Verify deterministic metric tallying and overall fit determination."""

    def test_strong_match_overall(self) -> None:
        req1 = Requirement(id="r1", text="Python", importance="must_have", type="skill")
        req2 = Requirement(
            id="r2", text="FastAPI", importance="must_have", type="skill"
        )
        req3 = Requirement(
            id="r3", text="Redis", importance="nice_to_have", type="skill"
        )

        judged = [
            JudgedRequirement(
                requirement=req1, verdict="strong", explanation="Python proficient"
            ),
            JudgedRequirement(
                requirement=req2, verdict="strong", explanation="FastAPI built"
            ),
            JudgedRequirement(
                requirement=req3, verdict="strong", explanation="Redis queuing"
            ),
        ]

        summary = compute_fit_summary(judged)
        assert summary.must_have_total == 2
        assert summary.must_have_strong == 2
        assert summary.must_have_gap == 0
        assert summary.overall_fit == "Strong Match"
        assert "Covers 2 of 2 must-haves" in summary.headline

    def test_partial_match_overall(self) -> None:
        req1 = Requirement(id="r1", text="Python", importance="must_have", type="skill")
        req2 = Requirement(
            id="r2", text="TypeScript", importance="must_have", type="skill"
        )
        req3 = Requirement(
            id="r3", text="Kubernetes", importance="must_have", type="skill"
        )

        judged = [
            JudgedRequirement(
                requirement=req1, verdict="strong", explanation="Python"
            ),
            JudgedRequirement(
                requirement=req2, verdict="partial", explanation="TS working"
            ),
            JudgedRequirement(requirement=req3, verdict="gap", explanation="No K8s"),
        ]

        summary = compute_fit_summary(judged)
        assert summary.must_have_total == 3
        assert summary.must_have_strong == 1
        assert summary.must_have_partial == 1
        assert summary.must_have_gap == 1
        assert summary.overall_fit == "Partial Match"
        assert "Covers 1 of 3 must-haves (1 partial, 1 gap)" in summary.headline

    def test_low_match_overall(self) -> None:
        req1 = Requirement(
            id="r1", text="C++ Embedded", importance="must_have", type="skill"
        )
        req2 = Requirement(id="r2", text="RTOS", importance="must_have", type="skill")
        req3 = Requirement(
            id="r3", text="PCB Design", importance="must_have", type="skill"
        )

        judged = [
            JudgedRequirement(
                requirement=req1, verdict="gap", explanation="No embedded C++"
            ),
            JudgedRequirement(requirement=req2, verdict="gap", explanation="No RTOS"),
            JudgedRequirement(requirement=req3, verdict="gap", explanation="No PCB"),
        ]

        summary = compute_fit_summary(judged)
        assert summary.must_have_total == 3
        assert summary.must_have_strong == 0
        assert summary.must_have_gap == 3
        assert summary.overall_fit == "Low Match"
