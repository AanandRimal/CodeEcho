def first_hit_score(ranked: list, relevant: set) -> float:
    """Return 1/rank of the first relevant item in ranked (0.0 if none)."""
    for i, item in enumerate(ranked, 1):
        if item in relevant:
            return 1.0 / i
    return 0.0


if __name__ == "__main__":
    assert first_hit_score(["a", "b", "c"], {"b"}) == 0.5
    assert first_hit_score(["a", "b"], {"x"}) == 0.0
    assert first_hit_score(["a"], {"a"}) == 1.0
    print("ok")
