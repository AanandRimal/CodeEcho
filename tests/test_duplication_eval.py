"""Scoring logic of eval/duplication_eval.py on tiny hand-made cases."""

from eval.duplication_eval import choose_threshold, prf

CASES = [
    {"kind": "type2", "s": 0.9}, {"kind": "type2", "s": 0.8}, {"kind": "type4", "s": 0.5},
    {"kind": "sibling", "s": 0.7}, {"kind": "unrelated", "s": 0.1}, {"kind": "one_edit", "s": 0.95},
]


def test_prf_counts_per_kind_and_overall():
    o = prf(CASES, lambda c: c["s"] >= 0.75)          # flags: t2, t2, one_edit
    assert (o["tp"], o["fp"], o["n_pos"], o["n_neg"]) == (2, 1, 3, 3)
    assert o["precision"] == 2 / 3 and o["recall"] == 2 / 3 and abs(o["fpr"] - 1 / 3) < 1e-9
    t4 = prf(CASES, lambda c: c["s"] >= 0.75, "type4")
    assert (t4["n_pos"], t4["tp"], t4["recall"]) == (1, 0, 0.0)


def test_choose_threshold_maximises_f1_and_prefers_higher_on_ties():
    cases = [{"kind": "type1", "s": 0.9}, {"kind": "type1", "s": 0.8}, {"kind": "unrelated", "s": 0.2},
             {"kind": "unrelated", "s": 0.1}]
    assert choose_threshold(cases, "s") == 0.8          # 0.8 separates the classes cleanly; 0.1/0.2 would flag negatives


def test_assign_splits_is_stratified_and_keeps_groups_together():
    from eval.duplication_eval import assign_splits
    cases = [{"kind": k, "group": f"{g}"} for g in range(6) for k in ("type1", "type2", "type3")]
    cases += [{"kind": "sibling", "group": f"s{i}"} for i in range(4)]
    assign_splits(cases)
    assert all(len({c["split"] for c in cases if c["group"] == g}) == 1 for g in {c["group"] for c in cases})
    sib = [c["split"] for c in cases if c["kind"] == "sibling"]
    assert sib.count("dev") == sib.count("test") == 2
    orig = {c["group"]: c["split"] for c in cases if c["kind"] == "type1"}
    assert list(orig.values()).count("dev") == 3
