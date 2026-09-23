"""The first item that already appeared earlier in the list, or None.

Pattern: repeated linear search (over a slice) -> set.
"""

EXAMPLES = [([1, 2, 3, 2, 1],), ([1, 2, 3],), ([],)]


def slow(items: list):
    # expect: O(len(items)^2)
    for i, item in enumerate(items):
        if item in items[:i]:
            return item
    return None


def fast(items: list):
    # expect: O(len(items))
    seen = set()
    for item in items:
        if item in seen:
            return item
        seen.add(item)
    return None
