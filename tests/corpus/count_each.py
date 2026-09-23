"""Pair each item with the number of times it appears in the list.

Pattern: repeated linear search (list.count) -> collections.Counter.
"""

from collections import Counter

EXAMPLES = [(["a", "b", "a"],), ([],), ([1, 1, 1],)]


def slow(items: list):
    # expect: O(len(items)^2)
    return [(item, items.count(item)) for item in items]


def fast(items: list):
    # expect: O(len(items))
    counts = Counter(items)
    return [(item, counts[item]) for item in items]
