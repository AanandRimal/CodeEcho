"""RQ1: how well does DevTrust find the right function? Writes results/retrieval.json.

Usage:  .venv/bin/python -m eval.retrieval_eval

Runs every search setting (eval.label.systems) over the answerable queries in data/queries.json.
Queries are the LLM-drafted set from docs/DECISIONS.md D25; there is no dev/test split because
nothing is tuned on these queries (all settings are fixed in advance). Unanswerable queries are
counted but not scored.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import time
from collections import defaultdict
from pathlib import Path

from devtrust.indexer import index_repo
from devtrust.retrieval.dense import REVISION as DENSE_REVISION
from devtrust.retrieval.rerank import REVISION as RERANK_REVISION
from eval.label import QUERIES_FILE, systems
from eval.metrics import bootstrap_ci, ndcg_at_k, recall_at_k, reciprocal_rank
from eval.repos import checkout, load_repos

SEED = 0
OUT = Path("results/retrieval.json")
METRICS = {
    "mrr": lambda r, rel: reciprocal_rank(r, rel),
    "ndcg@10": lambda r, rel: ndcg_at_k(r, rel, 10),
    "recall@1": lambda r, rel: recall_at_k(r, rel, 1),
    "recall@5": lambda r, rel: recall_at_k(r, rel, 5),
    "recall@10": lambda r, rel: recall_at_k(r, rel, 10),
}


def _git(*args: str) -> str:
    out = subprocess.run(["git", *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def _summarise(rows: list[dict], system: str) -> dict:
    """Mean and 95% bootstrap CI of every metric for one system over the given query rows."""
    return {m: dict(zip(("mean", "ci_low", "ci_high"), bootstrap_ci([r[system][m] for r in rows], SEED)))
            for m in METRICS}


def main() -> None:
    records = json.loads(QUERIES_FILE.read_text())
    kinds = {t["query"]: t["kind"] for p in Path("data/llm_labelling").glob("*/targets.json")
             for t in json.loads(p.read_text())}
    rows, build_s, latency, params = [], defaultdict(dict), defaultdict(list), {}
    for repo in load_repos():
        recs = [r for r in records if r["repo"] == repo]
        units = index_repo(checkout(repo)).functions
        t0 = time.perf_counter()
        retrievers = systems(units)
        build_s[repo] = round(time.perf_counter() - t0, 1)  # embeddings come from the on-disk cache
        for name, r in retrievers.items():
            m = getattr(r, "model", None)
            if m is not None and name not in params:
                params[name] = sum(p.numel() for p in (m if hasattr(m, "parameters") else m.model).parameters())
        for rec in (r for r in recs if r["answerable"]):
            relevant = {(x["file_path"], x["start_line"]) for x in rec["relevant"]}
            row = {"id": rec["id"], "repo": repo, "query": rec["query"], "kind": kinds.get(rec["query"], "?"),
                   "n_relevant": len(relevant), "relevant": [x["qualname"] for x in rec["relevant"]]}
            for name, r in retrievers.items():
                t = time.perf_counter()
                hits = r.search(rec["query"], 10)
                latency[name].append(time.perf_counter() - t)
                ranked = [(u.file_path, u.start_line) for u, _ in hits]
                row[name] = {m: f(ranked, relevant) for m, f in METRICS.items()}
            rows.append(row)
        print(f"{repo}: {len(recs)} queries, {sum(r['repo'] == repo for r in rows)} scored", flush=True)

    names = list(retrievers)  # same settings for every repo
    out = {
        "meta": {
            "date": dt.date.today().isoformat(),
            "git_commit": _git("rev-parse", "HEAD") or "none (repo has no commits yet)",
            "git_dirty": bool(_git("status", "--porcelain", "--", ".", ":!results")),  # results/ is our own output
            "seed": SEED,
            "dataset": "data/queries.json (LLM-drafted labels, claude-opus-5-5; see D25/D26)",
            "repos": {k: v["commit"] for k, v in load_repos().items()},
            "n_queries_total": len(records),
            "n_queries_scored": len(rows),
            "n_unanswerable_not_scored": sum(not r["answerable"] for r in records),
            "pool_depth": 10,
            "k_for_metrics": 10,
            "dense_revisions": DENSE_REVISION,
            "reranker_revision": RERANK_REVISION,
            "bootstrap": "95% percentile CI, 10000 resamples over queries",
            "model_params": params,
            "index_build_seconds_warm_cache": build_s,
            "mean_query_latency_ms": {n: round(1000 * sum(v) / len(v), 1) for n, v in latency.items()},
            "hardware": "CPU only",
        },
        "overall": {n: _summarise(rows, n) for n in names},
        "by_kind": {k: {n: _summarise(sub, n) for n in names}
                    for k in ("easy", "hard") if (sub := [r for r in rows if r["kind"] == k])},
        "by_repo": {rp: {n: _summarise(sub, n) for n in names}
                    for rp in load_repos() if (sub := [r for r in rows if r["repo"] == rp])},
        "all_systems_miss_at_10": [{k: r[k] for k in ("id", "query", "relevant")} for r in rows
                                   if all(r[n]["recall@10"] == 0 for n in names)],
        "per_query": rows,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
