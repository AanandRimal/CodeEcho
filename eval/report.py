"""Generate the README results tables from results/*.json (never typed by hand).

Usage:  .venv/bin/python -m eval.report
Replaces the text between `<!-- BEGIN:name -->` and `<!-- END:name -->` markers in README.md. A table whose
results file does not exist yet is replaced by a "not run yet" note, so the README never shows invented numbers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

README = Path("README.md")
RESULTS = Path("results")


def _f(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}"


def _ci(m: dict) -> str:
    return f"{_f(m['mean'])} [{_f(m['ci_low'])}, {_f(m['ci_high'])}]"


def _table(header: list[str], rows: list[list[str]]) -> str:
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
                     + ["| " + " | ".join(r) + " |" for r in rows])


def _meta(m: dict) -> str:
    return (f"_Generated from `results/` on {m['date']}, commit `{m['git_commit'][:7]}`"
            f"{' (working tree had uncommitted changes)' if m.get('git_dirty') else ''}._")


def retrieval_tables() -> str:
    d = json.loads((RESULTS / "retrieval.json").read_text())
    m, names = d["meta"], {"bm25": "BM25", "bm25_nosplit": "BM25, no identifier splitting", "bge_small": "bge-small-en-v1.5",
                           "coderankembed": "CodeRankEmbed", "rrf": "RRF (BM25 + CodeRankEmbed)",
                           "rrf_rerank": "RRF + cross-encoder rerank (top 50)"}
    rows = [[names[k], _ci(v["mrr"]), _ci(v["ndcg@10"]), _f(v["recall@1"]["mean"]), _f(v["recall@5"]["mean"]),
             _ci(v["recall@10"]), f"{m['mean_query_latency_ms'][k]:.0f}"] for k, v in d["overall"].items()]
    main = _table(["Search setting", "MRR [95% CI]", "NDCG@10 [95% CI]", "Recall@1", "Recall@5", "Recall@10 [95% CI]",
                   "ms/query (CPU)"], rows)
    kind_rows = [[names[k], _f(d["by_kind"]["easy"][k]["mrr"]["mean"]), _f(d["by_kind"]["hard"][k]["mrr"]["mean"])]
                 for k in d["overall"]]
    kinds = _table(["Search setting", "MRR, easy queries", "MRR, hard queries"], kind_rows)
    return (f"{main}\n\n{kinds}\n\n{m['n_queries_scored']} answerable queries over 3 repos "
            f"({m['n_unanswerable_not_scored']} unanswerable queries not scored). Labels are AI-drafted. "
            f"{(n := len(d['all_systems_miss_at_10']))} {'query was' if n == 1 else 'queries were'} missed by every "
            f"setting at rank 10.\n\n{_meta(m)}")


def duplication_tables() -> str:
    d = json.loads((RESULTS / "duplication.json").read_text())
    m, T = d["meta"], d["test"]
    names = {"embedding_only": "Embedding-only (max cosine)", "retrieval_plus_structural": "Retrieval + structural (F1 threshold)",
             "structural_at_tool_default": "Retrieval + structural (tool default 0.9)",
             "jscpd_token": "jscpd, token mode", "jscpd_token_small": "jscpd, token mode, min 20 tokens",
             "jscpd_semantic": "jscpd --semantic", "jscpd_semantic_small": "jscpd --semantic, min 20 tokens"}
    names = {k: v for k, v in names.items() if k in T}
    overall = _table(["Method", "Precision", "Recall", "F1", "False-positive rate"],
                     [[v, *(_f(T[k]["overall"][x]) for x in ("precision", "recall", "f1", "fpr"))] for k, v in names.items()])
    types = ("type1", "type2", "type3", "type4")
    rec = _table(["Method (recall)", *types], [[v, *(f"{_f(T[k][t]['recall'])} [{_f(T[k][t]['recall_ci'][0])}, "
                                                    f"{_f(T[k][t]['recall_ci'][1])}]" for t in types)] for k, v in names.items()])
    neg = ("unrelated", "sibling", "client_endpoint", "one_edit")
    n = {k: T["embedding_only"]["fpr_by_negative_kind"][k]["n"] for k in neg}
    fpr = _table(["Method (false-positive rate)", *(f"{k} (n={n[k]})" for k in neg)],
                 [[v, *(_f(T[k]["fpr_by_negative_kind"][x]["fpr"]) for x in neg)] for k, v in names.items()])
    th = m["thresholds_chosen_on_dev"]
    return (f"{overall}\n\n{rec}\n\n{fpr}\n\nTest split only ({m['n_test']} cases). Thresholds chosen on the dev split "
            f"({m['n_dev']} cases): embedding cosine {_f(th['embedding_only_top1_cosine'], 3)}, structural "
            f"{_f(th['structural'], 3)}. Precision is over each row's positives against all negatives.\n\n{_meta(m)}")


def _agents_section(d: dict, m: dict) -> str:
    g, t = d["groups"], d["tests_vs_human"]
    order = ["human", *d["groups_analysed"], "ALL_ANALYSED_AGENTS"]
    label = lambda k: {"ALL_ANALYSED_AGENTS": "All analysed agents pooled", "human": "Human"}.get(k, k)
    rows = [[label(k), str(g[k]["n_prs"]), str(g[k]["n_eligible_prs"]), str(g[k]["n_added_reviewed"]), str(g[k]["n_likely_duplicate"]),
             f"{_f(g[k]['share_prs_with_likely_duplicate'])} [{_f(g[k]['share_ci'][0])}, {_f(g[k]['share_ci'][1])}]",
             f"{_f(g[k]['likely_duplicates_per_added_function'], 3)} [{_f(g[k]['rate_ci'][0], 3)}, {_f(g[k]['rate_ci'][1], 3)}]"]
            for k in order if g[k].get("n_eligible_prs")]
    main = _table(["Group", "PRs", "PRs with new functions", "New functions reviewed", "Flagged", "Share of PRs with a flagged function [95% CI]",
                   "Flagged per new function [95% CI]"], rows)
    pf = lambda x: "<0.001" if x < 0.001 else f"{x:.3f}"
    holm = lambda v, k: pf(v[k]) if k in v else "n/a"
    trows = [[label(k), f"{v['diff_share']:+.3f}", pf(v["p_share"]), holm(v, "p_share_holm_over_agents"),
              f"{v['diff_rate']:+.4f}", pf(v["p_rate"]), holm(v, "p_rate_holm_over_agents")] for k, v in t.items()]
    tests = _table(["Agent vs human", "Diff in share", "p", "p (Holm)", "Diff in rate", "p", "p (Holm)"], trows)
    return f"{main}\n\n{tests}"


def agents_tables() -> str:
    d = json.loads((RESULTS / "agents.json").read_text())
    m = d["meta"]
    not_an = ", ".join(m["groups_not_analysed"]) or "none"
    a = d.get("audit")
    audit = ""
    if a and a.get("n_judged"):
        c = a["verdict_counts"]
        audit = (f"**Manual audit** ({a['n_judged']} random flagged findings out of {a['n_findings_total']}, judged by an AI, not blind, "
                 f"no human check): {c.get('duplicate', 0)} real duplicates, {c.get('moved_refactor', 0)} where the PR itself removed or moved "
                 f"the matched function, {c.get('similar_not_duplicate', 0)} similar in shape but not duplicates. Precision "
                 f"{_f(a['precision'])} [{_f(a['precision_ci'][0])}, {_f(a['precision_ci'][1])}] overall, and "
                 f"{_f(a['precision_among_match_survives'])} among the {a['n_match_survives']} findings whose matched function still exists "
                 f"at the PR head.")
    return (f"**Primary analysis** (the design fixed before the run, `docs/DECISIONS.md` D32): every flagged function counts.\n\n"
            f"{_agents_section(d['primary'], m)}\n\n"
            f"**Sensitivity analysis** (added after reading the audit sample, D33): findings whose matched function no longer exists at the PR's "
            f"head are not counted, because the PR moved or renamed that function (a move combined with edits slips past the exact-body "
            f"move filter).\n\n{_agents_section(d['sensitivity_match_survives'], m)}\n\n"
            f"Groups with too few PRs with new functions to analyse (under {m['min_eligible_prs_to_analyse']}): {not_an}. Permutation tests shuffle "
            f"agent/human labels within each repo; \"Holm\" adjusts across the agents tested; the pooled row is not part of that family. "
            f"\"Flagged\" means a structural score of at least {m['detector']['likely_duplicate_structural_threshold']} against a retrieved function, "
            f"counted for functions the PR adds (at least {m['detector']['min_ast_nodes']} AST nodes).\n\n{audit}\n\n{_meta(m)}")


def inject(text: str, name: str, body: str) -> str:
    """Replace the content between the BEGIN/END markers for `name`."""
    pat = re.compile(rf"(<!-- BEGIN:{name} -->\n).*?(\n<!-- END:{name} -->)", re.S)
    if not pat.search(text):
        raise ValueError(f"marker {name} not found")
    return pat.sub(lambda mt: mt.group(1) + body + mt.group(2), text)


def main() -> None:
    text = README.read_text()
    for name, fn, file in (("retrieval", retrieval_tables, "retrieval.json"), ("duplication", duplication_tables, "duplication.json"),
                           ("agents", agents_tables, "agents.json")):
        body = fn() if (RESULTS / file).exists() else f"_Not run yet: `results/{file}` does not exist._"
        text = inject(text, name, body)
    README.write_text(text)
    print("README tables updated")


if __name__ == "__main__":
    main()
