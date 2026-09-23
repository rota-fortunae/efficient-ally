"""What rules report, and the report ``analyze`` returns.

``Report.to_dict()`` is the JSON format shared by the CLI (``--json``) and,
later, the website's API, so change it deliberately.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .complexity import Complexity
from .edits import Edit


@dataclass
class Finding:
    rule: str  # rule id, e.g. "list-membership-in-loop"
    title: str  # one-line headline
    line: int  # 1-based line of the flagged code
    col: int  # 0-based column offset
    end_line: int
    explanation: str  # why the code is slow, in plain language
    suggestion: str  # what to do instead
    current: Complexity | None = None  # cost of the flagged code as written
    improved: Complexity | None = None  # cost after following the suggestion
    edits: list[Edit] | None = None  # a concrete rewrite, when we can produce a safe one

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "title": self.title,
            "line": self.line,
            "col": self.col,
            "end_line": self.end_line,
            "explanation": self.explanation,
            "suggestion": self.suggestion,
            "current": None if self.current is None else str(self.current),
            "improved": None if self.improved is None else str(self.improved),
            "edits": None if self.edits is None else [asdict(e) for e in self.edits],
        }


@dataclass
class FunctionSummary:
    name: str  # qualified name, e.g. "Stack.push", or "<module>" for top-level code
    line: int
    complexity: Complexity

    def to_dict(self) -> dict:
        return {"name": self.name, "line": self.line, "complexity": str(self.complexity)}


@dataclass
class Report:
    filename: str
    findings: list[Finding]
    functions: list[FunctionSummary]

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "functions": [f.to_dict() for f in self.functions],
            "findings": [f.to_dict() for f in self.findings],
        }
