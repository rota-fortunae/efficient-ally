"""Symbolic big-O values, and an estimator that derives them from loop structure.

A ``Complexity`` is a sum of terms, and each term is a sorted tuple of factors:
``("len(a)", "len(a)", "n")`` means len(a)^2 * n, and the empty tuple is the
constant term. Factors stay symbolic (instead of calling everything ``n``) so a
report can say *which* input a cost depends on. A factor ``log(x)`` grows more
slowly than ``x``, so O(n * log(n) + n^2) simplifies to O(n^2).
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .model import COMPREHENSIONS, LoopNode, ProgramModel, infer_kind

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

    @classmethod
    def parse(cls, text: str) -> Complexity:
        """The inverse of ``str()``: ``Complexity.parse("O(len(a) * n^2 + m)")``."""
        text = text.strip()
        if not (text.startswith("O(") and text.endswith(")")):
            raise ValueError(f"not a big-O expression: {text!r}")
        total = None
        for term in _split_top_level(text[2:-1], " + "):
            factors = []
            for factor in _split_top_level(term.strip(), " * "):
                base, _, power = factor.rpartition("^")
                count = 1
                if base and power.isdigit():  # "n^2"; but "2^n" is a single factor
                    factor, count = base, int(power)
                if _is_wrapped(factor):
                    factor = factor[1:-1]
                if factor != "1":
                    factors += [factor] * count
            total = cls.of(*factors) if total is None else total + cls.of(*factors)
        return total

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
    return " * ".join(_format_factor(f, n) for f, n in Counter(term).items())


def _format_factor(factor: str, power: int) -> str:
    if len(_split_top_level(factor, " ")) > 1:
        factor = f"({factor})"  # so `n * (n - i)` doesn't print as `n * n - i`
    return factor if power == 1 else f"{factor}^{power}"


def _split_top_level(text: str, separator: str) -> list[str]:
    """Split ``text`` on ``separator``, except inside brackets."""
    parts, depth, start, i = [], 0, 0, 0
    while i < len(text):
        if text[i] in "([{":
            depth += 1
        elif text[i] in ")]}":
            depth -= 1
        elif depth == 0 and text.startswith(separator, i):
            parts.append(text[start:i])
            i += len(separator)
            start = i
            continue
        i += 1
    parts.append(text[start:])
    return parts


def _is_wrapped(text: str) -> bool:
    """True for ``(n - i)``, but not ``(a) - (b)``."""
    if not (text.startswith("(") and text.endswith(")")):
        return False
    depth = 0
    for i, char in enumerate(text):
        depth += (char in "([{") - (char in ")]}")
        if depth == 0 and i < len(text) - 1:
            return False
    return True


def _simplify(terms: Iterable[Term]) -> frozenset[Term]:
    """Drop terms that grow no faster than another term: O(n + n * m) is O(n * m)."""
    pool = set(terms)
    return frozenset(t for t in pool if not any(t != u and _divides(t, u) for u in pool))


def _divides(small: Term, big: Term) -> bool:
    """True if ``small`` grows no faster than ``big``.

    Each factor of ``small`` must be matched by a different factor of ``big`` that
    grows at least as fast: ``n`` only by ``n``, but ``log(n)`` by ``log(n)`` or ``n``.
    """
    available = Counter(big)
    logs = []
    for factor in small:
        if _log_argument(factor) is not None:
            logs.append(factor)  # match these last, after exact matches are taken
        elif available[factor]:
            available[factor] -= 1
        else:
            return False
    for factor in logs:
        match = factor if available[factor] else _log_argument(factor)
        if not available[match]:
            return False
        available[match] -= 1
    return True


def _log_argument(factor: str) -> str | None:
    """``"n"`` for ``"log(n)"``; None if ``factor`` isn't a logarithm."""
    if factor.startswith("log(") and _is_wrapped(factor[3:]):
        return factor[4:-1]
    return None


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
    "dict",
    "Counter",
    "OrderedDict",
    "deque",
    "iter",
    "zip",
}
# Methods whose result has (at most) as many items as the object they're called on.
# (`text.split()` can't produce more words than `text` has characters.)
_SAME_LENGTH_METHODS = {"items", "keys", "values", "copy", "split", "rsplit", "splitlines"}


def _length_of(expr: ast.expr) -> Complexity:
    """Number of items in ``expr``, or produced by iterating over it."""
    if isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
        if not any(isinstance(e, ast.Starred) for e in expr.elts):
            return ONE
    elif isinstance(expr, (ast.Constant, ast.JoinedStr)):
        return ONE  # a literal, or an f-string (assumed short)
    elif isinstance(expr, ast.Subscript) and isinstance(expr.slice, ast.Slice):
        return _slice_length(expr)
    elif isinstance(expr, COMPREHENSIONS):
        return repeat_count(expr.generators)
    elif isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        return _length_of(expr.left) + _length_of(expr.right)  # a + b, for lists
    elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.args:
        name, args = expr.func.id, expr.args
        if name == "range":
            return _range_length(args)
        if name in _SAME_LENGTH:
            return _length_of(args[0])
        if name in ("map", "filter") and len(args) >= 2:
            return _length_of(args[1])
    elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute):
        method = expr.func.attr
        if method in _SAME_LENGTH_METHODS:
            return _length_of(expr.func.value)
        if method == "join" and len(expr.args) == 1:
            return _length_of(expr.args[0])  # treating each piece as short
    return Complexity.of(f"len({ast.unparse(expr)})")


def _slice_length(node: ast.Subscript) -> Complexity:
    """Constant for ``x[:3]`` or ``x[-3:]``; otherwise up to the length of ``x``."""
    lower, upper = _int_constant(node.slice.lower), _int_constant(node.slice.upper)
    if upper is not None and upper >= 0:
        return ONE
    if node.slice.upper is None and lower is not None and lower < 0:
        return ONE
    return _length_of(node.value)


def _range_length(args: list[ast.expr]) -> Complexity:
    # For big-O purposes the stop value bounds the count; the start value and a
    # constant step only change constant factors.
    return _count(args[0] if len(args) == 1 else args[1])


def _count(expr: ast.expr) -> Complexity:
    """How big the number ``expr`` is, for big-O purposes: ``n + 1`` is O(n)."""
    expr = _drop_constants(expr)
    if isinstance(expr, ast.Constant):
        return ONE
    return Complexity.of(ast.unparse(expr))


def _int_constant(expr: ast.expr | None) -> int | None:
    """The value of an integer literal like ``3`` or ``-3``; None for anything else."""
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
        value = _int_constant(expr.operand)
        return None if value is None else -value
    if isinstance(expr, ast.Constant) and type(expr.value) is int:
        return expr.value
    return None


def _log(size: Complexity) -> Complexity:
    """O(log(size)). Uses log(n * m) = log(n) + log(m); the log of a constant is O(1)."""
    total = ONE
    for factor in sorted({f for term in size.terms for f in term}):
        total = total + Complexity.of(f"log({factor})")
    return total


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

    A loop multiplies the cost of its body by its iteration count. Built-ins with
    a known cost (sorting, slicing, `max`, `set(...)`, `heapq`, ...) are listed in
    ``_operation_cost``; everything else is O(1). That includes calls to the
    program's own functions, for now (see ROADMAP.md, month 2).
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


# Built-in functions that go through their whole (single) argument.
_LINEAR_BUILTINS = {
    "list",
    "tuple",
    "set",
    "frozenset",
    "dict",
    "Counter",
    "OrderedDict",
    "deque",
    "min",
    "max",
    "sum",
    "any",
    "all",
}
# Modules whose functions are called as `module.function(...)`.
_MODULES = {"heapq", "bisect", "collections"}
_HEAP_OPERATIONS = {"heappush", "heappop", "heappushpop", "heapreplace"}  # O(log n)
_BISECT_SEARCHES = {"bisect", "bisect_left", "bisect_right"}  # O(log n)
_BISECT_INSERTS = {"insort", "insort_left", "insort_right"}  # O(n): shifts items over

# Methods whose running time grows with the length of the list or string.
_LINEAR_LIST_METHODS = {"index", "count", "remove", "insert", "copy", "reverse"}
_LINEAR_STR_METHODS = {
    "count",
    "find",
    "index",
    "replace",
    "split",
    "rsplit",
    "lower",
    "upper",
    "strip",
}


def _operation_cost(node: ast.AST, model: ProgramModel) -> Complexity:
    """The cost of ``node`` itself, not counting its children."""
    if isinstance(node, ast.Compare):
        cost = ONE
        for op, right in zip(node.ops, node.comparators, strict=True):
            if isinstance(op, (ast.In, ast.NotIn)) and _kind(right, model) == "list":
                cost = cost + _length_of(right)  # checks the items one by one
        return cost
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
        return _slice_length(node)  # slicing copies the items
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        if {_kind(node.left, model), _kind(node.right, model)} & {"list", "tuple"}:
            return _length_of(node.left) + _length_of(node.right)  # builds a new list
        return ONE
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            return _function_cost(func.id, node.args)
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id in _MODULES:
                return _function_cost(func.attr, node.args)
            return _method_cost(func.attr, func.value, node.args, model)
    return ONE


def _function_cost(name: str, args: list[ast.expr]) -> Complexity:
    if not args:
        return ONE
    if name in ("nsmallest", "nlargest") and len(args) >= 2:
        return _length_of(args[1]) * _log(_count(args[0]))  # heapq.nsmallest(k, items)
    size = _length_of(args[0])
    if name == "sorted":
        return size * _log(size)
    if name == "heapify" or name in _BISECT_INSERTS:
        return size
    if name in _HEAP_OPERATIONS or name in _BISECT_SEARCHES:
        return _log(size)
    if name in _LINEAR_BUILTINS and len(args) == 1:  # max(items), but not max(a, b)
        return size
    return ONE


def _method_cost(
    method: str, receiver: ast.expr, args: list[ast.expr], model: ProgramModel
) -> Complexity:
    if method == "join" and len(args) == 1:
        return _length_of(args[0])
    kind = _kind(receiver, model)
    size = _length_of(receiver)
    if kind == "list":
        if method == "sort":
            return size * _log(size)
        pops_front = method == "pop" and bool(args) and _int_constant(args[0]) == 0
        if method in _LINEAR_LIST_METHODS or pops_front:
            return size
    if kind == "str" and method in _LINEAR_STR_METHODS:
        return size
    return ONE


def _kind(expr: ast.expr, model: ProgramModel) -> str | None:
    """Like ``model.kind_of``, but for any expression: a slice of a list is a list."""
    if isinstance(expr, ast.Name):
        return model.kind_of(expr)
    if isinstance(expr, ast.Subscript) and isinstance(expr.slice, ast.Slice):
        return _kind(expr.value, model)
    return infer_kind(expr)
