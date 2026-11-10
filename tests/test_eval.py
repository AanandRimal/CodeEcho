"""Tests for evaluation helpers."""

from eval.label import blind_pool
from tests.test_retrieval import UNITS, FixedRetriever


def test_blind_pool_is_union_and_independent_of_system_ranking():
    a, b, c = UNITS
    p1 = blind_pool("q", {"x": FixedRetriever([a, b]), "y": FixedRetriever([c])}, depth=2)
    p2 = blind_pool("q", {"x": FixedRetriever([b, a]), "y": FixedRetriever([c])}, depth=2)
    assert set(p1) == {a, b, c}
    assert p1 == p2  # order depends only on query + location, not on who ranked what


def test_llm_label_save_records_and_rejects_unknown_functions(tmp_path, monkeypatch):
    import json
    import pytest
    from codeecho.indexer import IndexResult
    from eval import llm_label

    from dataclasses import replace
    a, b, c = units = [replace(u, start_line=i) for i, u in enumerate(UNITS, 1)]  # distinct locations
    monkeypatch.setattr(llm_label, "QUERIES_FILE", tmp_path / "q.json")
    monkeypatch.setattr(llm_label, "load_repos", lambda: {"o/r": {"commit": "abc"}})
    monkeypatch.setattr(llm_label, "checkout", lambda repo: tmp_path)
    monkeypatch.setattr(llm_label, "index_repo", lambda root: IndexResult(functions=units))
    key = lambda u: f"{u.file_path}:{u.start_line}"
    pools = [{"query": "q1", "depth": 10, "candidates": [llm_label.ref(a)]},
             {"query": "q2", "depth": 10, "candidates": [llm_label.ref(b)]}]
    judged = [{"query": "q1", "relevant": [key(a), key(c)], "note": "n"}, {"query": "q2", "relevant": []}]

    assert llm_label.save("o/r", pools, judged, "llm") == 2
    r1, r2 = json.loads((tmp_path / "q.json").read_text())
    assert (r1["id"], r1["answerable"], r1["added_outside_pool"], r1["annotator"]) == ("r-001", True, 1, "llm")
    assert (r2["id"], r2["answerable"], r2["relevant"]) == ("r-002", False, [])
    with pytest.raises(ValueError):
        llm_label.save("o/r", pools, [{"query": "q1", "relevant": ["nope.py:1"]}], "llm")
