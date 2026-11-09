"""README table generation: marker replacement and table layout."""

import pytest

from eval.report import _table, inject


def test_inject_replaces_only_the_marked_block():
    text = "a\n<!-- BEGIN:x -->\nold\n<!-- END:x -->\nb\n<!-- BEGIN:y -->\nkeep\n<!-- END:y -->"
    out = inject(text, "x", "NEW")
    assert "NEW" in out and "old" not in out and "keep" in out and out.startswith("a\n")


def test_inject_missing_marker_is_an_error():
    with pytest.raises(ValueError):
        inject("no markers", "x", "NEW")


def test_table_layout():
    assert _table(["a", "b"], [["1", "2"]]) == "| a | b |\n|---|---|\n| 1 | 2 |"
