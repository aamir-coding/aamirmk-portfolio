"""Tool registry and dispatcher for LLM tool-calling loops.

Provides a clean protocol seam: callers inspect schemas and execute tools
without coupling to internal tool implementations.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol, runtime_checkable

from app.tools.projects import (
    PROJECT_CATALOG,
    ProjectCardData,
    get_project_card,
)

logger = logging.getLogger(__name__)


@runtime_checkable
class Tool(Protocol):
    """Protocol for an executable tool in the assistant registry."""

    name: str
    description: str

    def get_schema(self) -> dict[str, Any]: ...

    def execute(self, arguments: dict[str, Any]) -> Any: ...


class ShowProjectCardTool:
    """Tool that resolves an authoritative ProjectCardData record from disk."""

    name: str = "show_project_card"
    description: str = (
        "Summon an interactive technical dossier card for one of Aamir's featured "
        "projects when the user asks about his projects, system architecture, "
        "or technical implementations."
    )

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "enum": list(PROJECT_CATALOG.keys()),
                            "description": "Unique identifier of the project",
                        }
                    },
                    "required": ["project_id"],
                },
            },
        }

    def execute(self, arguments: dict[str, Any]) -> ProjectCardData | None:
        project_id = arguments.get("project_id", "")
        if not isinstance(project_id, str):
            return None
        return get_project_card(project_id)


class ToolRegistry:
    """Central registry and executor for assistant tools."""

    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        if tools is not None:
            for tool in tools:
                self.register(tool)
        else:
            self.register(ShowProjectCardTool())

    def register(self, tool: Tool) -> None:
        """Register a new tool instance."""
        self._tools[tool.name] = tool

    def get_schemas(self) -> list[dict[str, Any]]:
        """Return all registered tool schemas formatted for Groq/OpenAI."""
        return [tool.get_schema() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any] | str) -> Any:
        """Safely execute a tool by name, handling string or dict arguments."""
        tool = self._tools.get(name)
        if not tool:
            logger.warning("Tool not found in registry: %s", name)
            return None

        # Parse string arguments if model passed serialized JSON string
        if isinstance(arguments, str):
            try:
                parsed_args = json.loads(arguments)
            except Exception as exc:
                logger.warning("Malformed JSON tool arguments for %s: %s", name, exc)
                return None
        elif isinstance(arguments, dict):
            parsed_args = arguments
        else:
            return None

        try:
            return tool.execute(parsed_args)
        except Exception as exc:
            logger.error("Error executing tool %s: %s", name, exc)
            return None


_default_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """FastAPI dependency returning the singleton tool registry."""
    return _default_registry
