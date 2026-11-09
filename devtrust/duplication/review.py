"""Duplication review of a git change: search the pre-change repo, then verify structurally (Phase 4).

Findings are candidates with evidence, never confirmed duplicates. The thresholds below are
PROVISIONAL placeholders; they are chosen on the dev split in Phase 5 (docs/DECISIONS.md D28).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import zip_longest
from pathlib import Path
from typing import Callable

from devtrust.duplication.diff import ChangedFunction, changed_functions
from devtrust.duplication.structural import structural_similarity, structure
from devtrust.indexer import FunctionUnit
from devtrust.retrieval.dense import DenseRetriever

HI, LO, MIN_NODES = 0.9, 0.6, 10   # provisional: likely_duplicate >= HI, similar_but_different >= LO
LIKELY, SIMILAR, INSUFFICIENT = "likely_duplicate", "similar_but_different", "insufficient_evidence"


@dataclass
class Match:
    unit: FunctionUnit
    retrieval_score: float
    structural_score: float


@dataclass
class Finding:
    function: FunctionUnit
    status: str                  # "added" | "modified"
    category: str
    confidence: str              # "high" | "medium" | "low"; provisional, see module docstring
    matches: list[Match]         # best structural match first


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    skipped_small: int = 0       # changed functions below MIN_NODES, not reviewed
    moved_or_renamed: int = 0    # filtered: same body as a function removed in the same change
    n_changed: int = 0


def default_retriever(units: list[FunctionUnit]):
    """Code embedder from the thin slice (docs/DECISIONS.md D5); embeddings are disk-cached."""
    return DenseRetriever(units, model_name="nomic-ai/CodeRankEmbed")


def _category(score: float, hi: float, lo: float) -> tuple[str, str]:
    if score >= hi:
        return LIKELY, "high" if score >= 0.95 else "medium"
    return (SIMILAR, "low") if score >= lo else (INSUFFICIENT, "low")


def review(repo: str | Path, base: str, head: str,
           make_retriever: Callable[[list[FunctionUnit]], object] = default_retriever,
           top_k: int = 5, hi: float = HI, lo: float = LO) -> Report:
    """Review the change base..head of the git repo at `repo` for new functions that resemble old ones.

    For each added or modified function, the pre-change repo is searched for the `top_k` most
    similar functions (the function's own previous version is excluded), and each candidate is
    scored structurally. The category comes from the best structural score.
    """
    cs = changed_functions(repo, base, head)
    retriever = make_retriever(cs.base_units)
    report = Report(moved_or_renamed=len(cs.moved_or_renamed), n_changed=len(cs.changed))
    for cf in cs.changed:
        if len(structure(cf.unit)) < MIN_NODES:
            report.skipped_small += 1
            continue
        own = (cf.previous.file_path, cf.previous.qualname) if cf.previous else None
        hits = [(u, s) for u, s in retriever.search(cf.unit.source, top_k + 1)
                if (u.file_path, u.qualname) != own][:top_k]
        matches = sorted((Match(u, s, structural_similarity(cf.unit, u)) for u, s in hits),
                         key=lambda m: -m.structural_score)
        best = matches[0].structural_score if matches else 0.0
        category, confidence = _category(best, hi, lo)
        report.findings.append(Finding(cf.unit, cf.status, category, confidence, matches))
    return report


def _side_by_side(a: str, b: str, width: int = 58) -> str:
    rows = zip_longest(a.splitlines(), b.splitlines(), fillvalue="")
    return "\n".join(f"{x[:width]:<{width}} | {y[:width]}" for x, y in rows)


def render(report: Report, show_all: bool = False) -> str:
    """Plain-text report. By default omits `insufficient_evidence` findings. Never claims certainty."""
    shown = [f for f in report.findings if show_all or f.category != INSUFFICIENT]
    lines = [f"{report.n_changed} changed functions: {len(report.findings)} reviewed, "
             f"{report.skipped_small} too small to review, {report.moved_or_renamed} moved/renamed (filtered). "
             f"{len(shown)} candidate(s) below. These are candidates for a human to check, not confirmed duplicates."]
    for f in shown:
        m = f.matches[0]
        lines += ["", "=" * 120,
                  f"[{f.category}, confidence {f.confidence}] {f.status} {f.function.qualname} "
                  f"({f.function.file_path}:{f.function.start_line}-{f.function.end_line})",
                  f"  resembles {m.unit.qualname} ({m.unit.file_path}:{m.unit.start_line}-{m.unit.end_line})  "
                  f"retrieval score {m.retrieval_score:.3f}, structural score {m.structural_score:.3f}"]
        for other in f.matches[1:3]:
            lines.append(f"  also: {other.unit.qualname} ({other.unit.file_path}:{other.unit.start_line}) "
                         f"structural {other.structural_score:.3f}")
        lines += ["-" * 120, f"{'NEW':<58} | EXISTING", _side_by_side(f.function.source, m.unit.source)]
    return "\n".join(lines)
