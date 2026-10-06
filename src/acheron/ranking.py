from __future__ import annotations

from typing import Any


def _model_ranks(scores: list[float | None]) -> list[int]:
    """Rank positions aligned to input order; unscored candidates rank last,
    keeping their native relative order (stable)."""
    order = sorted(
        range(len(scores)),
        key=lambda i: (scores[i] is None, -(scores[i] or 0.0), i),
    )
    ranks = [0] * len(scores)
    for position, index in enumerate(order, 1):
        ranks[index] = position
    return ranks


def rank_by_model(
    candidates: list[dict],
    model_scores: list[float | None] | None,
) -> list[dict[str, Any]]:
    """Order candidates by decision-model score alone; native order breaks ties.
    Falls back to native order when no scores are available."""
    if model_scores is None:
        return fuse(candidates, None)
    ranks = _model_ranks(model_scores)
    ranked = []
    for i, candidate in enumerate(candidates):
        ranked.append(
            {
                **candidate,
                "native_rank": i + 1,
                "model_rank": ranks[i],
                "model_score": model_scores[i],
                "fused_score": None,
            }
        )
    ranked.sort(key=lambda c: (c["model_rank"], c["native_rank"]))
    return ranked


def fuse(
    candidates: list[dict],
    model_scores: list[float | None] | None,
    k: int = 60,
) -> list[dict[str, Any]]:
    """Reciprocal rank fusion of native order and decision-model ranking.

    When model_scores is None (provider disabled or failed), the model term
    contributes nothing and native order is preserved.
    """
    n = len(candidates)
    if not n:
        return []
    model_ranks = _model_ranks(model_scores) if model_scores is not None else list(range(1, n + 1))

    fused = []
    for i, candidate in enumerate(candidates):
        native_rank = i + 1
        model_rank = model_ranks[i]
        fused_score = 1.0 / (k + native_rank) + 1.0 / (k + model_rank)
        fused.append(
            {
                **candidate,
                "native_rank": native_rank,
                "model_rank": model_rank,
                "model_score": model_scores[i] if model_scores is not None else None,
                "fused_score": fused_score,
            }
        )
    fused.sort(key=lambda c: (-c["fused_score"], c["native_rank"]))
    return fused
