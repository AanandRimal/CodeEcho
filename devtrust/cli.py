"""Command line: `devtrust index <repo>`, `devtrust search "<query>"`, `devtrust review --diff <range>`."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Find existing functions in a Python repo and review diffs for duplicated code.",
                  no_args_is_help=True)

METHODS = ("code", "general", "bm25", "hybrid", "rerank")


def _retriever(units, method: str):
    """Build one of the search settings evaluated in RQ1 (results/retrieval.json)."""
    from devtrust.retrieval.bm25 import BM25Retriever
    from devtrust.retrieval.dense import DenseRetriever
    from devtrust.retrieval.hybrid import RRFRetriever
    from devtrust.retrieval.rerank import CrossEncoderReranker

    if method == "bm25":
        return BM25Retriever(units)
    if method == "general":
        return DenseRetriever(units, model_name="BAAI/bge-small-en-v1.5")
    code = DenseRetriever(units, model_name="nomic-ai/CodeRankEmbed")
    if method == "code":
        return code
    hybrid = RRFRetriever([BM25Retriever(units), code])
    return hybrid if method == "hybrid" else CrossEncoderReranker(hybrid, top_n=50)


@app.command()
def index(repo: Path = typer.Argument(Path("."), help="Repository root")) -> None:
    """Parse the repo, report what was indexed and what failed, and warm the embedding cache."""
    from devtrust.indexer import index_repo

    result = index_repo(repo)
    typer.echo(f"{len(result.functions)} functions from {result.files_parsed} files "
               f"({result.files_skipped} test files skipped, {len(result.failures)} files failed to parse).")
    for path, err in result.failures[:10]:
        typer.echo(f"  parse failure: {path}: {err[:100]}")
    _retriever(result.functions, "code")
    typer.echo("Embeddings cached (.cache/embeddings).")


@app.command()
def search(query: str = typer.Argument(..., help="What you need, in plain words"),
           repo: Path = typer.Option(Path("."), help="Repository root"),
           k: int = typer.Option(5, "--k", "-k", help="Number of results"),
           method: str = typer.Option("code", help=f"One of {', '.join(METHODS)}. 'code' scored best in RQ1; "
                                                    "see results/retrieval.json")) -> None:
    """Find existing functions that match a description."""
    from devtrust.indexer import index_repo

    if method not in METHODS:
        raise typer.BadParameter(f"method must be one of {METHODS}")
    units = index_repo(repo).functions
    for rank, (u, score) in enumerate(_retriever(units, method).search(query, k), 1):
        typer.echo(f"{rank}. {u.qualname}   {u.file_path}:{u.start_line}-{u.end_line}   score {score:.3f}\n"
                   f"   {u.signature[:110]}")


@app.command()
def review(diff: str = typer.Option(..., "--diff", help="Commit range 'base..head', or one commit (its change)"),
           repo: Path = typer.Option(Path("."), help="Git repository"),
           top_k: int = typer.Option(5, help="Candidates searched per new function"),
           show_all: bool = typer.Option(False, "--all", help="Also show functions with insufficient evidence")) -> None:
    """Flag new or changed functions that closely resemble code already in the repo (candidates, not proof)."""
    from devtrust.duplication.review import render, review as run_review

    base, _, head = diff.partition("..")
    if not head:                                  # a single commit means "that commit's own change"
        base, head = f"{base}^", base
    typer.echo(render(run_review(repo, base, head, top_k=top_k), show_all=show_all))


if __name__ == "__main__":
    app()
