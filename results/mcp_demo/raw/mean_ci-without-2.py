import random
from statistics import mean


def mean_ci(values: list[float], n: int = 1000, seed: int = 42) -> tuple[float, float, float]:
    """Mean and 95% bootstrap confidence interval (mean, low, high)."""
    rng = random.Random(seed)
    k = len(values)
    means = sorted(mean(rng.choices(values, k=k)) for _ in range(n))
    return mean(values), means[int(0.025 * n)], means[int(0.975 * n)]


if __name__ == "__main__":
    m, lo, hi = mean_ci([1, 2, 3, 4, 5])
    assert lo <= m <= hi, (lo, m, hi)
    assert mean_ci([1, 2, 3, 4, 5]) == mean_ci([1, 2, 3, 4, 5])  # deterministic
    print(m, lo, hi)
