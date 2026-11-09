"""Parse a Python repository into function-level units (Phase 1)."""

from __future__ import annotations

import ast
import os
import textwrap
import tokenize
from dataclasses import dataclass, field
from pathlib import Path

# Directory names that are never indexed: tests, vendored code, environments, build output.
SKIP_DIRS = frozenset({
    "test", "tests",
    "vendor", "vendored", "_vendor", "third_party", "thirdparty", "site-packages", "node_modules",
    "venv", "env", "build", "dist", "__pycache__",
})


@dataclass(frozen=True)
class FunctionUnit:
    """One function or method extracted from a repository."""

    name: str
    qualname: str                   # dotted module path + enclosing classes/functions
    signature: str                  # e.g. "async def fetch(self, key) -> str"
    docstring: str | None
    source: str                     # full source incl. decorators and docstring, dedented
    body: str                       # body source without the docstring, dedented
    file_path: str                  # POSIX path relative to the repo root
    start_line: int                 # 1-based; first decorator line if decorated
    end_line: int
    decorators: tuple[str, ...]
    imports_used: tuple[str, ...]   # module-level imports referenced inside the function


@dataclass
class IndexResult:
    """Functions found in a repo, plus counts for the parse report."""

    functions: list[FunctionUnit] = field(default_factory=list)
    files_parsed: int = 0
    files_skipped: int = 0                                         # test files skipped by name
    failures: list[tuple[str, str]] = field(default_factory=list)  # (path, error)


def _is_test_file(name: str) -> bool:
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def _iter_py_files(root: Path, result: IndexResult):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            if _is_test_file(name):
                result.files_skipped += 1
                continue
            yield Path(dirpath) / name


def _import_map(tree: ast.Module) -> dict[str, str]:
    """Map each name bound by an import in the file to what it refers to."""
    # ponytail: ignores later rebinding of an imported name; fine for a "which imports are used" hint.
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names[a.asname or a.name.split(".")[0]] = a.name
        elif isinstance(node, ast.ImportFrom):
            base = "." * node.level + (node.module or "")
            for a in node.names:
                if a.name != "*":
                    names[a.asname or a.name] = f"{base}.{a.name}" if node.module else f"{base}{a.name}"
    return names


def _functions(node: ast.AST, prefix: str):
    """Yield (function node, qualname) for every def nested anywhere under node."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qual = f"{prefix}.{child.name}".lstrip(".")
            yield child, qual
            yield from _functions(child, qual)
        elif isinstance(child, ast.ClassDef):
            yield from _functions(child, f"{prefix}.{child.name}".lstrip("."))
        else:
            yield from _functions(child, prefix)


def _first_line(stmt: ast.stmt) -> int:
    decorators = getattr(stmt, "decorator_list", [])
    return min([d.lineno for d in decorators] + [stmt.lineno])


def _unit(node: ast.FunctionDef | ast.AsyncFunctionDef, qualname: str, lines: list[str],
          rel_path: str, imports: dict[str, str]) -> FunctionUnit:
    start, end = _first_line(node), node.end_lineno
    docstring = ast.get_docstring(node)
    rest = node.body[1:] if docstring is not None else node.body
    if not rest:
        body = ""
    elif lines[rest[0].lineno - 1][:rest[0].col_offset].strip():
        # Body shares a line with the header or docstring (e.g. `def f(): return 1`): no clean slice.
        body = "\n".join(ast.unparse(s) for s in rest)
    else:
        body = textwrap.dedent("\n".join(lines[_first_line(rest[0]) - 1:end])).strip("\n")

    signature = f"{'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}def {node.name}({ast.unparse(node.args)})"
    if node.returns is not None:
        signature += f" -> {ast.unparse(node.returns)}"

    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
    return FunctionUnit(
        name=node.name,
        qualname=qualname,
        signature=signature,
        docstring=docstring,
        source=textwrap.dedent("\n".join(lines[start - 1:end])).strip("\n"),
        body=body,
        file_path=rel_path,
        start_line=start,
        end_line=end,
        decorators=tuple(ast.unparse(d) for d in node.decorator_list),
        imports_used=tuple(sorted({imports[n] for n in used if n in imports})),
    )


def index_repo(root: str | Path) -> IndexResult:
    """Extract every function and method from the non-test, non-vendored .py files under root.

    Files that cannot be read or parsed are recorded in ``IndexResult.failures`` and skipped.
    Output order is deterministic (sorted directory walk, source order within a file).
    """
    root = Path(root)
    result = IndexResult()
    for path in _iter_py_files(root, result):
        rel = path.relative_to(root).as_posix()
        try:
            with tokenize.open(path) as f:  # honours PEP 263 encoding cookies and BOMs
                text = f.read()
            tree = ast.parse(text, filename=rel)
        except (SyntaxError, UnicodeDecodeError, ValueError, RecursionError) as e:
            result.failures.append((rel, f"{type(e).__name__}: {e}"))
            continue
        result.files_parsed += 1
        module = ".".join(p for p in Path(rel).with_suffix("").parts if p != "__init__")
        lines, imports = text.splitlines(), _import_map(tree)
        result.functions.extend(_unit(n, q, lines, rel, imports) for n, q in _functions(tree, module))
    return result
