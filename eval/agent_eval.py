"""RQ3: do AI-agent PRs add functions that duplicate existing code more often than human PRs?

Usage:
  .venv/bin/python -m eval.agent_eval run        # review every PR in data/agent_prs.json (resumable, slow)
  .venv/bin/python -m eval.agent_eval audit-sample  # draw the random sample of findings to audit by hand
  .venv/bin/python -m eval.agent_eval analyze    # statistics -> results/agents.json

`run` reviews each PR with the same detector as the tool: base state = merge-base(base, head), search with
CodeRankEmbed, structural check at the tool's untuned default (best structural >= 0.9 = likely_duplicate).
Per-PR outputs go to .cache/agent_runs/ (git-ignored). Only functions ADDED by the PR are counted (a modified
function can already have resembled another one before the PR). See docs/DECISIONS.md D32.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from devtrust.duplication.review import HI, LIKELY, MIN_NODES, review
from eval.agent_data import FULL, OUT
from eval.metrics import bootstrap_ci

RUNS = Path(".cache/agent_runs")


def repo_dir(repo: str) -> Path:
    return FULL / (repo.replace("/", "__") + ".git")


def review_pr(pr: dict) -> dict:
    """Review one PR; returns a JSON-serialisable record (with an "error" key if git could not do it)."""
    rd, t0 = repo_dir(pr["repo"]), time.perf_counter()
    try:
        git = lambda *a: subprocess.run(["git", "-C", str(rd), *a], check=True, capture_output=True, text=True).stdout.strip()
        mb = git("merge-base", pr["base_sha"], pr["head_sha"])
        report = review(rd, mb, pr["head_sha"], top_k=5)
    except subprocess.CalledProcessError as e:
        return {"error": f"git failed: {(e.stderr or '')[:200]}", "seconds": round(time.perf_counter() - t0, 1)}
    added = []
    for f in report.findings:
        if f.status != "added":
            continue
        best = f.matches[0] if f.matches else None
        rec = {"qualname": f.function.qualname, "file": f.function.file_path, "start_line": f.function.start_line,
               "category": f.category, "confidence": f.confidence,
               "best_structural": best.structural_score if best else None,
               "best_retrieval": best.retrieval_score if best else None,
               "match": f"{best.unit.file_path}:{best.unit.start_line} {best.unit.qualname}" if best else None}
        if f.category == LIKELY:                    # keep sources for the manual audit
            rec["new_source"], rec["match_source"] = f.function.source[:4000], best.unit.source[:4000]
        added.append(rec)
    return {"merge_base": mb, "n_changed": report.n_changed, "skipped_small": report.skipped_small,
            "moved_or_renamed": report.moved_or_renamed, "added_reviewed": added,
            "seconds": round(time.perf_counter() - t0, 1)}


def run() -> None:
    prs = json.loads(OUT.read_text())["prs"]
    RUNS.mkdir(parents=True, exist_ok=True)
    for i, pr in enumerate(prs, 1):
        path = RUNS / f"{pr['repo'].replace('/', '__')}__{pr['number']}.json"
        if path.exists():
            continue
        rec = {**{k: pr[k] for k in ("repo", "number", "group", "merged_at")}, **review_pr(pr)}
        path.write_text(json.dumps(rec))
        n_dup = sum(a["category"] == LIKELY for a in rec.get("added_reviewed", []))
        print(f"[{i}/{len(prs)}] {pr['repo']}#{pr['number']} {pr['group']}: "
              f"{len(rec.get('added_reviewed', []))} added reviewed, {n_dup} likely_duplicate, "
              f"{rec.get('seconds')}s{' ERROR ' + rec['error'] if 'error' in rec else ''}", flush=True)


SEED, N_PERM, N_BOOT, MIN_PRS, N_AUDIT = 0, 10_000, 10_000, 10, 40
AUDIT_SAMPLE, AUDIT_LABELS, RESULTS = Path(".cache/agent_audit_sample.json"), Path("data/agent_audit.json"), Path("results/agents.json")


def load_runs() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(RUNS.glob("*.json"))]


def pr_stats(rec: dict) -> tuple[int, int]:
    """(likely_duplicate findings, added functions reviewed) for one PR record."""
    added = rec.get("added_reviewed", [])
    return sum(a["category"] == LIKELY for a in added), len(added)


def _ci(values: np.ndarray, rng: np.random.Generator) -> list[float]:
    idx = rng.integers(0, len(values), (N_BOOT, len(values)))
    m = values[idx].mean(axis=1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def summarise(recs: list[dict], seed: int = SEED) -> dict:
    """Per-group numbers; PR-level share and per-function rate, both with PR-resampling 95% CIs."""
    rng = np.random.default_rng(seed)
    el = [r for r in recs if "error" not in r and pr_stats(r)[1] > 0]
    dup = np.array([pr_stats(r)[0] for r in el], dtype=float)
    n = np.array([pr_stats(r)[1] for r in el], dtype=float)
    out = {"n_prs": len(recs), "n_errors": sum("error" in r for r in recs), "n_eligible_prs": len(el),
           "n_added_reviewed": int(n.sum()) if len(el) else 0, "n_likely_duplicate": int(dup.sum()) if len(el) else 0}
    if el:
        has = (dup > 0).astype(float)
        idx = rng.integers(0, len(el), (N_BOOT, len(el)))
        rate = dup[idx].sum(axis=1) / n[idx].sum(axis=1)
        out |= {"share_prs_with_likely_duplicate": float(has.mean()), "share_ci": _ci(has, rng),
                "likely_duplicates_per_added_function": float(dup.sum() / n.sum()),
                "rate_ci": [float(np.percentile(rate, 2.5)), float(np.percentile(rate, 97.5))],
                "mean_added_reviewed_per_pr": float(n.mean())}
    return out


def perm_test(agent: list[dict], human: list[dict], seed: int = SEED) -> dict:
    """Two-sided permutation tests of agent vs human, labels shuffled within repo (so repo mix is held fixed).

    Statistics: difference in share of PRs with a likely_duplicate, and difference in findings per added function.
    """
    rng = np.random.default_rng(seed)
    rows = [(r["repo"], r["group"] != "human", *pr_stats(r)) for r in agent + human
            if "error" not in r and pr_stats(r)[1] > 0]
    repo = np.array([x[0] for x in rows]); is_a = np.array([x[1] for x in rows])
    dup = np.array([x[2] for x in rows], dtype=float); n = np.array([x[3] for x in rows], dtype=float)
    def stat(lab):
        a, h = lab, ~lab
        return ((dup[a] > 0).mean() - (dup[h] > 0).mean(), dup[a].sum() / n[a].sum() - dup[h].sum() / n[h].sum())
    obs = stat(is_a)
    ge = np.zeros(2)
    for _ in range(N_PERM):
        lab = is_a.copy()
        for r in set(repo):
            m = np.where(repo == r)[0]
            lab[m] = rng.permutation(lab[m])
        ge += np.abs(stat(lab)) >= np.abs(obs) - 1e-12
    p = (ge + 1) / (N_PERM + 1)
    return {"diff_share": float(obs[0]), "p_share": float(p[0]), "diff_rate": float(obs[1]), "p_rate": float(p[1])}


def holm(ps: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, in the input order."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def audit_sample() -> None:
    """Seeded random sample of likely_duplicate findings (all groups pooled) for manual judging."""
    findings = [{"repo": r["repo"], "number": r["number"], "group": r["group"], **a}
                for r in load_runs() for a in r.get("added_reviewed", []) if a["category"] == LIKELY]
    sample = random.Random(SEED).sample(findings, min(N_AUDIT, len(findings)))
    AUDIT_SAMPLE.write_text(json.dumps({"n_findings_total": len(findings), "sample": sample}, indent=1))
    print(f"{len(findings)} likely_duplicate findings; sampled {len(sample)} -> {AUDIT_SAMPLE}")


def analyze() -> None:
    recs = load_runs()
    groups = defaultdict(list)
    for r in recs:
        groups[r["group"]].append(r)
    table = {g: summarise(rs) for g, rs in sorted(groups.items())}
    analysed = [g for g in sorted(groups) if g != "human" and table[g]["n_eligible_prs"] >= MIN_PRS]
    human = groups["human"]
    agents_all = [r for g in analysed for r in groups[g]]
    table["ALL_ANALYSED_AGENTS"] = summarise(agents_all)
    tests = {g: perm_test(groups[g], human) for g in analysed} | {"ALL_ANALYSED_AGENTS": perm_test(agents_all, human)}
    keys = [g for g in tests if g != "ALL_ANALYSED_AGENTS"]
    for kind in ("p_share", "p_rate"):
        for g, adj in zip(keys, holm([tests[g][kind] for g in keys])):
            tests[g][kind + "_holm_over_agents"] = adj
    buckets = {"1": (1, 1), "2-3": (2, 3), "4-9": (4, 9), "10+": (10, 10**9)}
    by_size = {}
    for name, (lo, hi) in buckets.items():
        by_size[name] = {lab: summarise([r for r in rs if "error" not in r and lo <= pr_stats(r)[1] <= hi])
                         for lab, rs in (("agents", agents_all), ("human", human))}
    by_repo = {repo: {lab: summarise([r for r in rs if r["repo"] == repo]) for lab, rs in
                      (("agents", agents_all), ("human", human))} for repo in sorted({r["repo"] for r in recs})}
    audit = None
    if AUDIT_LABELS.exists():
        lab = json.loads(AUDIT_LABELS.read_text())
        j = lab["judgments"]
        k = sum(x["verdict"] == "duplicate" for x in j)
        audit = {"n_judged": len(j), "n_judged_duplicate": k, "precision": k / len(j) if j else None,
                 "annotator": lab.get("annotator"), "n_findings_total": lab.get("n_findings_total")}
        if j:
            audit["precision_ci"] = bootstrap_ci([float(x["verdict"] == "duplicate") for x in j], SEED)[1:]
    git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
    RESULTS.parent.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps({
        "meta": {"date": dt.date.today().isoformat(), "git_commit": git("rev-parse", "HEAD"),
                 "git_dirty": bool(git("status", "--porcelain", "--", ".", ":!results")), "seed": SEED,
                 "n_permutations": N_PERM, "n_bootstrap": N_BOOT, "min_eligible_prs_to_analyse": MIN_PRS,
                 "detector": {"retrieval": "nomic-ai/CodeRankEmbed (top 5)", "likely_duplicate_structural_threshold": HI,
                              "min_ast_nodes": MIN_NODES, "counted": "functions added by the PR only"},
                 "pr_table": json.loads(OUT.read_text())["meta"], "groups_analysed": analysed,
                 "groups_not_analysed": [g for g in sorted(groups) if g not in analysed and g != "human"]},
        "groups": table, "tests_vs_human": tests, "by_size_bucket": by_size, "by_repo": by_repo,
        "audit": audit}, indent=1) + "\n")
    print(f"Wrote {RESULTS}")


if __name__ == "__main__":
    {"run": run, "analyze": analyze, "audit-sample": audit_sample}[sys.argv[1] if len(sys.argv) > 1 else "run"]()
