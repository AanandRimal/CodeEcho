"""Cross-encoder reranking of a first-stage retriever's top-N candidates."""

from __future__ import annotations

from devtrust.indexer import FunctionUnit
from devtrust.retrieval import doc_text

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"  # formerly "ms-marco-MiniLM-L-6-v2"; Apache-2.0
REVISION = {DEFAULT_MODEL: "233902d25c440f23af6f7d6e94d2946bac0bee0a"}


class CrossEncoderReranker:
    """Retrieve top_n candidates with ``base``, then reorder them by a cross-encoder's score."""

    def __init__(self, base, model_name: str = DEFAULT_MODEL, top_n: int = 50,
                 include_docstring: bool = False, max_length: int = 512) -> None:
        from sentence_transformers import CrossEncoder  # heavy import, only when used

        self.base = base
        self.top_n = top_n
        self.include_docstring = include_docstring
        self.model = CrossEncoder(model_name, device="cpu", revision=REVISION.get(model_name),
                                  max_length=max_length)

    def search(self, query: str, k: int = 10) -> list[tuple[FunctionUnit, float]]:
        """Return the top-k reranked units, best first."""
        candidates = [u for u, _ in self.base.search(query, self.top_n)]
        if not candidates:
            return []
        scores = self.model.predict([(query, doc_text(u, self.include_docstring)) for u in candidates])
        ranked = sorted(zip(candidates, (float(s) for s in scores)), key=lambda p: -p[1])
        return ranked[:k]
