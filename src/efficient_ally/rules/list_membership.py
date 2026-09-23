"""`x in some_list` inside a loop: a linear search repeated on every iteration.

Covers "repeated linear search -> set" and "nested membership search -> set"
from the pattern list. The suggested rewrite depends on how the list is used:

1. The list never changes: build a set from it once, before the loop.
2. The list is only assigned and appended to: keep a set in sync with it.
3. Anything else: explain the fix, but don't offer an automatic rewrite.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass, field

from ..complexity import ONE, Complexity, repeat_count
from ..edits import Edit, indentation, replace_span
from ..findings import Finding
from ..model import LoopNode, ProgramModel, describe_loop
from .base import Rule

# Methods that change which items are in a list. (`sort` and `reverse` only
# reorder it, so a set of its items stays correct.)
_CHANGES_CONTENTS = {"append", "extend", "insert", "remove", "pop", "clear"}


class ListMembershipInLoop(Rule):
    id = "list-membership-in-loop"
    title = "Linear search inside a loop"

    def check(self, model: ProgramModel) -> Iterator[Finding]:
        for node in ast.walk(model.tree):
            if not isinstance(node, ast.Compare) or not model.loops_of.get(node):
                continue
            for op, container in zip(node.ops, node.comparators, strict=True):
                if (
                    isinstance(op, (ast.In, ast.NotIn))
                    and isinstance(container, ast.Name)
                    and model.kind_of(container) == "list"
                ):
                    finding = self._report(model, node, container)
                    if finding is not None:
                        yield finding

    def _report(
        self, model: ProgramModel, compare: ast.Compare, container: ast.Name
    ) -> Finding | None:
        name = container.id
        loops = model.loops_of[compare]
        uses = _classify_uses(model, container)
        # A loop that reassigns the list searches a fresh list each time around, so
        # only the loops inside the last reassignment repeat a search of the same items.
        repeating = [
            loop for loop in loops if not any(loop in model.loops_of[b] for b in uses.bindings)
        ]
        if not repeating or repeat_count(repeating).degree == 0:
            return None  # e.g. `for key in ("a", "b"):` only searches a fixed number of times
        outside = repeat_count(loops[: loops.index(repeating[0])])
        runs = repeat_count(loops)
        scan = Complexity.of(f"len({name})")
        explanation = (
            f"`{name}` is a list, so `{model.segment(compare)}` compares against its items one "
            f"at a time, which takes O(len({name})). It runs on every iteration of the "
            f"{describe_loop(loops[-1])}, so in total it costs {runs * scan}."
        )

        if not uses.appends and not uses.other_changes:
            return self.finding(
                compare,
                explanation=explanation,
                suggestion=(
                    f"Build a set from `{name}` once, before the loop, and test membership "
                    "against the set instead; a set lookup takes O(1) on average. If "
                    f"`{name}` never needs to be a list, make it a set from the start."
                ),
                current=runs * scan,
                improved=runs + outside * scan,
                edits=_build_set_once(model, container, repeating[0]),
            )

        if not uses.other_changes and uses.bindings:
            also = f", and add to it wherever you append to `{name}`" if uses.appends else ""
            improved = runs
            for binding in uses.bindings:
                build = ONE if _is_empty_list(binding.value) else scan
                improved = improved + repeat_count(model.loops_of[binding]) * build
            return self.finding(
                compare,
                explanation=explanation,
                suggestion=(
                    f"Keep a set with the same items as `{name}`: create it wherever `{name}` "
                    f"is assigned{also}. Then test membership against the set, which takes "
                    f"O(1) on average. If you don't need the list's order or duplicates, you "
                    f"can replace `{name}` with the set entirely."
                ),
                current=runs * scan,
                improved=improved,
                edits=_mirror_in_set(model, container, uses),
            )

        return self.finding(
            compare,
            explanation=explanation,
            suggestion=(
                f"Test membership against a set instead of the list `{name}`. `{name}` is "
                "changed in ways that are hard to mirror automatically, so consider switching "
                "it to a set (or a dict, if you need insertion order) and updating the code "
                "that modifies it."
            ),
            current=runs * scan,
            improved=runs,
        )


@dataclass
class _Uses:
    """How a list variable is used, as far as switching to a set is concerned."""

    bindings: list[ast.Assign | ast.AnnAssign] = field(default_factory=list)  # `name = ...`
    appends: list[ast.Call] = field(default_factory=list)  # `name.append(x)`
    other_changes: bool = False  # anything else that changes which items are in the list


def _classify_uses(model: ProgramModel, container: ast.Name) -> _Uses:
    uses = _Uses()
    for ref in model.references(container):
        parent = model.parents[ref]
        if isinstance(ref.ctx, ast.Store):
            if _is_simple_binding(ref, parent):
                uses.bindings.append(parent)
            else:
                uses.other_changes = True  # `+=`, loop variable, tuple unpacking, ...
        elif isinstance(ref.ctx, ast.Del):
            uses.other_changes = True
        elif isinstance(parent, ast.Subscript) and not isinstance(parent.ctx, ast.Load):
            uses.other_changes = True  # `name[i] = x` or `del name[i]`
        elif isinstance(parent, ast.Attribute) and parent.attr in _CHANGES_CONTENTS:
            call = model.parents.get(parent)
            if parent.attr == "append" and isinstance(call, ast.Call) and call.func is parent:
                uses.appends.append(call)
            else:
                uses.other_changes = True
    return uses


def _is_simple_binding(ref: ast.Name, parent: ast.AST) -> bool:
    """`name = <expr>`, where the new value isn't built from the old one (`name = name + [x]`)."""
    if isinstance(parent, ast.Assign) and any(t is ref for t in parent.targets):
        value = parent.value
    elif isinstance(parent, ast.AnnAssign) and parent.value is not None:
        value = parent.value
    else:
        return False
    return not any(isinstance(n, ast.Name) and n.id == ref.id for n in ast.walk(value))


def _is_empty_list(value: ast.expr | None) -> bool:
    if isinstance(value, ast.List):
        return not value.elts
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "list"
        and not value.args
        and not value.keywords
    )


def _build_set_once(
    model: ProgramModel, container: ast.Name, outer_loop: LoopNode
) -> list[Edit] | None:
    stmt = model.statement_of(outer_loop)
    if not model.starts_line(stmt):
        return None
    set_name = f"{container.id}_set"
    indent = indentation(model.line(stmt.lineno))
    return [
        Edit(stmt.lineno, "insert_before", f"{indent}{set_name} = set({container.id})"),
        _rename(model, container, set_name),
    ]


def _mirror_in_set(model: ProgramModel, container: ast.Name, uses: _Uses) -> list[Edit] | None:
    name, set_name = container.id, f"{container.id}_set"
    edits = []
    for stmt in uses.bindings:
        init = "set()" if _is_empty_list(stmt.value) else f"set({name})"
        edits.append(_insert_after(model, stmt, f"{set_name} = {init}"))
    for call in uses.appends:
        stmt = model.parents.get(call)
        if (
            not isinstance(stmt, ast.Expr)
            or len(call.args) != 1
            or call.keywords
            or isinstance(call.args[0], ast.Starred)
        ):
            return None
        edits.append(_insert_after(model, stmt, f"{set_name}.add({model.segment(call.args[0])})"))
    if None in edits:
        return None
    edits.append(_rename(model, container, set_name))
    return edits


def _insert_after(model: ProgramModel, stmt: ast.stmt, code: str) -> Edit | None:
    """An edit adding ``code`` on a new line after ``stmt``, at the same indentation."""
    if not model.starts_line(stmt) or "\n" in code:
        return None
    return Edit(stmt.end_lineno, "insert_after", indentation(model.line(stmt.lineno)) + code)


def _rename(model: ProgramModel, name: ast.Name, new_name: str) -> Edit:
    line = model.line(name.lineno)
    return Edit(
        name.lineno, "replace", replace_span(line, name.col_offset, name.end_col_offset, new_name)
    )
