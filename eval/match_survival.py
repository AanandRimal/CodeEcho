"""For each likely_duplicate finding, does the matched (existing) function still exist at the PR's head commit?

If it does not, the PR removed or moved it, so the finding is probably a refactor (a move combined with edits
slips past the exact-body move filter, docs/DECISIONS.md D28) and not new duplicated code. Used as a labelled
sensitivity analysis, never to change the main result (D33).
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

from codeecho.indexer import _functions
from eval.agent_eval import repo_dir, load_runs, LIKELY
from eval.agent_data import OUT

CACHE = Path(".cache/match_survival.json")


def _qualnames_at(rd: Path, rev: str, path: str) -> set[str] | None:
    """Qualified names of every function in `path` at `rev` (None if the file does not exist there)."""
    r = subprocess.run(["git", "-C", str(rd), "show", f"{rev}:{path}"], capture_output=True, text=True)
    if r.returncode:
        return None
    try:
        tree = ast.parse(r.stdout)
    except (SyntaxError, ValueError, RecursionError):
        return set()
    module = ".".join(p for p in Path(path).with_suffix("").parts if p != "__init__")
    return {q for _, q in _functions(tree, module)}


def key_of(rec: dict, a: dict) -> str:
    """Unique id of one finding: the PR, the new function's location, and its match."""
    return f"{rec['repo']}#{rec['number']}|{a['file']}:{a['start_line']}|{a['match']}"


def survival() -> dict[str, bool]:
    """{key_of(...): True if the matched function still exists at the PR head}."""
    heads = {(p["repo"], p["number"]): p["head_sha"] for p in json.loads(OUT.read_text())["prs"]}
    out, cache = {}, {}
    for rec in load_runs():
        for a in rec.get("added_reviewed", []):
            if a["category"] != LIKELY:
                continue
            m_path, m_rest = a["match"].split(" ", 1)[0].rsplit(":", 1)[0], a["match"].split(" ", 1)[1]
            head = heads[(rec["repo"], rec["number"])]
            key = (rec["repo"], head, m_path)
            if key not in cache:
                cache[key] = _qualnames_at(repo_dir(rec["repo"]), head, m_path)
            names = cache[key]
            out[key_of(rec, a)] = names is not None and m_rest in names
    CACHE.write_text(json.dumps(out))
    return out


if __name__ == "__main__":
    s = survival()
    print(f"{len(s)} findings; matched function still exists at PR head for {sum(s.values())}")
