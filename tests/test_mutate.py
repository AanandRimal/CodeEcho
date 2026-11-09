"""Mutation operators: output parses, has the intended relationship to the original."""

import ast
import random

from eval.mutate import type1, type2, type3

SRC = '''def total_positive(items, limit=10):
    """Sum the positive items."""
    out = 0
    for item in items:
        if item > 0 and out < limit:
            out += item
    label = "done"
    return out
'''


def run(src: str, name: str, *args):
    ns: dict = {}
    exec(src, ns)
    return ns[name](*args)


def test_type1_keeps_behaviour_and_structure():
    out = type1(SRC)
    assert out.startswith("#") and run(out, "total_positive", [3, -1, 4]) == run(SRC, "total_positive", [3, -1, 4])
    assert ast.dump(ast.parse(out)) == ast.dump(ast.parse(SRC))


def test_type2_renames_everything_bound_and_changes_literals():
    out = type2(SRC, random.Random(0))
    tree = ast.parse(out)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {a.arg for a in ast.walk(tree) if isinstance(a, ast.arg)}
    assert not names & {"items", "item", "out", "limit", "label"} and "total_positive" not in out
    assert ("'donex'" in out or '"donex"' in out) and "Sum the positive items." in out  # literal changed, docstring kept
    assert [type(n).__name__ for n in ast.walk(tree)] == [type(n).__name__ for n in ast.walk(ast.parse(SRC))]


def test_type3_changes_statement_count_by_one_and_is_deterministic():
    outs = {type3(SRC, random.Random(s)) for s in range(20)}
    n = lambda s: len(ast.parse(s).body[0].body)
    assert all(abs(n(o) - n(SRC)) == 1 for o in outs)
    assert type3(SRC, random.Random(5)) == type3(SRC, random.Random(5))
    assert len({n(o) - n(SRC) for o in outs}) == 2      # both insertion and deletion occur
