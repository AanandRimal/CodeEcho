"""MCP server: lets an AI coding agent search a repo for existing functions and review diffs.

Run:  python -m codeecho.mcp_server          (stdio; register with `claude mcp add`, see README)
Status: implemented, NOT evaluated with agents (docs/DECISIONS.md D34).
Both tools wrap the code evaluated in RQ1/RQ2. Review output is candidates with evidence, not proof.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.mcpserver import MCPServer

from codeecho.cli import _retriever
from codeecho.duplication.review import render, review as run_review
from codeecho.indexer import index_repo

mcp = MCPServer(
    "codeecho",
    instructions="Before writing a new helper or utility, call search_existing_functions to check "
                 "whether the repo already has one. Call review_diff on your change to flag new functions "
                 "that resemble existing code. Results are candidates, not confirmed duplicates.",
)


def search(repo: str, query: str, k: int = 5) -> str:
    """Plain-text search results; split out so it can be tested without the MCP transport."""
    units = index_repo(Path(repo)).functions  # embeddings are disk-cached, so repeat calls are fast
    hits = _retriever(units, "code").search(query, k)
    return "\n".join(f"{i}. {u.qualname}  {u.file_path}:{u.start_line}-{u.end_line}  score {s:.3f}\n   {u.signature[:110]}"
                     for i, (u, s) in enumerate(hits, 1)) or "No functions found."


@mcp.tool()
def search_existing_functions(query: str, repo: str = ".", k: int = 5) -> str:
    """Find functions already in the repo that match a plain-language description (e.g. 'parse a duration
    string into seconds'). Call this BEFORE writing a new helper. The first call on a repo builds an index
    and can take a while."""
    return search(repo, query, k)


@mcp.tool()
def review_diff(base: str, head: str = "HEAD", repo: str = ".") -> str:
    """Review the change base..head and flag newly added functions that closely resemble code already in
    the repo, with side-by-side evidence. Findings are candidates, not proof; verify before acting."""
    return render(run_review(Path(repo), base, head))


if __name__ == "__main__":
    mcp.run()
