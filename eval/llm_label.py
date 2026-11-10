"""Non-interactive labelling for LLM-drafted relevance judgments (docs/DECISIONS.md D25).

Same pooling and record format as eval/label.py, in two steps so the queries are fixed
before any candidates are seen:

  # 1. queries.json is a JSON list of query strings, written before looking at any pool
  python -m eval.llm_label pool --repo 567-labs/instructor --queries q.json --out pools.json
  # 2. judgments.json: [{"query": ..., "relevant": ["file_path:start_line", ...], "note": ...}]
  #    relevant may name functions outside the pool (the "+name" case); [] means unanswerable.
  python -m eval.llm_label save --repo 567-labs/instructor --pools pools.json \
      --judgments judgments.json --annotator claude-opus-5-5
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from codeecho.indexer import index_repo
from eval.label import QUERIES_FILE, blind_pool, ref, systems
from eval.repos import checkout, load_repos


def pool(repo: str, queries: list[str], depth: int) -> list[dict]:
    """Blind pool for each query, with full source so a judge can read every candidate."""
    retrievers = systems(index_repo(checkout(repo)).functions)
    return [{"query": q, "depth": depth, "candidates": [
        {**ref(u), "signature": u.signature, "source": u.source}
        for u in blind_pool(q, retrievers, depth)]} for q in queries]


def save(repo: str, pools: list[dict], judgments: list[dict], annotator: str) -> int:
    """Append one record per judged query to data/queries.json; returns how many were added."""
    commit = load_repos()[repo]["commit"]
    units = {f"{u.file_path}:{u.start_line}": u for u in index_repo(checkout(repo)).functions}
    by_query = {p["query"]: p for p in pools}
    records = json.loads(QUERIES_FILE.read_text()) if QUERIES_FILE.exists() else []
    n_repo = sum(r["repo"] == repo for r in records)
    for j in judgments:
        p = by_query[j["query"]]                             # KeyError = judged a query never pooled
        missing = [k for k in j["relevant"] if k not in units]
        if missing:
            raise ValueError(f"{j['query']!r}: not indexed functions: {missing}")
        in_pool = {f"{c['file_path']}:{c['start_line']}" for c in p["candidates"]}
        n_repo += 1
        records.append({
            "id": f"{repo.split('/')[1]}-{n_repo:03d}",
            "repo": repo,
            "commit": commit,
            "query": j["query"],
            "relevant": [ref(units[k]) for k in dict.fromkeys(j["relevant"])],
            "answerable": bool(j["relevant"]),
            "pool_size": len(p["candidates"]),
            "pool_depth": p["depth"],
            "added_outside_pool": sum(k not in in_pool for k in dict.fromkeys(j["relevant"])),
            "annotator": annotator,
            "notes": j.get("note", ""),
            "created": dt.date.today().isoformat(),
        })
    QUERIES_FILE.write_text(json.dumps(records, indent=2) + "\n")
    return len(judgments)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pool")
    p.add_argument("--repo", required=True, choices=sorted(load_repos()))
    p.add_argument("--queries", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--depth", type=int, default=10)
    s = sub.add_parser("save")
    s.add_argument("--repo", required=True, choices=sorted(load_repos()))
    s.add_argument("--pools", required=True, type=Path)
    s.add_argument("--judgments", required=True, type=Path)
    s.add_argument("--annotator", required=True)
    args = ap.parse_args()

    if args.cmd == "pool":
        out = pool(args.repo, json.loads(args.queries.read_text()), args.depth)
        args.out.write_text(json.dumps(out, indent=1) + "\n")
        print(f"Wrote {len(out)} pools ({sum(len(o['candidates']) for o in out)} candidates) to {args.out}")
    else:
        n = save(args.repo, json.loads(args.pools.read_text()), json.loads(args.judgments.read_text()),
                 args.annotator)
        print(f"Saved {n} queries to {QUERIES_FILE}")


if __name__ == "__main__":
    main()
