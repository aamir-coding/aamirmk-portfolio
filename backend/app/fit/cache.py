"""Bounded LRU fit reports bound to exact input and an immutable app snapshot."""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.fit.models import FitReport, FitRequest
from app.fit.sample_jds import SampleJobDescription, load_sample_jds


class CuratedProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    review_reference: str = Field(min_length=1)
    facts_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reports_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    samples: dict[str, str]


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def curated_source_hashes() -> dict[str, str]:
    root = Path(__file__).parents[1]
    paths = sorted((root / "data/facts").rglob("*"))
    facts = {
        p.relative_to(root).as_posix(): text_hash(p.read_text(encoding="utf-8"))
        for p in paths
        if p.suffix in {".md", ".yaml"}
    }
    return {
        "facts_sha256": text_hash(json.dumps(facts, sort_keys=True)),
        "reports_sha256": text_hash(
            Path(__file__).with_name("golden_benchmarks.py").read_text(encoding="utf-8")
        ),
    }


def cache_identity(models: tuple[str, str]) -> str:
    root = Path(__file__).parents[1]
    paths = [
        *root.rglob("*.py"),
        *root.rglob("*.md"),
        *root.rglob("*.yaml"),
        *root.rglob("*.txt"),
        root / "retrieval/facts_embeddings.npz",
        root / "fit/curated-provenance.json",
    ]
    hashes = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }
    payload = json.dumps({"models": models, "files": hashes}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


class ReportCache:
    """Authored presets stay distinct from expiring generated reports."""

    def __init__(
        self,
        *,
        identity: str,
        max_entries: int = 64,
        ttl_seconds: float = 900,
        include_curated: bool = True,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_entries < 1 or not math.isfinite(ttl_seconds) or ttl_seconds <= 0:
            raise ValueError("Positive finite cache bounds are required")
        self.identity, self.max_entries, self.ttl_seconds = (
            identity,
            max_entries,
            ttl_seconds,
        )
        self.clock = clock
        self._entries: OrderedDict[str, tuple[float, FitReport]] = OrderedDict()
        self._presets = load_sample_jds() if include_curated else []
        self._curated_provenance: CuratedProvenance | None = None
        if include_curated:
            try:
                path = Path(__file__).with_name("curated-provenance.json")
                provenance = CuratedProvenance.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
                hashes = curated_source_hashes()
                if all(
                    getattr(provenance, key) == value for key, value in hashes.items()
                ):
                    self._curated_provenance = provenance
            except (OSError, ValueError):
                pass

    def presets(self) -> list[SampleJobDescription]:
        """Stale authored reports are unavailable; public JD text remains useful."""
        return [
            sample if self._current(sample) else replace(sample, report=None)
            for sample in self._presets
        ]

    def _current(self, sample: SampleJobDescription) -> bool:
        provenance = self._curated_provenance
        return bool(
            provenance is not None
            and sample.report is not None
            and provenance.samples.get(sample.id) == text_hash(sample.text)
            and sample.report.jd_hash == FitRequest(jd_text=sample.text).compute_hash()
        )

    def key(self, request: FitRequest) -> str:
        payload = json.dumps(
            {
                "identity": self.identity,
                "jd": request.jd_text,
                "role_title": request.role_title,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(
        self, request: FitRequest
    ) -> tuple[FitReport, Literal["curated", "cache"]] | None:
        if request.force_live:
            return None
        for sample in self._presets:
            if (
                not self._current(sample)
                or request.jd_text.strip() != sample.text.strip()
            ):
                continue
            assert sample.report is not None
            if request.role_title and request.role_title not in {
                sample.title,
                sample.report.role_title,
            }:
                continue
            return sample.report.model_copy(
                deep=True, update={"cached": True}
            ), "curated"
        key = self.key(request)
        entry = self._entries.get(key)
        if entry is None:
            return None
        expiry, report = entry
        if self.clock() >= expiry:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return report.model_copy(deep=True, update={"cached": True}), "cache"

    def put(self, request: FitRequest, report: FitReport) -> None:
        now = self.clock()
        for key, (expiry, _) in list(self._entries.items()):
            if now >= expiry:
                del self._entries[key]
        key = self.key(request)
        self._entries[key] = (now + self.ttl_seconds, report.model_copy(deep=True))
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def __len__(self) -> int:
        return len(self._entries)
