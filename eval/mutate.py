"""Synthetic Type-1/2/3 clone generation with `ast`, in the spirit of the Roy & Cordy (2009) mutation
framework (A6 in docs/related_work.md). The original framework has no Python support, so this is a
small reimplementation of a few of its operators, not their tool:

  type1: layout and comments changed (ast.unparse reformats; a comment is added)
  type2: systematic renaming of the function, its arguments and its local variables (mSRI-like), and
         literal values changed (strings get a suffix, integers >= 2 are incremented)
  type3: type2, plus one statement inserted or deleted at the top level of the body (small insertion /
         small deletion)

Names that are not bound in the function (globals, imports, builtins, attributes, keyword-argument
names) are never renamed. Literal changes can alter behaviour; that is how Type-2 is defined
(syntactic, not semantic).
"""

from __future__ import annotations

import ast
import random

NAMES = ["value", "item", "entry", "node", "data", "result", "current", "chunk", "token", "record",
         "target", "source", "output", "buffer", "part", "elem", "key_", "obj", "payload_", "info",
         "state", "total", "acc", "text_", "pos", "idx_", "flag", "cfg", "opts", "ctx", "conv",
         "block", "piece", "unit_", "seg", "field_", "row", "cell", "line_", "word_"]
KEEP = {"self", "cls"}


def _bound_names(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Function name, parameters and every name bound inside (assignments, loops, with, except, defs)."""
    seen: dict[str, None] = {fn.name: None}
    for a in ast.walk(fn.args):
        if isinstance(a, ast.arg):
            seen[a.arg] = None
    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            seen[n.id] = None
        elif isinstance(n, ast.ExceptHandler) and n.name:
            seen[n.name] = None
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not fn:
            seen[n.name] = None
    return [s for s in seen if s not in KEEP]


class _Rename(ast.NodeTransformer):
    def __init__(self, mapping: dict[str, str]) -> None:
        self.m = mapping

    def visit_Name(self, node):
        node.id = self.m.get(node.id, node.id)
        return node

    def visit_arg(self, node):
        node.arg = self.m.get(node.arg, node.arg)
        return node

    def visit_FunctionDef(self, node):
        node.name = self.m.get(node.name, node.name)
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ExceptHandler(self, node):
        if node.name:
            node.name = self.m.get(node.name, node.name)
        self.generic_visit(node)
        return node


class _Literals(ast.NodeTransformer):
    def __init__(self, skip: set[int]) -> None:
        self.skip = skip

    def visit_Constant(self, node):
        if id(node) in self.skip:
            return node
        v = node.value
        if isinstance(v, str) and v:
            node.value = v + "x"
        elif isinstance(v, int) and not isinstance(v, bool) and v >= 2:
            node.value = v + 1
        return node


def _parse(src: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    return ast.parse(src).body[0]


def _docstring_nodes(fn) -> set[int]:
    if ast.get_docstring(fn) is None:
        return set()
    return {id(n) for n in ast.walk(fn.body[0])}


def type1(src: str) -> str:
    """Reformat (comments and layout dropped) and add a comment."""
    return "# local copy of a helper\n" + ast.unparse(ast.parse(src))


def type2(src: str, rng: random.Random) -> str:
    """Systematic identifier renaming plus literal changes."""
    fn = _parse(src)
    skip = _docstring_nodes(fn)
    names = rng.sample(NAMES, len(NAMES))
    taken = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}   # avoid colliding with globals used inside
    mapping = {}
    for old in _bound_names(fn):
        new = next((c for c in names if c not in taken and c not in mapping.values()), f"v_{len(mapping)}")
        mapping[old] = new
    fn = _Rename(mapping).visit(fn)
    fn = _Literals(skip).visit(fn)
    return ast.unparse(ast.fix_missing_locations(ast.Module([fn], [])))


def type3(src: str, rng: random.Random) -> str:
    """Type-2 changes plus one top-level statement inserted or deleted."""
    fn = _parse(type2(src, rng))
    start = 1 if ast.get_docstring(fn) is not None else 0
    body = fn.body
    deletable = [i for i in range(start, len(body) - 1) if not isinstance(body[i], (ast.Return, ast.Raise))]
    if len(body) - start >= 4 and deletable and rng.random() < 0.5:
        del body[rng.choice(deletable)]
    else:
        body.insert(rng.randint(start, max(start, len(body) - 1)), ast.parse("_checked = True").body[0])
    return ast.unparse(ast.fix_missing_locations(ast.Module([fn], [])))
