"""The interface every pattern detector implements."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from typing import Any, ClassVar

from ..findings import Finding
from ..model import ProgramModel


class Rule:
    """Detects one kind of inefficient pattern.

    Subclasses set ``id`` and ``title``, implement ``check``, and get listed in
    ``ALL_RULES`` in ``rules/__init__.py``. Only yield a finding when you're
    confident it's real (see the docstring at the top of ``model.py``).
    """

    id: ClassVar[str]
    title: ClassVar[str]

    def check(self, model: ProgramModel) -> Iterator[Finding]:
        raise NotImplementedError

    def finding(self, node: ast.expr | ast.stmt, **details: Any) -> Finding:
        """A finding from this rule, located at ``node``."""
        return Finding(
            rule=self.id,
            title=self.title,
            line=node.lineno,
            col=node.col_offset,
            end_line=node.end_lineno or node.lineno,
            **details,
        )
