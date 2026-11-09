"""Interactive labelling helper for the RQ1 benchmark: pooled, blind judging.

Usage:  .venv/bin/python -m eval.label --repo 567-labs/instructor --annotator "Your Name"

For each query you type, candidates from every evaluated search method are pooled and shown
in a shuffled order (hash of query + location), so you can't tell which method found what.
See data/ANNOTATION.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from devtrust.indexer import FunctionUnit, index_repo
from devtrust.retrieval import tokenize
from devtrust.retrieval.bm25 import BM25Retriever
from devtrust.retrieval.dense import DenseRetriever
from devtrust.retrieval.hybrid import RRFRetriever
from devtrust.retrieval.rerank import CrossEncoderReranker
from eval.repos import checkout, load_repos

QUERIES_FILE = Path("data/queries.json")


def systems(units: list[FunctionUnit]) -> dict:
    """Every search configuration evaluated in RQ1; the pool is the union of their top results."""
    bm25 = BM25Retriever(units)
    cre = DenseRetriever(units, model_name="nomic-ai/CodeRankEmbed")
    rrf = RRFRetriever([bm25, cre])
    return {
        "bm25": bm25,
        "bm25_nosplit": BM25Retriever(units, split_identifiers=False),
        "bge_small": DenseRetriever(units, model_name="BAAI/bge-small-en-v1.5"),
        "coderankembed": cre,
        "rrf": rrf,
        "rrf_rerank": CrossEncoderReranker(rrf, top_n=50),
    }


def blind_pool(query: str, retrievers: dict, depth: int) -> list[FunctionUnit]:
    """Union of each system's top-`depth` results, in an order unrelated to any ranking."""
    pool = {u for r in retrievers.values() for u, _ in r.search(query, depth)}
    key = lambda u: hashlib.sha256(f"{query}|{u.file_path}:{u.start_line}".encode()).hexdigest()
    return sorted(pool, key=key)


def show(i: int, u: FunctionUnit) -> None:
    print(f"\n[{i}] {u.qualname}   ({u.file_path}:{u.start_line})\n    {u.signature[:110]}")
    for line in u.body.splitlines()[:3]:
        print(f"      {line[:100]}")


def ref(u: FunctionUnit) -> dict:
    return {"qualname": u.qualname, "file_path": u.file_path, "start_line": u.start_line}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, choices=sorted(load_repos()))
    ap.add_argument("--annotator", required=True)
    ap.add_argument("--depth", type=int, default=10, help="top-k taken from each system into the pool")
    args = ap.parse_args()

    commit = load_repos()[args.repo]["commit"]
    units = index_repo(checkout(args.repo)).functions
    print(f"Indexed {len(units)} functions from {args.repo}@{commit[:7]}. Loading models...")
    retrievers = systems(units)
    records = json.loads(QUERIES_FILE.read_text()) if QUERIES_FILE.exists() else []
    n_repo = sum(r["repo"] == args.repo for r in records)

    while True:
        query = input(f"\n=== Query #{n_repo + 1} for {args.repo} (empty to quit): ").strip()
        if not query:
            break
        pool = blind_pool(query, retrievers, args.depth)
        for i, u in enumerate(pool, 1):
            show(i, u)
        relevant: list[FunctionUnit] = []
        print("\nEnter numbers of relevant candidates (e.g. '3 7'), '+name' to add one not listed,"
              " 'none' if nothing in the repo satisfies the need, or 'skip' to discard this query.")
        while True:
            ans = input("> ").strip()
            if ans == "skip":
                break
            if ans.startswith("+"):
                matches = [u for u in units if ans[1:].strip() in u.qualname]
                for i, u in enumerate(matches[:15], 1):
                    show(i, u)
                pick = input("number to add (empty for none): ").strip()
                if pick.isdigit() and 1 <= int(pick) <= len(matches[:15]):
                    relevant.append(matches[int(pick) - 1])
                continue
            if ans == "none" or all(t.isdigit() and 1 <= int(t) <= len(pool) for t in ans.split()) and ans:
                relevant += [pool[int(t) - 1] for t in ans.split() if t.isdigit()]
                break
            print("Didn't understand that; try again.")
        if ans == "skip":
            continue

        names = {t for u in relevant for t in tokenize(u.name)}
        overlap = sorted({t for t in tokenize(query) if t in names and len(t) > 3})
        if overlap:
            print(f"(note: query shares words with the answer's name: {overlap}; fine if natural, see guideline 2)")
        n_repo += 1
        records.append({
            "id": f"{args.repo.split('/')[1]}-{n_repo:03d}",
            "repo": args.repo,
            "commit": commit,
            "query": query,
            "relevant": [ref(u) for u in dict.fromkeys(relevant)],
            "answerable": bool(relevant),
            "pool_size": len(pool),
            "pool_depth": args.depth,
            "annotator": args.annotator,
            "notes": input("note (optional): ").strip(),
            "created": dt.date.today().isoformat(),
        })
        QUERIES_FILE.write_text(json.dumps(records, indent=2) + "\n")  # save after every query
        print(f"Saved ({n_repo} queries for this repo, {len(records)} total).")


if __name__ == "__main__":
    main()
