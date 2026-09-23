"""A lightweight model of a Python program: scopes, rough types, and loops.

Rules ask the model questions instead of re-deriving the answers themselves:

* ``model.loops_of[node]``: the loops that repeat ``node``, outermost first.
  The iterable of a ``for`` loop is evaluated once, so it isn't inside its own
  loop; a ``while`` condition is re-checked every iteration, so it is.
* ``model.kind_of(name)``: what kind of value a variable holds (``"list"``,
  ``"set"``, ``"dict"``, ``"str"``, ``"tuple"``, ``"deque"``), or ``None``.
* ``model.references(name)``: every use of the same variable.

Type inference is deliberately conservative. A variable only gets a kind when
*every* assignment to it agrees, and rules stay quiet when ``kind_of`` returns
``None``: a missed suggestion is much better than a wrong one.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass, field

from .edits import split_lines

Kind = str
LoopNode = ast.For | ast.AsyncFor | ast.While | ast.comprehension

SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


@dataclass(eq=False)
class Scope:
    """A module, function, lambda or class body, and the kinds of its variables."""

    node: ast.AST
    parent: Scope | None
    kinds: dict[str, set[Kind | None]] = field(default_factory=dict)

    def bind(self, name: str, kind: Kind | None) -> None:
        self.kinds.setdefault(name, set()).add(kind)


class ProgramModel:
    def __init__(self, source: str, filename: str = "<input>") -> None:
        self.source = source
        self.lines = split_lines(source)
        self.tree = ast.parse(source, filename=filename)
        self.parents: dict[ast.AST, ast.AST] = {}
        self.scope_of: dict[ast.AST, Scope] = {}
        self.loops_of: dict[ast.AST, tuple[LoopNode, ...]] = {}
        self._visit(self.tree, Scope(self.tree, None), ())
        self._collect_bindings()

    # --- Questions rules can ask ---------------------------------------------

    def kind_of(self, name: ast.Name) -> Kind | None:
        """The kind of value the variable ``name`` holds, or None if we're not sure."""
        scope = self.binding_scope(name)
        if scope is None:
            return None
        kinds = scope.kinds[name.id]
        return next(iter(kinds)) if len(kinds) == 1 else None

    def binding_scope(self, name: ast.Name) -> Scope | None:
        """The scope where the variable ``name`` is defined, following Python's lookup rules."""
        own = scope = self.scope_of.get(name)
        while scope is not None:
            # Names defined in a class body aren't visible inside its methods.
            visible = scope is own or not isinstance(scope.node, ast.ClassDef)
            if visible and name.id in scope.kinds:
                return scope
            scope = scope.parent
        return None

    def references(self, name: ast.Name) -> list[ast.Name]:
        """Every use of the same variable as ``name``, including ``name`` itself."""
        scope = self.binding_scope(name)
        return [
            node
            for node in self.scope_of
            if isinstance(node, ast.Name)
            and node.id == name.id
            and self.binding_scope(node) is scope
        ]

    def statement_of(self, node: ast.AST) -> ast.stmt:
        """The statement containing ``node`` (``node`` itself if it is a statement)."""
        while not isinstance(node, ast.stmt):
            node = self.parents[node]
        # An `elif` is an If nested in another If's `orelse`; code can't be inserted before it.
        while isinstance(node, ast.If):
            parent = self.parents.get(node)
            if not (isinstance(parent, ast.If) and parent.orelse == [node]):
                break
            node = parent
        return node

    def functions(self) -> Iterator[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
        """Every function in the file with its qualified name, e.g. ``Stack.push``."""
        for node in self.scope_of:
            if isinstance(node, FUNCTION_NODES):
                yield self._qualname(node), node

    def line(self, lineno: int) -> str:
        return self.lines[lineno - 1]

    def segment(self, node: ast.AST) -> str:
        """The source text of ``node``, as the user wrote it."""
        return ast.get_source_segment(self.source, node) or ast.unparse(node)

    def starts_line(self, node: ast.stmt) -> bool:
        """True if only whitespace comes before ``node`` on its line."""
        return not self.line(node.lineno).encode("utf-8")[: node.col_offset].strip()

    # --- Building the model --------------------------------------------------

    def _visit(self, node: ast.AST, scope: Scope, loops: tuple[LoopNode, ...]) -> None:
        self.scope_of[node] = scope
        self.loops_of[node] = loops

        if isinstance(node, SCOPE_NODES):
            # Decorators, base classes and default values are evaluated where the
            # function or class is defined. The body runs in a scope of its own,
            # outside any loop around the definition.
            inner = Scope(node, scope)
            for name, value in ast.iter_fields(node):
                if name in ("args", "body"):
                    self._add_all(node, value, inner, ())
                else:
                    self._add_all(node, value, scope, loops)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            inside = (*loops, node)
            self._add(node, node.iter, scope, loops)
            self._add(node, node.target, scope, inside)
            self._add_all(node, node.body, scope, inside)
            self._add_all(node, node.orelse, scope, loops)
        elif isinstance(node, ast.While):
            inside = (*loops, node)
            self._add(node, node.test, scope, inside)
            self._add_all(node, node.body, scope, inside)
            self._add_all(node, node.orelse, scope, loops)
        elif isinstance(node, COMPREHENSIONS):
            # Each `for` clause is a loop nested inside the previous one.
            inside = loops
            for gen in node.generators:
                self.parents[gen] = node
                self.scope_of[gen] = scope
                self.loops_of[gen] = inside
                self._add(gen, gen.iter, scope, inside)
                inside = (*inside, gen)
                self._add(gen, gen.target, scope, inside)
                self._add_all(gen, gen.ifs, scope, inside)
            elements = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
            self._add_all(node, elements, scope, inside)
        else:
            self._add_all(node, list(ast.iter_child_nodes(node)), scope, loops)

    def _add(self, parent: ast.AST, child: ast.AST, scope: Scope, loops) -> None:
        self.parents[child] = parent
        self._visit(child, scope, loops)

    def _add_all(self, parent: ast.AST, children, scope: Scope, loops) -> None:
        if not isinstance(children, list):
            children = [children]
        for child in children:
            if isinstance(child, ast.AST):
                self._add(parent, child, scope, loops)

    def _collect_bindings(self) -> None:
        for node, scope in self.scope_of.items():
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                parent = self.parents[node]
                if _updates_in_place(node, parent):
                    continue  # `x += y` and `x = x + y` don't change what kind of value x is
                scope.bind(node.id, _assigned_kind(node, parent))
            elif isinstance(node, ast.arg):
                scope.bind(node.arg, kind_from_annotation(node.annotation))
            elif isinstance(node, (*FUNCTION_NODES, ast.ClassDef)):
                scope.bind(node.name, None)
            elif isinstance(node, ast.alias):
                scope.bind((node.asname or node.name).split(".")[0], None)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                for name in node.names:
                    scope.bind(name, None)

    def _qualname(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        parts = [node.name]
        scope = self.scope_of[node]
        while scope.parent is not None:
            parts.append(getattr(scope.node, "name", "<lambda>"))
            scope = scope.parent
        return ".".join(reversed(parts))


def loop_line(loop: LoopNode) -> int:
    # `ast.comprehension` nodes have no position of their own.
    return loop.iter.lineno if isinstance(loop, ast.comprehension) else loop.lineno


def describe_loop(loop: LoopNode) -> str:
    if isinstance(loop, ast.While):
        kind = "while loop"
    elif isinstance(loop, ast.comprehension):
        kind = "comprehension"
    else:
        kind = "for loop"
    return f"{kind} on line {loop_line(loop)}"


# --- Guessing kinds from syntax ----------------------------------------------

_CALL_KINDS = {
    "list": "list",
    "sorted": "list",
    "set": "set",
    "frozenset": "set",
    "dict": "dict",
    "defaultdict": "dict",
    "Counter": "dict",
    "OrderedDict": "dict",
    "str": "str",
    "tuple": "tuple",
    "deque": "deque",
}
_METHOD_KINDS = {
    "split": "list",
    "rsplit": "list",
    "splitlines": "list",
    "join": "str",
    "strip": "str",
    "lower": "str",
    "upper": "str",
    "format": "str",
    # collections.defaultdict(...), collections.Counter(...), ...
    "defaultdict": "dict",
    "Counter": "dict",
    "OrderedDict": "dict",
    "deque": "deque",
}
_ANNOTATION_KINDS = {
    "list": "list",
    "List": "list",
    "set": "set",
    "Set": "set",
    "frozenset": "set",
    "FrozenSet": "set",
    "dict": "dict",
    "Dict": "dict",
    "str": "str",
    "tuple": "tuple",
    "Tuple": "tuple",
    "deque": "deque",
}


def infer_kind(expr: ast.expr | None) -> Kind | None:
    """Guess what kind of value ``expr`` produces, from its syntax alone."""
    if isinstance(expr, (ast.List, ast.ListComp)):
        return "list"
    if isinstance(expr, (ast.Set, ast.SetComp)):
        return "set"
    if isinstance(expr, (ast.Dict, ast.DictComp)):
        return "dict"
    if isinstance(expr, ast.Tuple):
        return "tuple"
    if isinstance(expr, ast.JoinedStr) or (
        isinstance(expr, ast.Constant) and isinstance(expr.value, str)
    ):
        return "str"
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, (ast.Add, ast.Mult)):
        # [0] * n, "-" * width, prefix + "!", ...
        return infer_kind(expr.left) or infer_kind(expr.right)
    if isinstance(expr, ast.Call):
        if isinstance(expr.func, ast.Name):
            return _CALL_KINDS.get(expr.func.id)
        if isinstance(expr.func, ast.Attribute):
            return _METHOD_KINDS.get(expr.func.attr)
    return None


def kind_from_annotation(annotation: ast.expr | None) -> Kind | None:
    if isinstance(annotation, ast.Subscript):  # list[int], Dict[str, int], ...
        annotation = annotation.value
    if isinstance(annotation, ast.Name):
        return _ANNOTATION_KINDS.get(annotation.id)
    if isinstance(annotation, ast.Attribute):  # typing.List, collections.deque
        return _ANNOTATION_KINDS.get(annotation.attr)
    return None


def _updates_in_place(target: ast.Name, parent: ast.AST) -> bool:
    if isinstance(parent, ast.AugAssign):
        return True
    return (
        isinstance(parent, ast.Assign)
        and isinstance(parent.value, ast.BinOp)
        and isinstance(parent.value.left, ast.Name)
        and parent.value.left.id == target.id
    )


def _assigned_kind(target: ast.Name, parent: ast.AST) -> Kind | None:
    if isinstance(parent, ast.Assign) and any(t is target for t in parent.targets):
        return infer_kind(parent.value)
    if isinstance(parent, ast.AnnAssign):
        return kind_from_annotation(parent.annotation) or infer_kind(parent.value)
    if isinstance(parent, ast.NamedExpr):
        return infer_kind(parent.value)
    return None  # loop variables, tuple unpacking, `with ... as x`, ...
