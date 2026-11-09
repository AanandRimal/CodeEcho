"""RQ3: do AI-agent PRs add functions that duplicate existing code more often than human PRs?

Usage:
  .venv/bin/python -m eval.agent_eval run        # review every PR in data/agent_prs.json (resumable, slow)
  .venv/bin/python -m eval.agent_eval analyze    # statistics -> results/agents.json   (added in a later step)

`run` reviews each PR with the same detector as the tool: base state = merge-base(base, head), search with
CodeRankEmbed, structural check at the tool's untuned default (best structural >= 0.9 = likely_duplicate).
Per-PR outputs go to .cache/agent_runs/ (git-ignored). Only functions ADDED by the PR are counted (a modified
function can already have resembled another one before the PR). See docs/DECISIONS.md D32.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from devtrust.duplication.review import LIKELY, review
from eval.agent_data import FULL, OUT

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


if __name__ == "__main__":
    {"run": run}[sys.argv[1] if len(sys.argv) > 1 else "run"]()
