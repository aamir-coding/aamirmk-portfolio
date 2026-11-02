"""Knowledge base loader — parses YAML and Markdown facts into FactChunk models."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from app.retrieval.models import FactChunk

# Default facts directory relative to repository root / backend root
_DEFAULT_FACTS_DIR = Path(__file__).parent.parent / "data" / "facts"


def parse_markdown_chunks(content: str, file_path: Path) -> list[FactChunk]:
    """Parse one or more frontmatter-delimited chunks from a markdown document.

    Supports both single-chunk markdown files and multi-chunk files delimited by
    standard YAML frontmatter delimiters (`---`).
    """
    chunks: list[FactChunk] = []
    # Split text into segments delimited by lines containing only '---'
    segments = re.split(r"(?m)^---\s*$", content)

    # Filter out empty or whitespace-only initial segments before the first '---'
    i = 0
    while i < len(segments):
        seg = segments[i].strip()
        if not seg:
            i += 1
            continue

        # If this segment looks like YAML frontmatter (e.g. contains 'id:' or 'type:')
        if ("id:" in seg or "type:" in seg) and i + 1 < len(segments):
            try:
                meta = yaml.safe_load(seg)
            except Exception as e:
                raise ValueError(f"Invalid YAML frontmatter in {file_path}: {e}") from e

            body = segments[i + 1].strip()
            if isinstance(meta, dict) and "id" in meta:
                meta_dict: dict[str, Any] = dict(meta)
                meta_dict["content"] = body
                chunks.append(FactChunk.model_validate(meta_dict))
                i += 2
                continue

        i += 1

    return chunks


def parse_yaml_chunks(content: str, file_path: Path) -> list[FactChunk]:
    """Parse FactChunk instances from a YAML file."""
    try:
        data = yaml.safe_load(content)
    except Exception as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}") from e

    if not data:
        return []

    chunks: list[FactChunk] = []
    if isinstance(data, dict):
        if "chunks" in data and isinstance(data["chunks"], list):
            for item in data["chunks"]:
                if isinstance(item, dict):
                    chunks.append(FactChunk.model_validate(item))
        elif "id" in data:
            chunks.append(FactChunk.model_validate(data))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "id" in item:
                chunks.append(FactChunk.model_validate(item))

    return chunks


class FactLoader:
    """Discovers, parses, and validates all knowledge base fact chunks."""

    def __init__(self, facts_dir: Path | str | None = None) -> None:
        if facts_dir is None:
            self.facts_dir = _DEFAULT_FACTS_DIR
        else:
            self.facts_dir = Path(facts_dir)

    def load_all(
        self,
        *,
        include_private: bool = False,
        include_unindexed: bool = False,
    ) -> list[FactChunk]:
        """Loads all fact chunks from facts directory with filtering rules."""
        if not self.facts_dir.exists():
            raise FileNotFoundError(f"Facts directory not found: {self.facts_dir}")

        all_chunks: list[FactChunk] = []
        seen_ids: set[str] = set()

        for file_path in sorted(self.facts_dir.rglob("*")):
            if not file_path.is_file():
                continue

            chunks: list[FactChunk] = []
            if file_path.suffix in (".yaml", ".yml"):
                content = file_path.read_text(encoding="utf-8")
                chunks = parse_yaml_chunks(content, file_path)
            elif file_path.suffix in (".md", ".markdown"):
                content = file_path.read_text(encoding="utf-8")
                chunks = parse_markdown_chunks(content, file_path)

            for chunk in chunks:
                if chunk.id in seen_ids:
                    raise ValueError(
                        f"Duplicate chunk id detected: '{chunk.id}' in {file_path}"
                    )
                seen_ids.add(chunk.id)

                # Filter private or unindexed chunks based on search context
                if not include_private and chunk.private:
                    continue
                if not include_unindexed and not chunk.indexed:
                    continue

                all_chunks.append(chunk)

        return all_chunks
