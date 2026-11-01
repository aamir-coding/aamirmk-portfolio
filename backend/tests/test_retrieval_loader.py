"""Unit tests for FactChunk models and FactLoader."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.retrieval.loader import (
    FactLoader,
    parse_markdown_chunks,
    parse_yaml_chunks,
)
from app.retrieval.models import FactChunk, RetrievedChunk


def test_fact_chunk_validation_and_immutability():
    """FactChunk validates fields and enforces frozen immutability."""
    chunk = FactChunk(
        id="test-chunk",
        type="project",
        title="Test Project Title",
        content="This is verified content.",
        source_section="J1",
        tags=["test", "project"],
    )
    assert chunk.id == "test-chunk"
    assert chunk.draft is True
    assert chunk.private is False
    assert chunk.indexed is True
    assert chunk.tags == ["test", "project"]

    # Frozen check
    with pytest.raises(ValidationError):
        chunk.title = "Modified"  # type: ignore[misc]


def test_retrieved_chunk_validation():
    """RetrievedChunk wraps FactChunk with score, rank, and method."""
    fact = FactChunk(
        id="fact-1",
        type="skill",
        title="Python Skill",
        content="Proficient in Python.",
    )
    retrieved = RetrievedChunk(
        chunk=fact,
        score=0.88,
        rank=1,
        retrieval_method="bm25",
    )
    assert retrieved.rank == 1
    assert retrieved.score == 0.88
    assert retrieved.retrieval_method == "bm25"
    assert retrieved.chunk.id == "fact-1"

    # Rank must be >= 1
    with pytest.raises(ValidationError):
        RetrievedChunk(chunk=fact, score=0.5, rank=0)


def test_fact_loader_loads_production_facts():
    """FactLoader discovers and parses all facts in backend/app/data/facts."""
    loader = FactLoader()
    public_chunks = loader.load_all(include_private=False, include_unindexed=False)

    assert len(public_chunks) >= 70
    types = {c.type for c in public_chunks}
    expected_types = {
        "profile",
        "education",
        "experience",
        "project",
        "skill",
        "hr",
        "opinion",
        "achievement",
        "personal",
    }
    assert expected_types.issubset(types)

    # Every chunk must have non-empty id, title, and content
    for c in public_chunks:
        assert c.id.strip() != ""
        assert c.title.strip() != ""
        assert len(c.content.strip()) > 20
        assert c.private is False
        assert c.indexed is True


def test_fact_loader_excludes_boundary_policies_from_public_search():
    """Boundary policies are excluded unless explicitly requested."""
    loader = FactLoader()
    public_chunks = loader.load_all(include_private=False, include_unindexed=False)
    assert not any(c.id == "policy-boundaries" for c in public_chunks)

    all_chunks = loader.load_all(include_private=True, include_unindexed=True)
    boundary_chunks = [c for c in all_chunks if c.id == "policy-boundaries"]
    assert len(boundary_chunks) == 1
    assert boundary_chunks[0].private is True
    assert boundary_chunks[0].indexed is False


def test_fact_loader_detects_duplicate_chunk_ids(tmp_path: Path):
    """FactLoader raises ValueError if two chunks share the exact same id."""
    file1 = tmp_path / "fact1.md"
    file1.write_text(
        """---
id: "duplicate-id"
type: "skill"
title: "Skill 1"
---
Content 1
""",
        encoding="utf-8",
    )

    file2 = tmp_path / "fact2.md"
    file2.write_text(
        """---
id: "duplicate-id"
type: "skill"
title: "Skill 2"
---
Content 2
""",
        encoding="utf-8",
    )

    loader = FactLoader(facts_dir=tmp_path)
    with pytest.raises(ValueError, match="Duplicate chunk id detected: 'duplicate-id'"):
        loader.load_all()


def test_parse_yaml_chunks_handles_single_and_list(tmp_path: Path):
    """parse_yaml_chunks parses root dict with 'chunks' list or direct chunk."""
    yaml_content = """
chunks:
  - id: "y-chunk-1"
    type: "profile"
    title: "Profile Title"
    content: "Some content here"
  - id: "y-chunk-2"
    type: "skill"
    title: "Skill Title"
    content: "Another content"
"""
    f = tmp_path / "test.yaml"
    f.write_text(yaml_content, encoding="utf-8")
    chunks = parse_yaml_chunks(yaml_content, f)
    assert len(chunks) == 2
    assert chunks[0].id == "y-chunk-1"
    assert chunks[1].id == "y-chunk-2"


def test_parse_markdown_chunks_handles_multi_chunks(tmp_path: Path):
    """parse_markdown_chunks splits multiple frontmatter chunks in single file."""
    md_content = """---
id: "md-1"
type: "project"
title: "Project 1"
---
This is project 1 body text.

---
id: "md-2"
type: "project"
title: "Project 2"
tags: ["tagA", "tagB"]
---
This is project 2 body text.
"""
    f = tmp_path / "test.md"
    f.write_text(md_content, encoding="utf-8")
    chunks = parse_markdown_chunks(md_content, f)
    assert len(chunks) == 2
    assert chunks[0].id == "md-1"
    assert chunks[0].content == "This is project 1 body text."
    assert chunks[1].id == "md-2"
    assert chunks[1].tags == ["tagA", "tagB"]
