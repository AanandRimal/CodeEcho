"""Find the functions a git change adds or modifies, and the repo state before it (Phase 4)."""

from __future__ import annotations

import io
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from codeecho.indexer import FunctionUnit, index_repo


@dataclass
class ChangedFunction:
    """A function in the new state that is added or modified."""

    unit: FunctionUnit
    status: str                            # "added" | "modified"
    previous: FunctionUnit | None = None   # the old version, for "modified"


@dataclass
class ChangeSet:
    base_units: list[FunctionUnit]         # every function in the repo BEFORE the change
    changed: list[ChangedFunction]
    moved_or_renamed: list[ChangedFunction] = field(default_factory=list)  # filtered out, see below


def _git(repo: str | Path, *args: str, text: bool = True):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=text).stdout


def changed_functions(repo: str | Path, base: str, head: str) -> ChangeSet:
    """Functions added or modified between commits `base` and `head` of the git repo at `repo`.

    The base state is the full tree at `base` (the search index). The head state is parsed only
    from the changed .py files. An added function whose body is identical to a function that
    disappeared in the same change is a move or rename, not new code: it is returned in
    `moved_or_renamed`, not in `changed`.
    """
    paths = _git(repo, "diff", "--name-only", "--no-renames", base, head, "--", "*.py").split()
    with tempfile.TemporaryDirectory() as tmp:
        base_dir, head_dir = Path(tmp, "base"), Path(tmp, "head")
        base_dir.mkdir(), head_dir.mkdir()
        with tarfile.open(fileobj=io.BytesIO(_git(repo, "archive", base, "--", ":(glob)**/*.py", text=False))) as tar:
            tar.extractall(base_dir, filter="data")
        for p in paths:
            r = subprocess.run(["git", "-C", str(repo), "show", f"{head}:{p}"], capture_output=True, text=True)
            if r.returncode == 0:                      # non-zero = file deleted in head
                (head_dir / p).parent.mkdir(parents=True, exist_ok=True)
                (head_dir / p).write_text(r.stdout)
        base_units = index_repo(base_dir).functions
        head_units = index_repo(head_dir).functions

    old = {(u.file_path, u.qualname): u for u in base_units}
    new_keys = {(u.file_path, u.qualname) for u in head_units}
    touched = set(paths)
    removed_bodies = {u.body.strip() for u in base_units
                      if u.file_path in touched and (u.file_path, u.qualname) not in new_keys}
    out = ChangeSet(base_units=base_units, changed=[])
    for u in head_units:
        prev = old.get((u.file_path, u.qualname))
        if prev is None:
            cf = ChangedFunction(u, "added")
            moved = u.body.strip() != "" and u.body.strip() in removed_bodies
            (out.moved_or_renamed if moved else out.changed).append(cf)
        elif prev.source != u.source:
            out.changed.append(ChangedFunction(u, "modified", prev))
    return out
