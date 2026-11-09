"""Benchmark repos pinned to exact commits (data/repos.json)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPOS_FILE = Path("data/repos.json")
CACHE = Path(".cache/repos")


def load_repos() -> dict[str, dict]:
    """Map full_name -> repo entry from data/repos.json."""
    return {r["full_name"]: r for r in json.loads(REPOS_FILE.read_text())["repos"]}


def checkout(full_name: str) -> Path:
    """Return a local checkout of the repo at its pinned commit, cloning or fetching if needed."""
    commit = load_repos()[full_name]["commit"]
    path = CACHE / full_name.replace("/", "__")
    git = lambda *a: subprocess.run(["git", "-C", str(path), *a], check=True, capture_output=True, text=True)
    if not path.exists():
        path.mkdir(parents=True)
        git("init", "-q")
        git("remote", "add", "origin", f"https://github.com/{full_name}")
    head = subprocess.run(["git", "-C", str(path), "rev-parse", "--verify", "-q", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    if head != commit:
        git("fetch", "-q", "--depth", "1", "origin", commit)
        git("checkout", "-q", "--detach", commit)
    return path
