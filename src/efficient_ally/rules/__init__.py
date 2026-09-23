"""All pattern detectors. To add one, subclass `Rule` and list it in `ALL_RULES`."""

from .base import Rule
from .list_membership import ListMembershipInLoop
from .string_concat import StringConcatInLoop

ALL_RULES: list[Rule] = [
    ListMembershipInLoop(),
    StringConcatInLoop(),
]

__all__ = ["ALL_RULES", "Rule"]
