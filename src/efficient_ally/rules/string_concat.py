"""Building up a string with `s += piece` (or `s = s + piece`) inside a loop."""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterator

from ..complexity import repeat_count
from ..edits import Edit, indentation, replace_span
from ..findings import Finding
from ..model import LoopNode, ProgramModel, describe_loop
from .base import Rule


class StringConcatInLoop(Rule):
    id = "string-concat-in-loop"
    title = "String built up piece by piece inside a loop"

    def check(self, model: ProgramModel) -> Iterator[Finding]:
        by_variable = defaultdict(list)
        for node in ast.walk(model.tree):
            target = _concat_target(node)
            if target is not None and model.loops_of.get(node) and model.kind_of(target) == "str":
                by_variable[model.binding_scope(target), target.id].append(node)
        for statements in by_variable.values():
            yield from self._check_variable(model, statements)

    def _check_variable(self, model: ProgramModel, statements: list[ast.stmt]) -> Iterator[Finding]:
        target = _concat_target(statements[0])
        refs = model.references(target)
        owned = {id(name) for stmt in statements for name in _pattern_names(stmt)}
        # Other assignments (like `s = ""`) start the string over, so a loop that
        # contains one doesn't make the string keep growing.
        restarts = [r for r in refs if isinstance(r.ctx, ast.Store) and id(r) not in owned]
        by_loop = defaultdict(list)
        for stmt in sorted(statements, key=lambda s: (s.lineno, s.col_offset)):
            growing = [
                loop
                for loop in model.loops_of[stmt]
                if not any(loop in model.loops_of[r] for r in restarts)
            ]
            if repeat_count(growing).degree > 0:  # growing a fixed number of times is fine
                by_loop[growing[0]].append(stmt)
        for outer, group in by_loop.items():
            yield self._report(model, target.id, outer, group, refs, owned)

    def _report(self, model, name, outer, group, refs, owned) -> Finding:
        loops = max((model.loops_of[stmt] for stmt in group), key=len)
        start = loops.index(outer)
        before, growing = repeat_count(loops[:start]), repeat_count(loops[start:])
        current = before * growing * growing
        return self.finding(
            group[0],
            explanation=(
                f"Python strings can't be changed in place, so each time `{name}` grows, a new "
                "string is made and everything built so far is copied into it. Over the "
                f"{describe_loop(outer)} the copying adds up to {current} (counting characters, "
                "for short pieces). CPython can sometimes extend a string in place, but PEP 8 "
                "warns not to rely on that: it isn't guaranteed, and other Python "
                "implementations don't do it."
            ),
            suggestion=(
                "Collect the pieces in a list and join them once after the loop with "
                '`"".join(...)`, so each character is copied only once.'
            ),
            current=current,
            improved=before * growing,
            edits=_join_edits(model, name, outer, group, refs, owned),
        )


def _join_edits(model, name, outer: LoopNode, group, refs, owned) -> list[Edit] | None:
    # The rewrite is only safe if nothing inside the loop reads or resets the
    # string while it's being built.
    if any(outer in model.loops_of[r] and id(r) not in owned for r in refs):
        return None
    lines = [stmt.lineno for stmt in group]
    if any(stmt.lineno != stmt.end_lineno for stmt in group) or len(set(lines)) != len(lines):
        return None
    parts = f"{name}_parts"
    indent = indentation(model.line(outer.lineno))
    edits = [Edit(outer.lineno, "insert_before", f"{indent}{parts} = [{name}]")]
    for stmt in group:
        line = model.line(stmt.lineno)
        piece = model.segment(_appended_piece(stmt))
        new_line = replace_span(
            line, stmt.col_offset, stmt.end_col_offset, f"{parts}.append({piece})"
        )
        edits.append(Edit(stmt.lineno, "replace", new_line))
    edits.append(Edit(outer.end_lineno, "insert_after", f'{indent}{name} = "".join({parts})'))
    return edits


def _concat_target(node: ast.AST) -> ast.Name | None:
    """`s` in `s += x` or `s = s + x`; None for anything else."""
    if (
        isinstance(node, ast.AugAssign)
        and isinstance(node.op, ast.Add)
        and isinstance(node.target, ast.Name)
    ):
        return node.target
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.BinOp)
        and isinstance(node.value.op, ast.Add)
        and isinstance(node.value.left, ast.Name)
        and node.value.left.id == node.targets[0].id
    ):
        return node.targets[0]
    return None


def _appended_piece(stmt: ast.AugAssign | ast.Assign) -> ast.expr:
    return stmt.value if isinstance(stmt, ast.AugAssign) else stmt.value.right


def _pattern_names(stmt: ast.AugAssign | ast.Assign) -> list[ast.Name]:
    if isinstance(stmt, ast.AugAssign):
        return [stmt.target]
    return [stmt.targets[0], stmt.value.left]
