"""Shared helpers for retrievers (Phase 2).

Every retriever exposes ``search(query, k) -> list[(FunctionUnit, score)]``, best first.
"""

from __future__ import annotations

import re

from codeecho.indexer import FunctionUnit

_WORD = re.compile(r"[A-Za-z0-9_]+")
_CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")


def doc_text(unit: FunctionUnit, include_docstring: bool = False) -> str:
    """Text indexed for a function: signature, optional docstring, and body.

    The docstring is off by default because benchmark queries are often docstring-like,
    so indexing it would leak the answer.
    """
    parts = [unit.signature, unit.docstring if include_docstring and unit.docstring else "", unit.body]
    return "\n".join(p for p in parts if p)


def tokenize(text: str, split_identifiers: bool = True) -> list[str]:
    """Lowercase word tokens. With split_identifiers, ``parseHTTPResponse_v2`` also yields
    ``parse``, ``http``, ``response``, ``v``, ``2``, and the whole identifier is kept too."""
    tokens = []
    for word in _WORD.findall(text):
        tokens.append(word.lower())
        if split_identifiers:
            parts = [p.lower() for chunk in word.split("_") for p in _CAMEL.findall(chunk)]
            if len(parts) > 1:
                tokens.extend(parts)
    return tokens
