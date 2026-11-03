"""Deterministic scoring and anti-overclaiming engine for JD Fit Reports.

Enforces server-side truthfulness invariants:
1. Anti-overclaiming rule: If the LLM assigns 'strong' or 'partial' but cites
   no valid, retrieved chunk ID, server unconditionally overrides verdict to 'gap'.
2. Deterministic scoring: All match numbers, ratios, and tier evaluations are
   computed strictly in Python code — never hallucinated by an LLM prompt.
"""

from __future__ import annotations

import logging
from collections.abc import Collection, Mapping

from app.fit.models import FitScoreSummary, JudgedRequirement

logger = logging.getLogger(__name__)

DEFAULT_GAP_RAMP_UP = (
    "No verified project evidence in current portfolio; would require "
    "structured ramp-up and codebase onboarding."
)


def validate_and_downgrade_verdicts(
    judged_requirements: list[JudgedRequirement],
    valid_chunk_ids: Mapping[str, Collection[str]],
) -> list[JudgedRequirement]:
    """Enforce the anti-overclaiming invariant on LLM-judged requirements.

    Any 'strong' or 'partial' verdict that lacks valid evidence chunk IDs
    (or cites unknown/invented chunk IDs) is downgraded to 'gap'.
    """
    sanitized: list[JudgedRequirement] = []

    for item in judged_requirements:
        valid_id_set = set(valid_chunk_ids.get(item.requirement.id, ()))
        # Filter citations to only those that actually exist in the retrieved corpus
        verified_chunk_ids = [
            cid for cid in item.evidence_chunk_ids if cid in valid_id_set
        ]

        if item.verdict in ("strong", "partial"):
            if not verified_chunk_ids:
                logger.warning(
                    "Anti-overclaiming trigger: requirement '%s' claimed verdict '%s' "
                    "with invalid/missing chunk IDs %s. Downgrading to 'gap'.",
                    item.requirement.id,
                    item.verdict,
                    item.evidence_chunk_ids,
                )
                downgraded_explanation = (
                    f"{item.explanation.strip()} "
                    "[Downgraded to gap: No verified portfolio evidence cited.]"
                )
                ramp_up_plan = item.ramp_up or DEFAULT_GAP_RAMP_UP

                sanitized.append(
                    JudgedRequirement(
                        requirement=item.requirement,
                        verdict="gap",
                        evidence_chunk_ids=[],
                        explanation=downgraded_explanation[:300],
                        ramp_up=ramp_up_plan[:300],
                        downgraded=True,
                    )
                )
                continue

            # Retain valid evidence citations
            sanitized.append(
                JudgedRequirement(
                    requirement=item.requirement,
                    verdict=item.verdict,
                    evidence_chunk_ids=verified_chunk_ids,
                    explanation=item.explanation,
                    ramp_up=item.ramp_up,
                    downgraded=item.downgraded,
                )
            )
        else:
            # For gap verdicts, ensure honest ramp-up exists
            sanitized.append(
                JudgedRequirement(
                    requirement=item.requirement,
                    verdict="gap",
                    evidence_chunk_ids=verified_chunk_ids,
                    explanation=item.explanation,
                    ramp_up=item.ramp_up or DEFAULT_GAP_RAMP_UP,
                    downgraded=item.downgraded,
                )
            )

    return sanitized


def compute_fit_summary(
    judged_requirements: list[JudgedRequirement],
) -> FitScoreSummary:
    """Compute deterministic match metrics directly from judged requirements."""
    must_have_strong = 0
    must_have_partial = 0
    must_have_gap = 0
    must_have_total = 0

    nice_to_have_strong = 0
    nice_to_have_partial = 0
    nice_to_have_gap = 0
    nice_to_have_total = 0

    for item in judged_requirements:
        if item.requirement.importance == "must_have":
            must_have_total += 1
            if item.verdict == "strong":
                must_have_strong += 1
            elif item.verdict == "partial":
                must_have_partial += 1
            else:
                must_have_gap += 1
        else:
            nice_to_have_total += 1
            if item.verdict == "strong":
                nice_to_have_strong += 1
            elif item.verdict == "partial":
                nice_to_have_partial += 1
            else:
                nice_to_have_gap += 1

    total_requirements = must_have_total + nice_to_have_total

    # Deterministic overall fit logic
    if must_have_total == 0:
        if nice_to_have_total > 0 and nice_to_have_strong >= (nice_to_have_total / 2):
            overall_fit = "Strong Match"
        elif (nice_to_have_strong + nice_to_have_partial) > 0:
            overall_fit = "Partial Match"
        else:
            overall_fit = "Low Match"
    else:
        # Strict must-have thresholds
        if must_have_gap == 0 and must_have_strong >= (must_have_total * 0.7):
            overall_fit = "Strong Match"
        elif (must_have_strong + must_have_partial) >= (must_have_total * 0.5):
            overall_fit = "Partial Match"
        else:
            overall_fit = "Low Match"

    # Deterministic summary headline
    if must_have_total > 0 and nice_to_have_total > 0:
        headline = (
            f"Covers {must_have_strong} of {must_have_total} must-haves "
            f"({must_have_partial} partial), "
            f"{nice_to_have_strong} of {nice_to_have_total} nice-to-haves"
        )
    elif must_have_total > 0:
        headline = (
            f"Covers {must_have_strong} of {must_have_total} must-haves "
            f"({must_have_partial} partial, {must_have_gap} gap)"
        )
    else:
        headline = (
            f"Covers {nice_to_have_strong} of {nice_to_have_total} "
            f"preferred requirements ({nice_to_have_partial} partial)"
        )

    return FitScoreSummary(
        must_have_total=must_have_total,
        must_have_strong=must_have_strong,
        must_have_partial=must_have_partial,
        must_have_gap=must_have_gap,
        nice_to_have_total=nice_to_have_total,
        nice_to_have_strong=nice_to_have_strong,
        nice_to_have_partial=nice_to_have_partial,
        nice_to_have_gap=nice_to_have_gap,
        total_requirements=total_requirements,
        overall_fit=overall_fit,
        headline=headline,
    )
