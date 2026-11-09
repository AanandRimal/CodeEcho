"""Tests for the Phase 1 indexer, on a small fixture repo written to a temp dir."""

import textwrap
from pathlib import Path

import pytest

from devtrust.indexer import index_repo

FILES = {
    "pkg/__init__.py": "",
    "pkg/utils.py": '''
        import re
        from os import path as osp
        import json

        def is_valid_email(addr: str) -> bool:
            """Check whether addr looks like an email."""
            return re.match(r"[^@]+@[^@]+", addr) is not None

        class Store:
            @staticmethod
            def load(p):
                return json.loads(open(osp.join("a", p)).read())

            async def fetch(self, key, *, timeout=1.0):
                def inner():
                    return key
                return inner()

        def one_liner(x): return x + 1

        def doc_only():
            """Nothing else."""

        def split_header(
            a, b,
        ): return a + b
    ''',
    "pkg/msg.py": 'class Msg:\n    def text(self):\n        return """first\nsecond at column zero\n"""\n',
    "pkg/broken.py": "def oops(:\n",
    "pkg/test_helpers.py": "def helper():\n    pass\n",       # test file by name: skipped
    "tests/test_utils.py": "def test_x():\n    pass\n",       # tests dir: skipped
    "vendor/lib.py": "def vendored():\n    pass\n",          # vendored dir: skipped
    ".venv/site.py": "def hidden():\n    pass\n",            # hidden dir: skipped
    "examples/demo.py": "def demo():\n    pass\n",          # examples dir: skipped
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for rel, text in FILES.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text).lstrip("\n"))
    return tmp_path


@pytest.fixture
def units(repo):
    return {u.qualname: u for u in index_repo(repo).functions}


def test_finds_functions_methods_and_nested(units):
    assert set(units) == {
        "pkg.utils.is_valid_email",
        "pkg.utils.Store.load",
        "pkg.utils.Store.fetch",
        "pkg.utils.Store.fetch.inner",
        "pkg.utils.one_liner",
        "pkg.utils.doc_only",
        "pkg.utils.split_header",
        "pkg.msg.Msg.text",
    }


def test_skips_tests_vendor_hidden_and_reports_failures(repo):
    result = index_repo(repo)
    assert result.files_parsed == 3                     # pkg/__init__.py, pkg/utils.py, pkg/msg.py
    assert result.files_skipped == 1                    # pkg/test_helpers.py (tests/ dir pruned entirely)
    assert [path for path, _ in result.failures] == ["pkg/broken.py"]
    assert result.failures[0][1].startswith("SyntaxError")


def test_function_fields(units):
    u = units["pkg.utils.is_valid_email"]
    assert u.name == "is_valid_email"
    assert u.signature == "def is_valid_email(addr: str) -> bool"
    assert u.docstring == "Check whether addr looks like an email."
    assert u.body == 'return re.match(r"[^@]+@[^@]+", addr) is not None'
    assert u.source.startswith("def is_valid_email") and '"""Check' in u.source
    assert (u.file_path, u.start_line, u.end_line) == ("pkg/utils.py", 5, 7)
    assert u.imports_used == ("re",)


def test_decorators_start_line_and_imports(units):
    u = units["pkg.utils.Store.load"]
    assert u.decorators == ("staticmethod",)
    assert u.start_line == 10 and u.source.startswith("@staticmethod")   # decorator line included
    assert u.imports_used == ("json", "os.path")


def test_async_signature(units):
    assert units["pkg.utils.Store.fetch"].signature == "async def fetch(self, key, *, timeout=1.0)"


def test_body_edge_cases(units):
    assert units["pkg.utils.one_liner"].body == "return x + 1"
    assert units["pkg.utils.doc_only"].body == ""
    assert units["pkg.utils.split_header"].body == "return a + b"


def test_deterministic(repo):
    assert index_repo(repo) == index_repo(repo)


def test_method_with_unindented_multiline_string_still_parses(units):
    import ast
    u = units["pkg.msg.Msg.text"]
    assert u.source.startswith("def text(self):") and "second at column zero" in u.source
    ast.parse(u.source)
    ast.parse(u.body)
