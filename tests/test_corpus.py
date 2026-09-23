"""Measures the analyzer against the hand-labeled programs in tests/corpus/.

Run `pytest tests/test_corpus.py` for the checks below, or
`python tests/test_corpus.py` for a scoreboard of what the estimator gets right.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest

from efficient_ally import Finding, analyze
from efficient_ally.complexity import Complexity

CORPUS = Path(__file__).parent / "corpus"
PROGRAMS = sorted(CORPUS.glob("*.py"))

# Functions the estimator gets wrong today, and why: the to-do list for making
# it better. Each reason starts with the kind of fix it needs, so the scoreboard
# can show which fix would help the most functions. Tests for these are
# expected to fail; when one starts passing, pytest reports an XPASS failure so
# you remember to delete its entry.
KNOWN_MISSES = {
    "binary_search.fast": "while loops: `lo`/`hi` halve the range each time -> log",
    "bubble_sort.slow": "aliases + loop bounds: n = len(items); n - i - 1 <= n",
    "concat_lists.slow": "collection sizes: `evens` grows to at most len(nums)",
    "dedupe.slow": "collection sizes: `seen` grows to at most len(items)",
    "edit_distance.slow": "recursion: three calls on shorter strings",
    "fib.slow": "recursion: f(n - 1) + f(n - 2)",
    "grid_paths.slow": "recursion: two calls, each shrinking one argument",
    "grid_paths.fast": "recursion: @cache means each (r, c) is computed once",
    "group_anagrams.group": "collection sizes: `groups` has at most len(words) entries",
    "k_smallest.slow": "collection sizes + loop bounds: len(remaining) = len(nums); min(k, x) <= k",
    "matrix_multiply.multiply": "aliases: n = len(a)",
    "min_gap.fast": "collection sizes: `ordered` and `gaps` are about as long as nums",
    "pascal_triangle.triangle": "loop bounds: j < i < n",
    "power.fast": "while loops: exponent halves each time -> log",
    "prepend_all.slow": "collection sizes: `result` grows to len(items)",
    "prepend_all.fast": "collection sizes: `result` grows to len(items)",
    "print_queue.slow": "while loops + collection sizes: runs until `queue` (from jobs) is empty",
    "print_queue.fast": "while loops + collection sizes: runs until `queue` (from jobs) is empty",
    "render_grid.fast": "collection sizes: `lines` gets one entry per row, so height",
    "repeated_min.slow": "while loops + collection sizes: runs until `remaining` is empty",
    "repeated_min.fast": "collection sizes: `heap` is a copy of nums",
    "reverse_string.slow": "string building: prepending (`result = char + result`) isn't seen",
    "two_sum.slow": "loop bounds: i < j < len(nums)",
}


@dataclass
class Case:
    """A corpus function with an `# expect:` comment."""

    program: str
    function: str
    expected: Complexity
    actual: Complexity
    findings: list[Finding]

    @property
    def id(self) -> str:
        return f"{self.program}.{self.function}"

    @property
    def correct(self) -> bool:
        return self.actual == self.expected


_EXPECT = re.compile(r"#\s*expect:\s*(O\(.*\))\s*$")


def load_cases(path: Path) -> list[Case]:
    source = path.read_text(encoding="utf-8")
    report = analyze(source, str(path))
    estimates = {summary.name: summary.complexity for summary in report.functions}
    lines = source.splitlines()
    cases = []
    for node in ast.parse(source).body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for line in lines[node.lineno - 1 : node.end_lineno]:
            match = _EXPECT.search(line)
            if match:
                findings = [f for f in report.findings if node.lineno <= f.line <= node.end_lineno]
                expected = Complexity.parse(match.group(1))
                cases.append(Case(path.stem, node.name, expected, estimates[node.name], findings))
                break
    return cases


CASES = [case for path in PROGRAMS for case in load_cases(path)]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"corpus_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- Tests -------------------------------------------------------------------


def _as_param(case: Case):
    marks = []
    if case.id in KNOWN_MISSES:
        marks.append(pytest.mark.xfail(reason=KNOWN_MISSES[case.id], strict=True))
    return pytest.param(case, id=case.id, marks=marks)


@pytest.mark.parametrize("case", [_as_param(case) for case in CASES])
def test_estimate_matches_expectation(case: Case):
    assert str(case.actual) == str(case.expected)


def test_known_misses_name_real_functions():
    assert set(KNOWN_MISSES) <= {case.id for case in CASES}


@pytest.mark.parametrize("case", [pytest.param(c, id=c.id) for c in CASES if c.function != "slow"])
def test_only_slow_versions_are_flagged(case: Case):
    assert [f"{f.rule} (line {f.line})" for f in case.findings] == []


@pytest.mark.parametrize("path", PROGRAMS, ids=lambda path: path.stem)
def test_program_is_well_formed_and_versions_agree(path: Path):
    names = sorted(case.function for case in CASES if case.program == path.stem)
    assert names, "no `# expect:` comments found"
    module = _load_module(path)
    examples = getattr(module, "EXAMPLES", None)
    assert examples, "every program needs EXAMPLES"
    if "slow" in names or "fast" in names:
        assert {"slow", "fast"} <= set(names), "slow and fast versions come in pairs"
    for args in examples:
        results = {name: getattr(module, name)(*copy.deepcopy(args)) for name in names}
        first = next(iter(results.values()))
        assert all(r == first for r in results.values()), f"versions disagree: {results}"


# --- Scoreboard --------------------------------------------------------------


def scoreboard() -> str:
    right = [case for case in CASES if case.correct]
    programs = sorted({case.program for case in CASES})
    fully_right = [p for p in programs if all(case.correct for case in CASES if case.program == p)]
    slow = [case for case in CASES if case.function == "slow"]
    flagged = [case for case in slow if case.findings]
    false_alarms = [case for case in CASES if case.function != "slow" and case.findings]

    out = [
        f"Estimator: {len(right)}/{len(CASES)} functions right ({len(right) / len(CASES):.0%}); "
        f"{len(fully_right)}/{len(programs)} programs entirely right",
        f"Rules: flag {len(flagged)}/{len(slow)} slow versions; "
        f"{len(false_alarms)} false alarms on fast or clean code",
        "",
    ]
    id_width = max(len(case.id) for case in CASES)
    expected_width = max(len(str(case.expected)) for case in CASES)
    for case in CASES:
        status = "ok  " if case.correct else "MISS"
        rules = sorted({f.rule for f in case.findings})
        out.append(
            f"{status}  {case.id:<{id_width}}  expect {str(case.expected):<{expected_width}}"
            f"  got {case.actual}" + (f"  [{', '.join(rules)}]" if rules else "")
        )

    fixes = Counter(
        fix.strip() for reason in KNOWN_MISSES.values() for fix in reason.split(":")[0].split("+")
    )
    if fixes:
        out += ["", "Misses by the fix they need:"]
        out += [f"  {count:>3}  {fix}" for fix, count in fixes.most_common()]
    return "\n".join(out)


if __name__ == "__main__":
    print(scoreboard())
