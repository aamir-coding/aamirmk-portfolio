"""Deterministic, multi-stage Job Fit Report evaluation pipeline.

Coordinates requirement extraction, hybrid factual retrieval, batched judging,
anti-overclaiming enforcement, and summary generation with streaming progress updates.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from app.fit.cache import ReportCache, cache_identity
from app.fit.models import (
    FitReport,
    FitRequest,
    FitScoreSummary,
    JudgedRequirement,
    Requirement,
    RequirementExtraction,
)
from app.fit.prompts import (
    build_extraction_messages,
    build_judging_messages,
    build_summary_messages,
)
from app.fit.scorer import compute_fit_summary, validate_and_downgrade_verdicts
from app.llm import LLMCapacityError, LLMClient, LLMError, Message
from app.retrieval.models import RetrievedChunk
from app.retrieval.retriever import Retriever
from app.safety.guardrails import check_prompt_injection
from app.settings import Settings, get_settings
from app.telemetry import (
    ObservedLLM,
    ObservedRetriever,
    Trace,
    active_trace,
    provenance,
)

logger = logging.getLogger(__name__)


class RequirementExtractionError(ValueError):
    """No trustworthy requirement set could be extracted after the bounded retry."""


class FitPipeline:
    """Fixed-stage deep module for generating grounded JD fit reports."""

    def __init__(
        self,
        llm: LLMClient,
        retriever: Retriever,
        settings: Settings | None = None,
        cache: ReportCache | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._llm = ObservedLLM(llm, main_model=self._settings.LLM_MODEL_MAIN)
        self._retriever = ObservedRetriever(retriever)
        self._cache = (
            cache
            if cache is not None
            else ReportCache(
                identity=cache_identity(
                    (self._settings.LLM_MODEL_MAIN, self._settings.LLM_MODEL_UTILITY)
                ),
                include_curated=cache is None,
            )
        )

    async def run(self, request: FitRequest) -> AsyncIterator[dict[str, Any]]:
        trace = Trace()
        versions = await asyncio.to_thread(provenance)
        iterator = self._run(request)
        deadline = time.monotonic() + 90
        try:
            while True:
                # Heartbeat transport resumes each __anext__ in a separate task.
                # Install/reset within that task, never across a yielded frame.
                token = active_trace.set(trace)
                try:
                    frame = await asyncio.wait_for(
                        anext(iterator), timeout=max(0, deadline - time.monotonic())
                    )
                except StopAsyncIteration:
                    return
                finally:
                    active_trace.reset(token)
                if frame["event"] == "progress":
                    stage = frame["data"]["step"]
                    if stage == "cache_hit":
                        trace.origin = frame["data"].get("origin", "cache")
                    trace.set_stage(stage)
                elif frame["event"] in {"complete", "error"}:
                    if frame["event"] == "complete":
                        trace.text()
                    frame = {
                        **frame,
                        "data": {
                            **frame["data"],
                            "telemetry": {**trace.snapshot().model_dump(), **versions},
                        },
                    }
                yield frame
        except TimeoutError:
            yield {
                "event": "error",
                "data": {
                    "code": "upstream_timeout",
                    "message": (
                        "The live report timed out. Try a curated example "
                        "or contact Aamir."
                    ),
                    "telemetry": {**trace.snapshot().model_dump(), **versions},
                },
            }
        finally:
            await iterator.aclose()

    async def _run(self, request: FitRequest) -> AsyncIterator[dict[str, Any]]:
        """Execute the 5-stage pipeline and yield SSE progress & completion frames."""
        jd_hash = request.compute_hash()
        if not check_prompt_injection(
            request.jd_text + "\n" + (request.role_title or "")
        ).is_safe:
            yield {
                "event": "error",
                "data": {
                    "code": "unsafe_input",
                    "message": (
                        "Please provide job requirements "
                        "without assistant instructions."
                    ),
                },
            }
            return

        # Step 0: Check content-hash cache
        cached = self._cache.get(request)
        if cached is not None:
            logger.info("Fit cache hit")
            cached_report, origin = cached
            yield {
                "event": "progress",
                "data": {
                    "step": "cache_hit",
                    "message": "Instant match found in verification cache.",
                    "percent": 100,
                    "origin": origin,
                },
            }
            yield {
                "event": "complete",
                "data": cached_report.model_copy(update={"cached": True}).model_dump(),
            }
            return

        try:
            # Step 1: Read and analyze structure
            yield {
                "event": "progress",
                "data": {
                    "step": "reading_jd",
                    "message": "Reading job description and analyzing role scope...",
                    "percent": 10,
                },
            }

            # Step 2: Extract requirements with utility model
            yield {
                "event": "progress",
                "data": {
                    "step": "extracting_requirements",
                    "message": "Extracting core technical requirements...",
                    "percent": 25,
                },
            }
            extraction = await self._extract_requirements(request)

            # Step 3: Per-requirement hybrid retrieval
            req_count = len(extraction.requirements)
            yield {
                "event": "progress",
                "data": {
                    "step": "retrieving_evidence",
                    "message": (
                        f"Cross-referencing {req_count} requirements with "
                        "Aamir's verified facts..."
                    ),
                    "percent": 50,
                },
            }
            retrieved_by_req, valid_chunk_ids_by_req = await self._retrieve_evidence(
                extraction.requirements
            )

            # Step 4: Batched LLM judging with main model
            yield {
                "event": "progress",
                "data": {
                    "step": "evaluating_fit",
                    "message": (
                        "Evaluating alignment, checking citations, and "
                        "identifying gaps..."
                    ),
                    "percent": 75,
                },
            }
            raw_judged = await self._judge_requirements(
                extraction.requirements, retrieved_by_req
            )

            # Step 5: Anti-overclaiming invariant & scoring (pure Python)
            sanitized_judged = validate_and_downgrade_verdicts(
                raw_judged, valid_chunk_ids_by_req
            )
            score_summary = compute_fit_summary(sanitized_judged)

            # Step 6: Balanced executive summary synthesis
            yield {
                "event": "progress",
                "data": {
                    "step": "synthesizing",
                    "message": "Formulating executive summary recommendations...",
                    "percent": 90,
                },
            }
            if any(
                item.verdict == "gap" or item.downgraded for item in sanitized_judged
            ):
                strong = sum(item.verdict == "strong" for item in sanitized_judged)
                partial = sum(item.verdict == "partial" for item in sanitized_judged)
                gaps = len(sanitized_judged) - strong - partial
                summary_text = (
                    f"Current portfolio judgments: {strong} strong, {partial} partial "
                    f"and {gaps} gap requirements. These judgments are limited to the "
                    "cited material. Review the evidence and any gaps with Aamir."
                )
            else:
                summary_text = await self._generate_summary(
                    extraction.role_title, sanitized_judged, score_summary
                )

            # Final Report Assembly
            report = FitReport(
                role_title=extraction.role_title,
                jd_hash=jd_hash,
                score=score_summary,
                requirements=sanitized_judged,
                summary=summary_text,
                cached=False,
            )
            # Store in in-memory cache
            self._cache.put(request, report)

            yield {
                "event": "complete",
                "data": report.model_dump(),
            }

        except RequirementExtractionError:
            yield {
                "event": "error",
                "data": {
                    "code": "extraction_error",
                    ("message"): (
                        "Could not extract valid job requirements. Please retry or "
                        "clarify the job description."
                    ),
                },
            }
        except LLMCapacityError:
            yield {
                "event": "error",
                "data": {
                    "code": "resting",
                    "state": "resting",
                    "message": (
                        "Live reports are resting. Explore a curated example "
                        "or contact Aamir."
                    ),
                },
            }
        except LLMError as err:
            logger.error("LLM fit failure: %s", type(err).__name__)
            yield {
                "event": "error",
                "data": {
                    "code": "upstream_error",
                    "message": (
                        "Inference service momentarily unavailable. Please retry."
                    ),
                },
            }
        except Exception as err:
            logger.error("Fit pipeline failure: %s", type(err).__name__)
            yield {
                "event": "error",
                "data": {
                    "code": "internal_error",
                    "message": "Failed to analyze job description. Please check input.",
                },
            }

    async def _extract_requirements(self, request: FitRequest) -> RequirementExtraction:
        """Call utility model to extract structured requirements with retry."""
        messages = build_extraction_messages(request.jd_text, request.role_title)

        for attempt in range(2):
            try:
                reply = await self._llm.complete(
                    messages=messages,
                    model=self._settings.LLM_MODEL_UTILITY,
                    response_format={"type": "json_object"},
                )
                data = json.loads(reply.content)
                role_title = request.role_title or data.get("role_title", "Target Role")
                raw_reqs = data.get("requirements", [])
                if not raw_reqs:
                    raise ValueError("Empty requirements list from extractor.")

                reqs: list[Requirement] = []
                for idx, r in enumerate(raw_reqs[:8], start=1):
                    req_id = r.get("id") or f"req-{idx}"
                    text = r.get("text", "").strip()
                    if not text:
                        raise ValueError("Requirement text must not be empty.")
                    imp_val = r.get("importance")
                    importance = (
                        imp_val
                        if imp_val in ("must_have", "nice_to_have")
                        else "must_have"
                    )
                    type_val = r.get("type")
                    req_type = (
                        type_val
                        if type_val in ("skill", "experience", "education", "soft")
                        else "skill"
                    )
                    reqs.append(
                        Requirement(
                            id=req_id,
                            text=text[:300],
                            importance=importance,
                            type=req_type,
                        )
                    )

                return RequirementExtraction(role_title=role_title, requirements=reqs)
            except LLMError:
                raise
            except Exception as exc:
                logger.warning(
                    "Extraction attempt %d failed: %s", attempt + 1, type(exc).__name__
                )
                if attempt == 0:
                    messages.append(
                        Message(
                            role="user",
                            content=(
                                "Previous output failed schema validation. "
                                "Return strictly valid JSON."
                            ),
                        )
                    )

        raise RequirementExtractionError("Requirement extraction failed twice.")

    async def _retrieve_evidence(
        self, requirements: list[Requirement]
    ) -> tuple[dict[str, list[RetrievedChunk]], dict[str, set[str]]]:
        """Retrieve candidate facts for each extracted requirement."""
        retrieved_by_req: dict[str, list[RetrievedChunk]] = {}
        chunk_ids_by_req: dict[str, set[str]] = {}

        for req in requirements:
            chunks = await self._retriever.retrieve(req.text, top_k=2)
            chunks = [rc for rc in chunks if not rc.chunk.private and rc.chunk.indexed]
            retrieved_by_req[req.id] = chunks
            chunk_ids_by_req[req.id] = {rc.chunk.id for rc in chunks}

        return retrieved_by_req, chunk_ids_by_req

    async def _judge_requirements(
        self,
        requirements: list[Requirement],
        retrieved_by_req: dict[str, list[RetrievedChunk]],
        batch_size: int = 4,
    ) -> list[JudgedRequirement]:
        """Evaluate requirements in batches using main model."""
        judged_list: list[JudgedRequirement] = []

        for i in range(0, len(requirements), batch_size):
            batch = requirements[i : i + batch_size]
            messages = build_judging_messages(batch, retrieved_by_req)

            try:
                reply = await self._llm.complete(
                    messages=messages,
                    model=self._settings.LLM_MODEL_MAIN,
                    response_format={"type": "json_object"},
                )
                data = json.loads(reply.content)
                judged_entries = data.get("judged", [])

                entry_map = {
                    e.get("requirement_id"): e
                    for e in judged_entries
                    if isinstance(e, dict)
                }

                for req in batch:
                    entry = entry_map.get(req.id)
                    if entry:
                        verdict = entry.get("verdict", "gap")
                        if verdict not in ("strong", "partial", "gap"):
                            verdict = "gap"
                        evidence_ids = entry.get("evidence_chunk_ids") or []
                        if not isinstance(evidence_ids, list):
                            evidence_ids = []
                        explanation = str(
                            entry.get(
                                "explanation",
                                "Evaluated against portfolio facts.",
                            )
                        )[:300]
                        ramp_up = entry.get("ramp_up")
                        if ramp_up is not None:
                            ramp_up = str(ramp_up)[:300]

                        judged_list.append(
                            JudgedRequirement(
                                requirement=req,
                                verdict=verdict,
                                evidence_chunk_ids=[str(cid) for cid in evidence_ids],
                                explanation=explanation,
                                ramp_up=ramp_up,
                            )
                        )
                    else:
                        judged_list.append(
                            JudgedRequirement(
                                requirement=req,
                                verdict="gap",
                                evidence_chunk_ids=[],
                                explanation="Not addressed in evaluation response.",
                                ramp_up="Review candidate projects and background.",
                            )
                        )
            except LLMError:
                raise
            except Exception as exc:
                logger.warning(
                    "Judging batch failed: %s; assigning safe gaps", type(exc).__name__
                )
                for req in batch:
                    judged_list.append(
                        JudgedRequirement(
                            requirement=req,
                            verdict="gap",
                            evidence_chunk_ids=[],
                            explanation="Evaluation error; defaulting to gap.",
                            ramp_up="Discuss directly during candidate interview.",
                        )
                    )

        return judged_list

    async def _generate_summary(
        self,
        role_title: str,
        judged: list[JudgedRequirement],
        score: FitScoreSummary,
    ) -> str:
        """Call main model to write balanced 3-sentence summary."""
        messages = build_summary_messages(role_title, judged, score)
        try:
            reply = await self._llm.complete(
                messages=messages,
                model=self._settings.LLM_MODEL_MAIN,
            )
            content = reply.content.strip()
            if len(content) > 20:
                return content
        except LLMError:
            raise
        except Exception as exc:
            logger.warning(
                "Summary generation failed: %s; using deterministic fallback",
                type(exc).__name__,
            )

        return (
            f"Aamir presents a {score.overall_fit.lower()} for the {role_title} role, "
            f"covering {score.must_have_strong} of {score.must_have_total} core "
            "requirements with verified evidence. "
            "Identified gaps can be addressed through his documented rapid ramp-up "
            "approach and containerization experience. "
            "A technical interview is recommended to discuss architecture alignment."
        )
