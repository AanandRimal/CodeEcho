"""Structural similarity of two functions, ignoring identifier names and literal values (Phase 4)."""

from __future__ import annotations

import ast
import difflib

from codeecho.indexer import FunctionUnit


def structure(unit: FunctionUnit) -> list[str]:
    """Node-type sequence of the function's AST, without the docstring.

    Identifier names are never included (so renamed variables, arguments and functions match,
    as in Type-2 clones); a constant keeps only its type, not its value.
    """
    fn = ast.parse(unit.source).body[0]
    if ast.get_docstring(fn) is not None:
        fn.body = fn.body[1:]
    return [f"Constant:{type(n.value).__name__}" if isinstance(n, ast.Constant) else type(n).__name__
            for n in ast.walk(fn)]


def structural_similarity(a: FunctionUnit, b: FunctionUnit) -> float:
    """Similarity in [0, 1] of the two functions' normalised AST node sequences (1.0 = identical)."""
    return difflib.SequenceMatcher(None, structure(a), structure(b), autojunk=False).ratio()
