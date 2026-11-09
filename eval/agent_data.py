"""RQ3 data: the table of merged agent PRs (AIDev) and sampled human PRs (GitHub API) for our 3 repos.

Usage:  .venv/bin/python -m eval.agent_data
Needs GITHUB_TOKEN in .env (read-only, public repos). Writes data/agent_prs.json and clones each repo with
full history (bare) into .cache/repos_full/ so PR commits can be checked out. See docs/DECISIONS.md D32.

Groups: the agent name (AIDev `agent` column) or "human". Only merged PRs are used, in both groups.
Human PRs: merged in the same repo within [first, last] merge date of that repo's merged agent PRs, not
authored by a GitHub Bot account, not listed in AIDev (any agent PR, merged or not); a seeded random sample.
Each PR gets base_sha / head_sha from the API; the review later uses merge-base(base, head) as "before".
"""

from __future__ import annotations

import datetime as dt
import json
import random
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

from eval.repos import load_repos

SEED, N_HUMAN = 0, 150
OUT = Path("data/agent_prs.json")
FULL = Path(".cache/repos_full")


def _token() -> str:
    return next(l.split("=", 1)[1].strip().strip("'\"") for l in open(".env") if l.startswith("GITHUB_TOKEN="))


def api(path: str, tok: str) -> object:
    """GET https://api.github.com{path}; one patient retry on rate-limit style 403s."""
    for attempt in (0, 1):
        req = urllib.request.Request("https://api.github.com" + path, headers={
            "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json", "User-Agent": "devtrust-eval"})
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                return json.load(f)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt == 0:
                time.sleep(int(e.headers.get("retry-after") or 65))
                continue
            raise


def clone_full(repo: str) -> Path:
    """Bare clone with full history (public repo, no token needed)."""
    dest = FULL / (repo.replace("/", "__") + ".git")
    if not dest.exists():
        FULL.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--bare", "--quiet", f"https://github.com/{repo}.git", str(dest)], check=True)
    return dest


def fetch_pr_heads(repo_dir: Path, numbers: list[int]) -> None:
    """Fetch refs/pull/N/head for the given PR numbers (works for merged PRs and deleted fork branches)."""
    for i in range(0, len(numbers), 100):
        specs = [f"+refs/pull/{n}/head:refs/pull/{n}/head" for n in numbers[i:i + 100]]
        subprocess.run(["git", "-C", str(repo_dir), "fetch", "--quiet", "origin", *specs], check=False)


def main() -> None:
    tok = _token()
    aidev_pr = pd.read_parquet(".cache/aidev/pull_request.parquet")
    aidev_repo = pd.read_parquet(".cache/aidev/repository.parquet")
    rows, meta = [], {}
    for repo in load_repos():
        rid = int(aidev_repo.loc[aidev_repo["full_name"] == repo, "id"].iloc[0])
        mine = aidev_pr[aidev_pr["repo_id"] == rid]
        merged = mine[mine["merged_at"].notna()]
        lo, hi = merged["merged_at"].min(), merged["merged_at"].max()
        agent_numbers = set(int(n) for n in mine["number"])           # every AIDev agent PR, merged or not
        print(f"{repo}: {len(merged)} merged agent PRs, window {lo} .. {hi}", flush=True)
        for _, r in merged.iterrows():
            d = api(f"/repos/{repo}/pulls/{int(r['number'])}", tok)
            rows.append({"repo": repo, "number": int(r["number"]), "group": r["agent"], "merged_at": r["merged_at"],
                         "base_sha": d["base"]["sha"], "head_sha": d["head"]["sha"], "url": r["html_url"]})
        humans, page = [], 1
        while True:
            batch = api(f"/repos/{repo}/pulls?state=closed&per_page=100&page={page}", tok)
            if not batch:
                break
            humans += [p for p in batch if p["merged_at"] and lo <= p["merged_at"] <= hi
                       and p["user"]["type"] == "User" and p["number"] not in agent_numbers]
            page += 1
        humans.sort(key=lambda p: p["number"])
        sample = random.Random(f"{SEED}|{repo}").sample(humans, min(N_HUMAN, len(humans)))
        print(f"  human merged PRs eligible: {len(humans)}, sampled {len(sample)}", flush=True)
        meta[repo] = {"window": [lo, hi], "n_merged_agent": len(merged), "n_human_eligible": len(humans),
                      "n_human_sampled": len(sample)}
        rows += [{"repo": repo, "number": p["number"], "group": "human", "merged_at": p["merged_at"],
                  "base_sha": p["base"]["sha"], "head_sha": p["head"]["sha"], "url": p["html_url"]}
                 for p in sorted(sample, key=lambda p: p["number"])]
        repo_dir = clone_full(repo)
        fetch_pr_heads(repo_dir, [r["number"] for r in rows if r["repo"] == repo])
    OUT.write_text(json.dumps({
        "meta": {"date": dt.date.today().isoformat(), "seed": SEED, "n_human_per_repo_max": N_HUMAN,
                 "source_agents": "hao-li/AIDev pull_request.parquet (merged PRs only)",
                 "source_humans": "GitHub REST API /pulls?state=closed", "repos": meta},
        "prs": rows}, indent=1) + "\n")
    print(f"Wrote {OUT}: {len(rows)} PRs")


if __name__ == "__main__":
    main()
