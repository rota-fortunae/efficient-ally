"""The entry point: source code in, `Report` out."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from .complexity import ONE, estimate
from .findings import FunctionSummary, Report
from .model import ProgramModel
from .rules import ALL_RULES, Rule


def analyze(source: str, filename: str = "<input>", rules: Sequence[Rule] = ALL_RULES) -> Report:
    """Analyze Python source code. Raises ``SyntaxError`` if it doesn't parse."""
    model = ProgramModel(source, filename)
    findings = sorted(
        (finding for rule in rules for finding in rule.check(model)),
        key=lambda f: (f.line, f.col),
    )
    functions = sorted(model.functions(), key=lambda item: item[1].lineno)

    def owner(line: int):
        """The innermost function containing ``line``, or None for top-level code."""
        best = None
        for _, node in functions:
            if node.lineno <= line <= node.end_lineno and (
                best is None or node.lineno > best.lineno
            ):
                best = node
        return best

    # Rules can see costs the loop estimator misses (like the copying in `s += x`),
    # so fold what they found into the estimate of the function they're in.
    # Adding a cost that's already counted doesn't change anything: O(n) + O(n) is O(n).
    extra = defaultdict(lambda: ONE)
    for finding in findings:
        if finding.current is not None:
            key = owner(finding.line)
            extra[key] = extra[key] + finding.current

    summaries = []
    top_level = estimate(model.tree.body, model) + extra[None]
    if top_level.degree > 0:
        summaries.append(FunctionSummary("<module>", 1, top_level))
    for name, node in functions:
        summaries.append(
            FunctionSummary(name, node.lineno, estimate(node.body, model) + extra[node])
        )
    return Report(filename, findings, summaries)
