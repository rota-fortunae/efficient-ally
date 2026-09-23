"""Command-line interface: `efficient-ally path/to/file.py`."""

from __future__ import annotations

import argparse
import difflib
import json
import sys
import textwrap
from pathlib import Path

from .analyzer import analyze
from .edits import Edit, apply_edits, split_lines
from .findings import Report


def main(argv: list[str] | None = None) -> int:
    """Exit status: 0 if nothing was found, 1 if there are findings, 2 on errors."""
    parser = argparse.ArgumentParser(
        prog="efficient-ally",
        description="Find Python code that is slower than it needs to be, and suggest rewrites.",
    )
    parser.add_argument("files", nargs="+", type=Path, help="Python files to analyze")
    parser.add_argument(
        "--json", action="store_true", help="print JSON (the format the website's API will use)"
    )
    args = parser.parse_args(argv)

    status = 0
    reports = []
    for path in args.files:
        try:
            source = path.read_text(encoding="utf-8")
            report = analyze(source, filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            print(f"{path}: error: {error}", file=sys.stderr)
            status = 2
            continue
        if report.findings:
            status = max(status, 1)
        if args.json:
            reports.append(report.to_dict())
        else:
            print(format_report(report, source))
    if args.json:
        print(json.dumps(reports, indent=2))
    return status


def format_report(report: Report, source: str) -> str:
    out = [report.filename]
    if report.functions:
        out.append("  Estimated running time (calls to other functions count as O(1) for now):")
        width = max(len(f.name) for f in report.functions)
        for summary in report.functions:
            out.append(f"    {summary.name:<{width}}  {summary.complexity}")
    if not report.findings:
        out.append("  No inefficient patterns found.")
    for finding in report.findings:
        out.append("")
        out.append(
            f"  {report.filename}:{finding.line}:{finding.col + 1}: "
            f"{finding.title} [{finding.rule}]"
        )
        out.extend(_wrap(finding.explanation))
        out.extend(_wrap("Suggestion: " + finding.suggestion))
        if finding.current is not None and finding.improved is not None:
            out.append(f"    Complexity: {finding.current} -> {finding.improved}")
        if finding.edits:
            out.append("    Suggested change:")
            out.extend("      " + line for line in _diff(source, finding.edits))
    return "\n".join(out)


def _wrap(text: str) -> list[str]:
    return textwrap.wrap(text, width=92, initial_indent="    ", subsequent_indent="    ")


def _diff(source: str, edits: list[Edit]) -> list[str]:
    before, after = split_lines(source), split_lines(apply_edits(source, edits))
    diff = difflib.unified_diff(before, after, lineterm="", n=1)
    return [line for line in diff if not line.startswith(("---", "+++"))]
