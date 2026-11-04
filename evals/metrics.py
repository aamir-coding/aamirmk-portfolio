"""Pure retrieval metrics with explicit relevance and alternative-source semantics."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from evals.schemas import ExpectedSources


class MetricModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class RankingScores(MetricModel):
    hit_at_3: int = Field(ge=0, le=1)
    hit_at_5: int = Field(ge=0, le=1)
    reciprocal_rank_at_5: float = Field(ge=0, le=1)
    recall_at_3: float | None = Field(default=None, ge=0, le=1)
    recall_at_5: float | None = Field(default=None, ge=0, le=1)


class MetricMean(MetricModel):
    numerator: float = Field(ge=0)
    denominator: int = Field(ge=0)
    value: float | None = Field(ge=0, le=1)

    @model_validator(mode="after")
    def consistent_mean(self) -> Self:
        if self.denominator == 0:
            if self.numerator != 0 or self.value is not None:
                raise ValueError("An empty denominator must have a null score")
        elif self.value is None or not math.isclose(
            self.value,
            self.numerator / self.denominator,
            abs_tol=1e-12,
        ):
            raise ValueError("Metric value differs from its numerator/denominator")
        return self


class RetrievalMetrics(MetricModel):
    hit_at_3: MetricMean
    hit_at_5: MetricMean
    mrr_at_5: MetricMean
    recall_at_3: MetricMean
    recall_at_5: MetricMean


def score_ranking(
    retrieved_ids: Sequence[str],
    expected: ExpectedSources,
) -> RankingScores | None:
    if len(retrieved_ids) != len(set(retrieved_ids)):
        raise ValueError("Duplicate retrieved IDs invalidate the ranking")
    if expected.mode == "none":
        return None
    relevant = set(expected.ids)
    top3, top5 = set(retrieved_ids[:3]), set(retrieved_ids[:5])
    first = next(
        (rank for rank, cid in enumerate(retrieved_ids[:5], 1) if cid in relevant), None
    )
    return RankingScores(
        hit_at_3=int(bool(top3 & relevant)),
        hit_at_5=int(first is not None),
        reciprocal_rank_at_5=1 / first if first is not None else 0,
        recall_at_3=len(top3 & relevant) / len(relevant)
        if expected.mode == "all_relevant"
        else None,
        recall_at_5=len(top5 & relevant) / len(relevant)
        if expected.mode == "all_relevant"
        else None,
    )


def _mean(values: list[float]) -> MetricMean:
    numerator = math.fsum(values)
    return MetricMean(
        numerator=numerator,
        denominator=len(values),
        value=numerator / len(values) if values else None,
    )


def summarize_scores(scores: Sequence[RankingScores]) -> RetrievalMetrics:
    """Macro averages; recall excludes cases labeled only with alternatives."""
    return RetrievalMetrics(
        hit_at_3=_mean([score.hit_at_3 for score in scores]),
        hit_at_5=_mean([score.hit_at_5 for score in scores]),
        mrr_at_5=_mean([score.reciprocal_rank_at_5 for score in scores]),
        recall_at_3=_mean(
            [score.recall_at_3 for score in scores if score.recall_at_3 is not None]
        ),
        recall_at_5=_mean(
            [score.recall_at_5 for score in scores if score.recall_at_5 is not None]
        ),
    )
