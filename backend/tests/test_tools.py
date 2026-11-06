"""Unit tests for ToolRegistry and ProjectCardData provider."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.tools.projects import (
    PROJECT_CATALOG,
    ProjectCardData,
    get_project_card,
)
from app.tools.registry import (
    ShowProjectCardTool,
    ToolRegistry,
    get_tool_registry,
)


def test_project_catalog_contains_expected_projects() -> None:
    expected_ids = {
        "entropy-oj",
        "ai-digital-assistant",
        "health-premium-predictor",
        "health-tracker",
        "keynone",
        "vayusetu",
        "browser-games",
        "secure-auction",
    }
    assert expected_ids.issubset(set(PROJECT_CATALOG.keys()))


def test_project_card_schema_and_immutability() -> None:
    entropy = PROJECT_CATALOG["entropy-oj"]
    assert entropy.id == "entropy-oj"
    assert "Entropy Online Judge" in entropy.title
    assert len(entropy.tech_stack) > 5
    assert len(entropy.highlights) > 0
    assert "Redis" in entropy.tech_stack
    assert entropy.github_url is not None
    assert entropy.live_url == "https://entropy-oj.vercel.app"
    assert "System Architecture" in entropy.architecture_details

    # Verify model is frozen/immutable
    with pytest.raises(ValidationError):
        entropy.title = "Mutated Title"  # type: ignore[misc]


def test_get_project_card_exact_and_alias_lookup() -> None:
    assert get_project_card("entropy-oj") is not None
    assert get_project_card("entropy") == get_project_card("entropy-oj")
    assert get_project_card("ENTROPY_OJ") == get_project_card("entropy-oj")
    assert get_project_card("ai-assistant") == get_project_card("ai-digital-assistant")
    assert get_project_card("insurance") == get_project_card("health-premium-predictor")
    assert get_project_card("healthtracker") == get_project_card("health-tracker")
    assert get_project_card("key-none") == get_project_card("keynone")
    assert get_project_card("non-existent-project") is None


def test_tool_registry_schemas_format() -> None:
    registry = ToolRegistry()
    schemas = registry.get_schemas()
    assert len(schemas) >= 1

    first = schemas[0]
    assert first["type"] == "function"
    assert first["function"]["name"] == "show_project_card"
    assert "parameters" in first["function"]
    assert first["function"]["parameters"]["type"] == "object"
    assert "project_id" in first["function"]["parameters"]["properties"]


def test_tool_registry_execute_success() -> None:
    registry = ToolRegistry()

    # Dict arguments
    result_dict = registry.execute("show_project_card", {"project_id": "entropy-oj"})
    assert isinstance(result_dict, ProjectCardData)
    assert result_dict.id == "entropy-oj"

    # JSON string arguments (standard LLM output)
    result_str = registry.execute(
        "show_project_card", '{"project_id": "ai-digital-assistant"}'
    )
    assert isinstance(result_str, ProjectCardData)
    assert result_str.id == "ai-digital-assistant"


def test_tool_registry_execute_edge_cases() -> None:
    registry = ToolRegistry()

    # Unknown tool
    assert registry.execute("unknown_tool", {"foo": "bar"}) is None

    # Unknown project ID
    assert registry.execute("show_project_card", {"project_id": "unknown"}) is None

    # Malformed JSON string
    assert registry.execute("show_project_card", "{not-valid-json}") is None

    # Wrong argument type
    assert registry.execute("show_project_card", ["not", "a", "dict"]) is None


def test_get_tool_registry_singleton() -> None:
    from starlette.requests import Request

    from app.main import create_app

    app = create_app()
    request = Request({"type": "http", "app": app})
    r1 = get_tool_registry(request)
    r2 = get_tool_registry(request)
    assert r1 is r2
    assert isinstance(r1._tools["show_project_card"], ShowProjectCardTool)
