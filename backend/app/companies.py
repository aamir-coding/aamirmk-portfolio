"""Load recruiter contexts from authored configuration."""

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter

from app.tools.projects import PROJECT_CATALOG

_COMPANIES_PATH = Path(__file__).parent / "data" / "companies.yaml"
_Slug = Annotated[
    str,
    StringConstraints(
        max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*-[a-f0-9]{4,}$"
    ),
]
_ShortText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=180)
]


class _CompanyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    greeting: _ShortText
    highlighted_projects: tuple[str, ...] = Field(min_length=1, max_length=4)
    suggested_questions: tuple[_ShortText, _ShortText, _ShortText]
    why_us: str = Field(min_length=1, max_length=400)


class HighlightedProject(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str


class CompanyContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    slug: _Slug
    greeting: _ShortText
    highlighted_projects: tuple[HighlightedProject, ...]
    suggested_questions: tuple[_ShortText, _ShortText, _ShortText]
    why_us: str


def load_company_contexts(path: Path = _COMPANIES_PATH) -> dict[str, CompanyContext]:
    entries = TypeAdapter(dict[_Slug, _CompanyEntry]).validate_python(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
    contexts = {}
    for slug, entry in entries.items():
        if len(set(entry.highlighted_projects)) != len(entry.highlighted_projects):
            raise ValueError(f"Duplicate project in company context {slug}")
        if len(set(entry.suggested_questions)) != len(entry.suggested_questions):
            raise ValueError(f"Duplicate suggested question in company context {slug}")
        if any(
            project_id not in PROJECT_CATALOG
            for project_id in entry.highlighted_projects
        ):
            raise ValueError(f"Unknown project in company context {slug}")
        contexts[slug] = CompanyContext(
            slug=slug,
            greeting=entry.greeting,
            highlighted_projects=tuple(
                HighlightedProject(
                    id=project_id, title=PROJECT_CATALOG[project_id].title
                )
                for project_id in entry.highlighted_projects
            ),
            suggested_questions=entry.suggested_questions,
            why_us=entry.why_us,
        )
    return contexts
