import random
from statistics import mean


def mean_ci(values: list[float], seed: int = 0) -> tuple[float, float, float]:
    """Mean and 95% bootstrap CI (mean, low, high). Deterministic via seed."""
    rng = random.Random(seed)
    n = len(values)
    means = sorted(mean(rng.choices(values, k=n)) for _ in range(1000))
    return mean(values), means[25], means[975]


if __name__ == "__main__":
    m, lo, hi = mean_ci([1, 2, 3, 4, 5])
    assert lo < m < hi, (lo, m, hi)
    assert mean_ci([1, 2, 3, 4, 5]) == mean_ci([1, 2, 3, 4, 5])  # deterministic
    print(m, lo, hi)
