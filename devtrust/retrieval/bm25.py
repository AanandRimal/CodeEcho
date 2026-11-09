"""BM25 retriever over function units."""

from __future__ import annotations

import numpy as np
from rank_bm25 import BM25Okapi

from devtrust.indexer import FunctionUnit
from devtrust.retrieval import doc_text, tokenize


class BM25Retriever:
    """Okapi BM25 (rank_bm25 defaults: k1=1.5, b=0.75) over signature + body text."""

    def __init__(self, units: list[FunctionUnit], split_identifiers: bool = True,
                 include_docstring: bool = False) -> None:
        self.units = units
        self.split_identifiers = split_identifiers
        self._bm25 = BM25Okapi([tokenize(doc_text(u, include_docstring), split_identifiers) for u in units])

    def search(self, query: str, k: int = 10) -> list[tuple[FunctionUnit, float]]:
        """Return the top-k units for a natural-language query, best first."""
        scores = self._bm25.get_scores(tokenize(query, self.split_identifiers))
        top = np.argsort(-scores, kind="stable")[:k]  # stable: ties keep index order, so output is deterministic
        return [(self.units[i], float(scores[i])) for i in top]
