"""Hand-computed checks for eval/metrics.py."""

import math

from eval.metrics import bootstrap_ci, ndcg_at_k, recall_at_k, reciprocal_rank


def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b", "c"], {"b"}) == 0.5
    assert reciprocal_rank(["a", "b"], {"z"}) == 0.0


def test_recall_at_k():
    assert recall_at_k(["a", "b", "c"], {"a", "c", "z"}, 1) == 1 / 3
    assert recall_at_k(["a", "b", "c"], {"a", "c", "z"}, 3) == 2 / 3


def test_ndcg_at_k():
    assert ndcg_at_k(["a", "b"], {"a"}) == 1.0
    # relevant at ranks 2 and 3, two relevant total: DCG = 1/log2(3) + 1/log2(4); IDCG = 1 + 1/log2(3)
    expect = (1 / math.log2(3) + 0.5) / (1 + 1 / math.log2(3))
    assert math.isclose(ndcg_at_k(["x", "a", "b"], {"a", "b"}), expect)
    assert ndcg_at_k(["x", "y"], {"a"}) == 0.0


def test_bootstrap_ci_brackets_mean_and_is_seeded():
    vals = [0.0, 1.0, 1.0, 0.5, 0.25, 1.0]
    mean, lo, hi = bootstrap_ci(vals, seed=1)
    assert lo <= mean <= hi and bootstrap_ci(vals, seed=1) == (mean, lo, hi)
    assert bootstrap_ci([0.7] * 5) == (0.7, 0.7, 0.7)
