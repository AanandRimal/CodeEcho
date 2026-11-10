"""Reciprocal rank fusion (RRF) of several retrievers."""

from __future__ import annotations

from codeecho.indexer import FunctionUnit


class RRFRetriever:
    """Fuse ranked lists with RRF: score(d) = sum over retrievers of 1 / (k_rrf + rank(d)).

    k_rrf = 60 is the constant from Cormack, Clarke & Büttcher (SIGIR 2009). Each retriever
    contributes its top ``depth`` results; documents missing from a list get nothing from it.
    """

    def __init__(self, retrievers: list, k_rrf: int = 60, depth: int = 100) -> None:
        self.retrievers = retrievers
        self.k_rrf = k_rrf
        self.depth = depth

    def search(self, query: str, k: int = 10) -> list[tuple[FunctionUnit, float]]:
        """Return the top-k fused results, best first. Ties keep first-seen order."""
        scores: dict[FunctionUnit, float] = {}
        for r in self.retrievers:
            for rank, (unit, _) in enumerate(r.search(query, self.depth), start=1):
                scores[unit] = scores.get(unit, 0.0) + 1.0 / (self.k_rrf + rank)
        return sorted(scores.items(), key=lambda kv: -kv[1])[:k]  # sorted() is stable
