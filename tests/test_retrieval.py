"""Tests for Phase 2 retrievers."""

from codeecho.indexer import FunctionUnit
from codeecho.retrieval import doc_text, tokenize
from codeecho.retrieval.bm25 import BM25Retriever


def unit(name: str, body: str, doc: str | None = None) -> FunctionUnit:
    return FunctionUnit(name=name, qualname=f"m.{name}", signature=f"def {name}(x)", docstring=doc,
                        source="", body=body, file_path="m.py", start_line=1, end_line=2,
                        decorators=(), imports_used=())


UNITS = [
    unit("isValidEmail", "return '@' in x", doc="Check an email address."),
    unit("parse_http_response", "return x.split('\\n')"),
    unit("slugify_title", "return x.lower().replace(' ', '-')"),
]


def test_tokenize_splits_snake_and_camel():
    assert tokenize("parseHTTPResponse_v2") == ["parsehttpresponse_v2", "parse", "http", "response", "v", "2"]
    assert tokenize("parseHTTPResponse_v2", split_identifiers=False) == ["parsehttpresponse_v2"]


def test_doc_text_docstring_flag():
    assert "Check an email" not in doc_text(UNITS[0])
    assert "Check an email" in doc_text(UNITS[0], include_docstring=True)


def test_bm25_finds_function_via_identifier_splitting():
    top, _ = BM25Retriever(UNITS).search("validate email", k=1)[0]
    assert top.name == "isValidEmail"


def test_identifier_splitting_ablation_changes_result():
    # Without splitting, "email" never matches the single token "isvalidemail".
    scores = [s for _, s in BM25Retriever(UNITS, split_identifiers=False).search("email", k=3)]
    assert all(s == 0 for s in scores)


def test_search_returns_k_sorted_and_deterministic():
    r = BM25Retriever(UNITS)
    hits = r.search("parse http response", k=2)
    assert len(hits) == 2 and hits[0][0].name == "parse_http_response"
    assert hits[0][1] >= hits[1][1]
    assert hits == r.search("parse http response", k=2)


def test_dense_bge_small_and_cache(tmp_path):
    from codeecho.retrieval.dense import DenseRetriever  # downloads BAAI/bge-small-en-v1.5 on first run

    r = DenseRetriever(UNITS, cache_dir=tmp_path)
    assert r.search("validate an email address", k=1)[0][0].name == "isValidEmail"
    assert list(tmp_path.glob("*.npz"))  # cache written
    again = DenseRetriever(UNITS, cache_dir=tmp_path)
    assert (again._matrix == r._matrix).all()  # same vectors when served from cache


class FixedRetriever:
    """Stub retriever returning a fixed ranking, to test fusion exactly."""

    def __init__(self, ranking):
        self.ranking = ranking

    def search(self, query, k):
        return [(u, 1.0) for u in self.ranking[:k]]


def test_rrf_fuses_rankings():
    from codeecho.retrieval.hybrid import RRFRetriever

    a, b, c = UNITS
    fused = RRFRetriever([FixedRetriever([a, b, c]), FixedRetriever([b, c, a])], k_rrf=60).search("q", k=3)
    # b: 1/62 + 1/61 beats a: 1/61 + 1/63 beats c: 1/63 + 1/62
    assert [u.name for u, _ in fused] == [b.name, a.name, c.name]
    assert abs(fused[0][1] - (1 / 62 + 1 / 61)) < 1e-12


def test_rrf_counts_documents_missing_from_one_list():
    from codeecho.retrieval.hybrid import RRFRetriever

    a, b, _ = UNITS
    fused = RRFRetriever([FixedRetriever([a]), FixedRetriever([b, a])]).search("q", k=2)
    assert [u.name for u, _ in fused] == [a.name, b.name]


def test_cross_encoder_reranks_candidates():
    from codeecho.retrieval.rerank import CrossEncoderReranker  # downloads the MiniLM cross-encoder

    a, b, c = UNITS
    r = CrossEncoderReranker(FixedRetriever([c, b, a]), top_n=3)
    hits = r.search("check whether a string is a valid email address", k=3)
    assert hits[0][0].name == "isValidEmail" and len(hits) == 3
    assert hits[0][1] >= hits[1][1] >= hits[2][1]
