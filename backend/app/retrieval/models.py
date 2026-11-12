"""Data models for knowledge base facts and retrieved chunks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FactChunk(BaseModel):
    """A granular, single-topic chunk of verified factual information."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        description="Unique identifier for the chunk, e.g. 'proj-entropy-oj-pitch'"
    )
    type: str = Field(
        description=(
            "Category type: profile, education, experience, project, skill, "
            "hr, opinion, achievement, personal, boundary"
        )
    )
    title: str = Field(description="Human-readable title describing the fact chunk")
    content: str = Field(description="The verified factual markdown or text content")
    source_section: str = Field(
        default="",
        description="Questionnaire or resume reference, e.g. 'J1, J2 (Project A)'",
    )
    source_url: str | None = Field(
        default=None,
        description="Optional public receipt or repository link",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Categorical and keyword lookup tags",
    )
    draft: bool = Field(
        default=True,
        description="Whether this fact chunk is marked as draft",
    )
    private: bool = Field(
        default=False,
        description="Whether this chunk contains private information",
    )
    indexed: bool = Field(
        default=True,
        description="Whether this chunk should be indexed for public search",
    )


class RetrievedChunk(BaseModel):
    """A fact chunk retrieved by an index or fusion algorithm with ranking metadata."""

    model_config = ConfigDict(frozen=True)

    chunk: FactChunk = Field(description="The underlying fact chunk")
    score: float = Field(description="Relevance or fusion score")
    rank: int = Field(ge=1, description="1-based rank in the result list")
    retrieval_method: str = Field(
        default="hybrid_rrf",
        description="Method used: bm25, dense, or hybrid_rrf",
    )
    dense_similarity: float | None = Field(default=None, ge=-1, le=1)
