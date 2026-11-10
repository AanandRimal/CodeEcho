"""MCP server: both tools are registered and review_diff works on the throwaway git repo."""

import asyncio

from codeecho.mcp_server import mcp, review_diff
from tests.test_duplication import repo  # noqa: F401  (pytest fixture)


def test_tools_registered():
    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert names == {"search_existing_functions", "review_diff"}


def test_review_diff_flags_duplicate(repo):  # noqa: F811
    path, base, head = repo
    out = review_diff(base, head, str(path))
    assert "clean_mail" in out and "likely_duplicate" in out
