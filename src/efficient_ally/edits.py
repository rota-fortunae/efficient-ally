"""Line-based edits that describe a suggested rewrite of the user's code."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

_NEWLINE = re.compile(r"\r\n|\r|\n")


@dataclass(frozen=True)
class Edit:
    line: int  # 1-based line number in the original source
    action: Literal["replace", "insert_before", "insert_after"]
    text: str  # the new line of code, including its indentation


def split_lines(source: str) -> list[str]:
    """Split source into lines the same way the Python parser numbers them."""
    return _NEWLINE.split(source)


def apply_edits(source: str, edits: Iterable[Edit]) -> str:
    """Return ``source`` with ``edits`` applied. Line numbers refer to the original source."""
    lines = split_lines(source)
    # Apply from the bottom up so earlier line numbers stay valid.
    order = {"insert_after": 0, "replace": 1, "insert_before": 2}
    for edit in sorted(edits, key=lambda e: (-e.line, order[e.action])):
        index = edit.line - 1
        if edit.action == "replace":
            lines[index] = edit.text
        elif edit.action == "insert_before":
            lines.insert(index, edit.text)
        else:
            lines.insert(index + 1, edit.text)
    return "\n".join(lines)


def replace_span(line: str, start: int, end: int, new: str) -> str:
    """Replace part of ``line``. ``start``/``end`` are UTF-8 byte offsets, as ``ast`` reports."""
    raw = line.encode("utf-8")
    return raw[:start].decode("utf-8") + new + raw[end:].decode("utf-8")


def indentation(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]
