import textwrap

from efficient_ally import Finding, analyze
from efficient_ally.edits import apply_edits


def findings(source: str, rule: str) -> tuple[str, list[Finding]]:
    """Dedent ``source`` and return it with the findings ``rule`` reports for it."""
    source = textwrap.dedent(source)
    return source, [f for f in analyze(source).findings if f.rule == rule]


def rewritten(source: str, finding: Finding) -> str:
    assert finding.edits, "expected the finding to include a rewrite"
    return apply_edits(source, finding.edits)


def run(source: str, function: str, *args):
    """Execute ``source`` and call ``function`` from it. Used to check that rewrites
    behave exactly like the original code."""
    namespace: dict = {}
    exec(source, namespace)
    return namespace[function](*args)
