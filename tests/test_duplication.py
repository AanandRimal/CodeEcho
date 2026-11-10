"""Phase 4: diff parsing, structural comparison, review report; on a throwaway git repo."""

import subprocess
import textwrap
from pathlib import Path

import pytest

from codeecho.duplication.diff import changed_functions
from codeecho.duplication.review import INSUFFICIENT, LIKELY, render, review
from codeecho.duplication.structural import structural_similarity
from codeecho.indexer import index_repo
from codeecho.retrieval.bm25 import BM25Retriever

NORMALIZE = '''
    def normalize_email(addr):
        parts = addr.strip().lower().split("@")
        if len(parts) != 2:
            raise ValueError("bad address")
        local, domain = parts
        return local + "@" + domain
'''
COUNT = '''
    def count_words(text):
        counts = {}
        for word in text.split():
            counts[word] = counts.get(word, 0) + 1
        return counts
'''
OLD_HELPER = '''
    def old_helper(items):
        total = 0
        for item in items:
            if item > 0:
                total += item
        return total
'''
# Renamed copy of normalize_email: same structure, different names and literals (Type-2).
CLEAN_MAIL = '''
    def clean_mail(value):
        bits = value.strip().lower().split("#")
        if len(bits) != 2:
            raise ValueError("nope")
        first, second = bits
        return first + "#" + second
'''
FIBONACCI = '''
    def fibonacci(n):
        a, b = 0, 1
        out = []
        while len(out) < n:
            out.append(a)
            a, b = b, a + b
        return out
'''


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text(textwrap.dedent(text).lstrip("\n"))


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str, str]:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    write(tmp_path, "pkg/mail.py", NORMALIZE)
    write(tmp_path, "pkg/text.py", COUNT)
    write(tmp_path, "pkg/old.py", OLD_HELPER)
    git(tmp_path, "add", "-A"), git(tmp_path, "commit", "-q", "-m", "base")
    base = git(tmp_path, "rev-parse", "HEAD")
    write(tmp_path, "pkg/more_mail.py", CLEAN_MAIL)                          # added: renamed copy
    write(tmp_path, "pkg/seq.py", FIBONACCI)                                 # added: unrelated
    write(tmp_path, "pkg/moved.py", OLD_HELPER.replace("old_helper", "sum_positive"))  # moved + renamed
    (tmp_path / "pkg/old.py").unlink()
    write(tmp_path, "pkg/text.py", COUNT.replace("+ 1", "+ 2"))              # modified in place
    git(tmp_path, "add", "-A"), git(tmp_path, "commit", "-q", "-m", "head")
    return tmp_path, base, git(tmp_path, "rev-parse", "HEAD")


def bm25(units):
    return BM25Retriever(units)


def test_changed_functions_added_modified_and_moved(repo):
    path, base, head = repo
    cs = changed_functions(path, base, head)
    assert {(c.unit.qualname, c.status) for c in cs.changed} == {
        ("pkg.more_mail.clean_mail", "added"), ("pkg.seq.fibonacci", "added"), ("pkg.text.count_words", "modified")}
    assert [c.unit.qualname for c in cs.moved_or_renamed] == ["pkg.moved.sum_positive"]
    assert len(cs.base_units) == 3                                           # the state BEFORE the change


def test_structural_similarity_ignores_names_and_literals(tmp_path):
    write(tmp_path, "a.py", NORMALIZE + CLEAN_MAIL + FIBONACCI)
    u = {x.name: x for x in index_repo(tmp_path).functions}
    assert structural_similarity(u["normalize_email"], u["clean_mail"]) == 1.0
    assert structural_similarity(u["normalize_email"], u["fibonacci"]) < 0.6


def test_review_flags_renamed_copy_and_not_unrelated(repo):
    path, base, head = repo
    report = review(path, base, head, make_retriever=bm25)
    by_name = {f.function.name: f for f in report.findings}
    assert by_name["clean_mail"].category == LIKELY
    assert by_name["clean_mail"].matches[0].unit.name == "normalize_email"
    assert by_name["fibonacci"].category == INSUFFICIENT
    # the modified function never matches its own previous version
    assert all(m.unit.qualname != "pkg.text.count_words" for m in by_name["count_words"].matches)
    assert report.moved_or_renamed == 1
    text = render(report)
    assert "clean_mail" in text and "not confirmed duplicates" in text and "fibonacci" not in text
