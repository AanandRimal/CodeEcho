"""RQ3 statistics on small synthetic PR records."""

from eval import agent_eval as ae


def rec(repo, group, dups, n):
    added = [{"category": "likely_duplicate" if i < dups else "insufficient_evidence"} for i in range(n)]
    return {"repo": repo, "number": 1, "group": group, "added_reviewed": added}


def test_holm_matches_hand_computation():
    # sorted p: .01, .02, .04 -> x3, x2, x1 = .03, .04, .04 (monotone)
    assert ae.holm([0.04, 0.01, 0.02]) == [0.04, 0.03, 0.04]
    assert ae.holm([0.5]) == [0.5]


def test_summarise_counts_and_excludes_errors_and_empty_prs():
    recs = [rec("r", "x", 1, 4), rec("r", "x", 0, 2), rec("r", "x", 0, 0), {"repo": "r", "group": "x", "error": "boom"}]
    s = ae.summarise(recs)
    assert (s["n_prs"], s["n_errors"], s["n_eligible_prs"]) == (4, 1, 2)       # empty PR and error not eligible
    assert (s["n_added_reviewed"], s["n_likely_duplicate"]) == (6, 1)
    assert s["share_prs_with_likely_duplicate"] == 0.5 and abs(s["likely_duplicates_per_added_function"] - 1 / 6) < 1e-12
    assert s["share_ci"][0] <= 0.5 <= s["share_ci"][1]


def test_perm_test_detects_a_clear_difference_and_not_a_null(monkeypatch):
    monkeypatch.setattr(ae, "N_PERM", 400)
    agent = [rec("r", "A", 1, 2) for _ in range(30)]
    human = [rec("r", "human", 0, 2) for _ in range(30)]
    clear = ae.perm_test(agent, human)
    assert clear["diff_share"] == 1.0 and clear["p_share"] < 0.01
    mixed_a = [rec("r", "A", i % 2, 2) for i in range(30)]
    mixed_h = [rec("r", "human", i % 2, 2) for i in range(30)]
    null = ae.perm_test(mixed_a, mixed_h)
    assert null["diff_share"] == 0.0 and null["p_share"] > 0.5
