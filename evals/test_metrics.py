"""Known rankings distinguish source coverage, first-hit quality and exclusions."""

import pytest

from evals.metrics import score_ranking, summarize_scores
from evals.schemas import ExpectedSources


def test_recall_measures_all_relevant_coverage_while_hit_needs_only_one() -> None:
    labels = ExpectedSources(mode="all_relevant", ids=["a", "b", "c", "d"])
    scores = score_ranking(["x", "b", "y", "c", "z"], labels)
    assert scores is not None
    assert scores.hit_at_3 == scores.hit_at_5 == 1
    assert scores.recall_at_3 == 0.25
    assert scores.recall_at_5 == 0.50
    assert scores.reciprocal_rank_at_5 == 0.5


def test_alternatives_do_not_invent_a_recall_denominator() -> None:
    scores = score_ranking(["x", "a"], ExpectedSources(mode="any_of", ids=["a", "b"]))
    assert scores is not None
    assert scores.hit_at_3 == 1
    assert scores.recall_at_3 is scores.recall_at_5 is None
    assert scores.reciprocal_rank_at_5 == 0.5


@pytest.mark.parametrize(
    "position,hit3,hit5,rr",
    [
        (1, 1, 1, 1.0),
        (3, 1, 1, 1 / 3),
        (4, 0, 1, 0.25),
        (5, 0, 1, 0.2),
        (6, 0, 0, 0.0),
    ],
)
def test_cutoff_boundaries(position: int, hit3: int, hit5: int, rr: float) -> None:
    ranking = [f"irrelevant-{i}" for i in range(position - 1)] + ["a"]
    scores = score_ranking(ranking, ExpectedSources(mode="all_relevant", ids=["a"]))
    assert scores is not None
    assert (scores.hit_at_3, scores.hit_at_5, scores.reciprocal_rank_at_5) == (
        hit3,
        hit5,
        rr,
    )


def test_empty_ranking_is_a_miss_not_a_skipped_case() -> None:
    scores = score_ranking([], ExpectedSources(mode="all_relevant", ids=["a"]))
    assert scores is not None
    assert scores.hit_at_3 == scores.hit_at_5 == scores.reciprocal_rank_at_5 == 0
    assert scores.recall_at_3 == scores.recall_at_5 == 0


def test_nonapplicable_source_case_never_gets_a_perfect_score() -> None:
    assert score_ranking([], ExpectedSources(mode="none")) is None
    empty = summarize_scores([])
    for metric in (
        empty.hit_at_3,
        empty.hit_at_5,
        empty.mrr_at_5,
        empty.recall_at_3,
        empty.recall_at_5,
    ):
        assert metric.denominator == 0
        assert metric.value is None


def test_macro_recall_and_hit_denominators_are_separate() -> None:
    scores = [
        score_ranking(["a"], ExpectedSources(mode="all_relevant", ids=["a", "b"])),
        score_ranking([], ExpectedSources(mode="all_relevant", ids=["c"])),
        score_ranking(["d"], ExpectedSources(mode="any_of", ids=["d", "e"])),
    ]
    summary = summarize_scores([score for score in scores if score is not None])
    assert summary.hit_at_3.numerator == 2
    assert summary.hit_at_3.denominator == 3
    assert summary.hit_at_3.value == pytest.approx(2 / 3)
    assert summary.recall_at_3.numerator == 0.5
    assert summary.recall_at_3.denominator == 2
    assert summary.recall_at_3.value == 0.25


def test_duplicate_ranked_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        score_ranking(["a", "a"], ExpectedSources(mode="all_relevant", ids=["a", "b"]))
