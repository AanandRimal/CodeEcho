def first_hit_score(ranked: list, relevant: set) -> float:
    """Reciprocal rank of the first relevant item (0.0 if none)."""
    return next((1 / i for i, x in enumerate(ranked, 1) if x in relevant), 0.0)


if __name__ == "__main__":
    assert first_hit_score(["a", "b", "c"], {"b"}) == 0.5
    assert first_hit_score(["a", "b"], {"z"}) == 0.0
    assert first_hit_score(["x", "y"], {"x"}) == 1.0
