"""Dense (embedding) retriever with an on-disk embedding cache."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from codeecho.indexer import FunctionUnit
from codeecho.retrieval import doc_text

# Query prefixes required or recommended by each model card (code side needs none for either):
# - BGE v1.5: "Represent this sentence for searching relevant passages: " (optional; helps short queries)
# - CodeRankEmbed: "Represent this query for searching relevant code: " (required)
QUERY_PREFIX = {
    "BAAI/bge-small-en-v1.5": "Represent this sentence for searching relevant passages: ",
    "nomic-ai/CodeRankEmbed": "Represent this query for searching relevant code: ",
}
TRUST_REMOTE_CODE = {"nomic-ai/CodeRankEmbed"}  # model ships custom modelling code (per its model card)
# Pinned Hugging Face revisions: results stay reproducible and remote code can't change under us.
REVISION = {
    "BAAI/bge-small-en-v1.5": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a",
    "nomic-ai/CodeRankEmbed": "3c4b60807d71f79b43f3c4363786d9493691f8b1",
}


_MODELS: dict[str, object] = {}   # loaded models are reused: a review over many PRs builds many retrievers


class DenseRetriever:
    """Cosine-similarity search over sentence-transformers embeddings of function text."""

    def __init__(self, units: list[FunctionUnit], model_name: str = "BAAI/bge-small-en-v1.5",
                 include_docstring: bool = False, max_seq_length: int = 512,
                 cache_dir: str | Path = ".cache/embeddings", batch_size: int = 32) -> None:
        from sentence_transformers import SentenceTransformer  # heavy import, only when used

        self.units = units
        self.model_name = model_name
        if model_name not in _MODELS:
            _MODELS[model_name] = SentenceTransformer(model_name, device="cpu", revision=REVISION.get(model_name),
                                                      trust_remote_code=model_name in TRUST_REMOTE_CODE)
        self.model = _MODELS[model_name]
        # ponytail: truncates long functions to 512 tokens to keep CPU cost sane; CodeRankEmbed allows 8192.
        self.model.max_seq_length = max_seq_length
        texts = [doc_text(u, include_docstring) for u in units]
        self._matrix = self._embed_cached(texts, Path(cache_dir), batch_size)

    def _embed_cached(self, texts: list[str], cache_dir: Path, batch_size: int) -> np.ndarray:
        """Embed texts, reusing vectors cached by (model, revision, max_seq_length, sha256 of text)."""
        rev = (REVISION.get(self.model_name) or "unpinned")[:12]
        slug = f"{self.model_name.replace('/', '__')}__{rev}__{self.model.max_seq_length}"
        path = cache_dir / f"{slug}.npz"
        cache: dict[str, np.ndarray] = {}
        if path.exists():
            with np.load(path) as f:
                cache = dict(zip(f["keys"], f["vectors"]))
        keys = [hashlib.sha256(t.encode()).hexdigest() for t in texts]
        missing = sorted({k: t for k, t in zip(keys, texts) if k not in cache}.items())
        if missing:
            vecs = self.model.encode([t for _, t in missing], batch_size=batch_size,
                                     normalize_embeddings=True, convert_to_numpy=True)
            cache.update(zip((k for k, _ in missing), vecs))
            cache_dir.mkdir(parents=True, exist_ok=True)
            np.savez(path, keys=np.array(list(cache)), vectors=np.stack(list(cache.values())))
        if not keys:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        return np.stack([cache[k] for k in keys]).astype(np.float32)

    def search(self, query: str, k: int = 10) -> list[tuple[FunctionUnit, float]]:
        """Return the top-k units by cosine similarity to the query, best first."""
        q = self.model.encode(QUERY_PREFIX.get(self.model_name, "") + query,
                              normalize_embeddings=True, convert_to_numpy=True)
        scores = self._matrix @ q
        top = np.argsort(-scores, kind="stable")[:k]
        return [(self.units[i], float(scores[i])) for i in top]
