"""Build a shareable snapshot from the published résumé."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SummaryProjectId = Literal[
    "entropy-oj", "ai-digital-assistant", "health-tracker", "health-premium-predictor"
]
SourceSection = Literal["Technical Skills", "Experience", "Technical Projects"]


class SummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_ids: list[SummaryProjectId] = Field(default_factory=list, max_length=4)


class SummaryEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    description: str
    source: SourceSection


class SummaryProject(SummaryEvidence):
    id: SummaryProjectId


class ForwardableSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    headline: str
    strengths: tuple[SummaryEvidence, SummaryEvidence, SummaryEvidence]
    projects: tuple[SummaryProject, ...] = Field(min_length=1, max_length=2)
    gaps: str
    availability: str
    contact_email: str


_STRENGTHS = (
    SummaryEvidence(
        title="Full-stack applications",
        description="Builds web applications with React and TypeScript, backed by "
        "FastAPI or Express APIs.",
        source="Technical Skills",
    ),
    SummaryEvidence(
        title="Grounded AI applications",
        description="Built a recruiter assistant with hybrid retrieval, streaming "
        "answers, and source citations.",
        source="Technical Projects",
    ),
    SummaryEvidence(
        title="Asynchronous workloads",
        description="Implemented queued C++ and Python judging with BullMQ, Redis, "
        "and Linux execution limits.",
        source="Experience",
    ),
)

_PROJECTS: dict[SummaryProjectId, SummaryProject] = {
    "entropy-oj": SummaryProject(
        id="entropy-oj",
        title="Entropy-OJ",
        description="Coding workspace with asynchronous judging, submission history, "
        "and progressive debugging hints.",
        source="Experience",
    ),
    "ai-digital-assistant": SummaryProject(
        id="ai-digital-assistant",
        title="AI Digital Assistant Portfolio",
        description="Recruiter assistant built with FastAPI and React, with cited "
        "responses, human handoff, and structured job-fit reports.",
        source="Technical Projects",
    ),
    "health-tracker": SummaryProject(
        id="health-tracker",
        title="HealthTracker",
        description="Progressive web app for nutrition, workouts, and health metrics "
        "with dashboards and cache-first data access.",
        source="Technical Projects",
    ),
    "health-premium-predictor": SummaryProject(
        id="health-premium-predictor",
        title="Health Premium Predictor",
        description="Streamlit application using XGBoost regression to estimate "
        "insurance premiums.",
        source="Technical Projects",
    ),
}
_DEFAULT_PROJECTS: tuple[SummaryProjectId, ...] = ("entropy-oj", "ai-digital-assistant")


def build_summary(payload: SummaryRequest) -> ForwardableSummary:
    selected = list(dict.fromkeys([*payload.project_ids, *_DEFAULT_PROJECTS]))[:2]
    return ForwardableSummary(
        name="Aamir Mohammed Khan",
        headline="Full-stack and AI application development",
        strengths=_STRENGTHS,
        projects=tuple(_PROJECTS[project_id] for project_id in selected),
        gaps="The résumé documents project and externship work. Confirm role-specific "
        "requirements such as certifications and production scale directly with Aamir.",
        availability="Confirm start date and work arrangements with Aamir.",
        contact_email="aamirmkh25@gmail.com",
    )
