"""Symbolic big-O values, and an estimator that derives them from loop structure.

A ``Complexity`` is a sum of terms, and each term is a sorted tuple of factors:
``("len(a)", "len(a)", "n")`` means len(a)^2 * n, and the empty tuple is the
constant term. Factors stay symbolic (instead of calling everything ``n``) so a
report can say *which* input a cost depends on.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .model import COMPREHENSIONS, LoopNode, ProgramModel

Term = tuple[str, ...]

# Factor for a loop whose iteration count we can't work out (most while loops).
UNKNOWN = "?"


@dataclass(frozen=True)
class Complexity:
    terms: frozenset[Term]

    @classmethod
    def of(cls, *factors: str) -> Complexity:
        """A single term: ``Complexity.of("n", "m")`` is O(n * m), ``Complexity.of()`` is O(1)."""
        return cls(frozenset({tuple(sorted(factors))}))

    def __add__(self, other: Complexity) -> Complexity:
        return Complexity(_simplify(self.terms | other.terms))

    def __mul__(self, other: Complexity) -> Complexity:
        return Complexity(_simplify(tuple(sorted(a + b)) for a in self.terms for b in other.terms))

    @property
    def degree(self) -> int:
        """Most factors in any term: 0 for O(1), 1 for O(n), 2 for O(n^2) or O(n * m)."""
        return max(len(term) for term in self.terms)

    def __str__(self) -> str:
        terms = sorted(self.terms, key=lambda term: (-len(term), term))
        return "O(" + " + ".join(_format_term(term) for term in terms) + ")"


ONE = Complexity.of()


def _format_term(term: Term) -> str:
    if not term:
        return "1"
    return " * ".join(f if n == 1 else f"{f}^{n}" for f, n in Counter(term).items())


def _simplify(terms: Iterable[Term]) -> frozenset[Term]:
    """Drop terms that grow no faster than another term: O(n + n * m) is O(n * m)."""
    pool = set(terms)
    return frozenset(t for t in pool if not any(t != u and _divides(t, u) for u in pool))


def _divides(small: Term, big: Term) -> bool:
    """True if every factor of ``small`` appears in ``big`` at least as many times."""
    available = Counter(big)
    return all(available[f] >= n for f, n in Counter(small).items())


# --- How many times does a loop run? -----------------------------------------


def iteration_count(loop: LoopNode) -> Complexity:
    """How many times the body of ``loop`` runs, in terms of the loop's inputs."""
    if isinstance(loop, ast.While):
        return Complexity.of(UNKNOWN)  # TODO(month 2): bounds for simple counter loops
    return _length_of(loop.iter)


def repeat_count(loops: Sequence[LoopNode]) -> Complexity:
    """How many times code nested inside all of ``loops`` runs."""
    total = ONE
    for loop in loops:
        total = total * iteration_count(loop)
    return total


# Calls whose result has (at most) as many items as their first argument.
_SAME_LENGTH = {
    "enumerate",
    "reversed",
    "sorted",
    "list",
    "tuple",
    "set",
    "frozenset",
    "iter",
    "zip",
}


def _length_of(expr: ast.expr) -> Complexity:
    """Number of items produced by iterating over ``expr``."""
    if isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
        if not any(isinstance(e, ast.Starred) for e in expr.elts):
            return ONE
    elif isinstance(expr, ast.Constant):
        return ONE
    elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.args:
        if expr.func.id == "range":
            return _range_length(expr.args)
        if expr.func.id in _SAME_LENGTH:
            return _length_of(expr.args[0])
    elif (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Attribute)
        and expr.func.attr in ("items", "keys", "values")
        and not expr.args
    ):
        return _length_of(expr.func.value)
    return Complexity.of(f"len({ast.unparse(expr)})")


def _range_length(args: list[ast.expr]) -> Complexity:
    # For big-O purposes the stop value bounds the count; the start value and a
    # constant step only change constant factors.
    stop = _drop_constants(args[0] if len(args) == 1 else args[1])
    if isinstance(stop, ast.Constant):
        return ONE
    return Complexity.of(ast.unparse(stop))


def _drop_constants(expr: ast.expr) -> ast.expr:
    """``n + 1``, ``n - 1``, ``2 * n`` and ``n // 2`` all grow like ``n``."""
    scaling = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv)
    while isinstance(expr, ast.BinOp) and isinstance(expr.op, scaling):
        if isinstance(expr.right, ast.Constant):
            expr = expr.left
        elif isinstance(expr.left, ast.Constant) and isinstance(expr.op, (ast.Add, ast.Mult)):
            expr = expr.right
        else:
            break
    return expr


# --- Estimating the cost of a block of code ----------------------------------


def estimate(body: list[ast.stmt], model: ProgramModel) -> Complexity:
    """Estimate the running time of ``body`` from its loop structure.

    A loop multiplies the cost of its body by its iteration count. Everything
    else is O(1), apart from the few operations in ``_operation_cost``. Calls to
    other functions also count as O(1) for now (see ROADMAP.md, month 2).
    """
    return _block_cost(body, model)


def _block_cost(stmts: list[ast.stmt], model: ProgramModel) -> Complexity:
    total = ONE
    for stmt in stmts:
        total = total + _cost(stmt, model)
    return total


def _cost(node: ast.AST, model: ProgramModel) -> Complexity:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
        return ONE  # defining a function is cheap; its body only runs when it's called
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return (
            _cost(node.iter, model)
            + iteration_count(node) * _block_cost(node.body, model)
            + _block_cost(node.orelse, model)
        )
    if isinstance(node, ast.While):
        body = _cost(node.test, model) + _block_cost(node.body, model)
        return iteration_count(node) * body + _block_cost(node.orelse, model)
    if isinstance(node, COMPREHENSIONS):
        return _comprehension_cost(node, model)
    total = _operation_cost(node, model)
    for child in ast.iter_child_nodes(node):
        total = total + _cost(child, model)
    return total


def _comprehension_cost(node: ast.expr, model: ProgramModel) -> Complexity:
    if isinstance(node, ast.DictComp):
        inner = _cost(node.key, model) + _cost(node.value, model)
    else:
        inner = _cost(node.elt, model)
    # Work outwards: each `for` clause repeats its conditions and everything after it.
    for gen in reversed(node.generators):
        per_item = inner
        for condition in gen.ifs:
            per_item = per_item + _cost(condition, model)
        inner = _cost(gen.iter, model) + iteration_count(gen) * per_item
    return inner


# List methods whose running time grows with the length of the list.
_LINEAR_LIST_METHODS = {"index", "count", "remove", "insert", "copy", "reverse"}


def _operation_cost(node: ast.AST, model: ProgramModel) -> Complexity:
    """The cost of ``node`` itself, not counting its children."""
    if isinstance(node, ast.Compare):
        cost = ONE
        for op, right in zip(node.ops, node.comparators, strict=True):
            if (
                isinstance(op, (ast.In, ast.NotIn))
                and isinstance(right, ast.Name)
                and model.kind_of(right) == "list"
            ):
                cost = cost + Complexity.of(f"len({right.id})")
        return cost
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and model.kind_of(node.func.value) == "list"
    ):
        method, name = node.func.attr, node.func.value.id
        pops_front = (
            method == "pop"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == 0
        )
        if method in _LINEAR_LIST_METHODS or pops_front:
            return Complexity.of(f"len({name})")
    return ONE
