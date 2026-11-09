"""CLI end to end on the throwaway git repo from the duplication tests."""

from typer.testing import CliRunner

from devtrust.cli import app
from tests.test_duplication import repo  # noqa: F401  (pytest fixture)

runner = CliRunner()


def test_search_bm25_finds_function(repo):  # noqa: F811
    path, _, _ = repo
    out = runner.invoke(app, ["search", "normalize email address lower", "--repo", str(path), "--method", "bm25", "-k", "2"])
    assert out.exit_code == 0 and "normalize_email" in out.output.splitlines()[0]


def test_search_rejects_unknown_method(repo):  # noqa: F811
    path, _, _ = repo
    assert runner.invoke(app, ["search", "x", "--repo", str(path), "--method", "nope"]).exit_code != 0


def test_review_range_and_single_commit(repo):  # noqa: F811
    path, base, head = repo
    for diff in (f"{base}..{head}", head):                 # a single commit means its own change
        out = runner.invoke(app, ["review", "--diff", diff, "--repo", str(path)])
        assert out.exit_code == 0, out.output
        assert "clean_mail" in out.output and "likely_duplicate" in out.output
        assert "not confirmed duplicates" in out.output
