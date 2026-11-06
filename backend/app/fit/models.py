"""Pydantic models and schemas for the JD Fit Report pipeline."""

from __future__ import annotations

import hashlib
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RequirementImportance = Literal["must_have", "nice_to_have"]
RequirementType = Literal["skill", "experience", "education", "soft"]
RequirementVerdictType = Literal["strong", "partial", "gap"]


class FitRequest(BaseModel):
    """Inbound payload for JD Fit Report generation."""

    jd_text: str = Field(
        ...,
        min_length=50,
        max_length=6000,
        description="Raw job description text pasted by the recruiter (max 6k chars)",
    )
    role_title: str | None = Field(
        default=None,
        max_length=150,
        description="Optional title of the role (e.g. 'Senior AI Engineer')",
    )
    force_live: bool = Field(default=False, strict=True)

    @field_validator("jd_text", mode="after")
    @classmethod
    def strip_and_normalize(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 50:
            raise ValueError(
                "Job description is too short (minimum 50 characters required)."
            )
        return cleaned

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 hash of normalized text for caching."""
        normalized = re.sub(r"\s+", " ", self.jd_text).strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    model_config = ConfigDict(frozen=True)


class Requirement(BaseModel):
    """A single atomic requirement extracted from the job description."""

    id: str = Field(..., description="Unique requirement ID, e.g. 'req-1'")
    text: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="Concise statement of the requirement",
    )
    importance: RequirementImportance = Field(
        default="must_have",
        description="Core requirement (must_have) or preferred (nice_to_have)",
    )
    type: RequirementType = Field(
        default="skill",
        description="Requirement category: skill, experience, education, or soft",
    )

    model_config = ConfigDict(frozen=True)


class RequirementExtraction(BaseModel):
    """Structured extraction result returned by the utility extraction LLM."""

    role_title: str = Field(
        default="Target Role",
        max_length=150,
        description="Inferred or explicitly stated role title",
    )
    requirements: list[Requirement] = Field(
        ...,
        min_length=1,
        description="Up to 8 prioritized atomic requirements extracted from the JD",
    )

    @field_validator("requirements", mode="before")
    @classmethod
    def limit_requirements(
        cls, v: list[Requirement] | list[dict[str, object]]
    ) -> list[Requirement] | list[dict[str, object]]:
        if isinstance(v, list) and len(v) > 8:
            return v[:8]
        return v

    @field_validator("requirements")
    @classmethod
    def unique_requirement_ids(cls, items: list[Requirement]) -> list[Requirement]:
        if len({item.id for item in items}) != len(items):
            raise ValueError("Requirement IDs must be unique.")
        return items

    model_config = ConfigDict(frozen=True)


class JudgedRequirement(BaseModel):
    """A requirement evaluated against Aamir's verified knowledge facts."""

    requirement: Requirement
    verdict: RequirementVerdictType = Field(
        ...,
        description="Match: strong (verified), partial (adjacent), or gap",
    )
    evidence_chunk_ids: list[str] = Field(
        default_factory=list,
        description="List of verified fact chunk IDs supporting this verdict",
    )
    explanation: str = Field(
        ...,
        max_length=300,
        description="Truthful explanation under 30 words",
    )
    ramp_up: str | None = Field(
        default=None,
        max_length=300,
        description="Honest ramp-up narrative for partial and gap verdicts",
    )
    downgraded: bool = Field(
        default=False,
        description="True if server downgraded claim due to missing evidence",
    )

    model_config = ConfigDict(frozen=True)


class FitScoreSummary(BaseModel):
    """Deterministic score metrics computed in Python (no LLM hallucinations)."""

    must_have_total: int = Field(ge=0)
    must_have_strong: int = Field(ge=0)
    must_have_partial: int = Field(ge=0)
    must_have_gap: int = Field(ge=0)

    nice_to_have_total: int = Field(ge=0)
    nice_to_have_strong: int = Field(ge=0)
    nice_to_have_partial: int = Field(ge=0)
    nice_to_have_gap: int = Field(ge=0)

    total_requirements: int = Field(ge=0)
    overall_fit: Literal["Strong Match", "Partial Match", "Low Match"]
    headline: str = Field(description="Summary count headline")

    model_config = ConfigDict(frozen=True)


class FitReport(BaseModel):
    """Complete, verified Job Fit Report."""

    role_title: str
    jd_hash: str
    score: FitScoreSummary
    requirements: list[JudgedRequirement]
    summary: str = Field(
        description="3-sentence summary covering strengths, gaps, and next steps"
    )
    cached: bool = Field(
        default=False,
        description="True if served instantly from content-hash cache",
    )

    model_config = ConfigDict(frozen=True)
