"""Ranking metrics for the retrieval evaluation. Relevance is binary; a query's `relevant` is a set."""

from __future__ import annotations

import math

import numpy as np


def reciprocal_rank(ranked: list, relevant: set) -> float:
    """1 / rank of the first relevant item, 0 if none is ranked."""
    return next((1.0 / i for i, x in enumerate(ranked, 1) if x in relevant), 0.0)


def recall_at_k(ranked: list, relevant: set, k: int) -> float:
    """Fraction of the relevant items found in the top k."""
    return len(relevant & set(ranked[:k])) / len(relevant)


def ndcg_at_k(ranked: list, relevant: set, k: int = 10) -> float:
    """Binary-gain NDCG@k, log2 discount."""
    dcg = sum(1 / math.log2(i + 1) for i, x in enumerate(ranked[:k], 1) if x in relevant)
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal


def bootstrap_ci(values: list[float], seed: int = 0, n_boot: int = 10_000) -> tuple[float, float, float]:
    """Mean and 95% percentile bootstrap CI, resampling queries with replacement."""
    v = np.asarray(values, dtype=float)
    means = v[np.random.default_rng(seed).integers(0, len(v), (n_boot, len(v)))].mean(axis=1)
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))
