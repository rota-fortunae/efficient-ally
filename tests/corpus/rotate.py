"""Rotate a list left by k positions.

Pattern: repeated array shifting -> slicing.
"""

EXAMPLES = [([1, 2, 3, 4, 5], 2), ([1, 2], 5), ([], 3)]


def slow(items: list, k: int):
    # expect: O(k * len(items))
    if not items:
        return []
    items = list(items)
    for _ in range(k):
        items.append(items.pop(0))
    return items


def fast(items: list, k: int):
    # expect: O(len(items))
    if not items:
        return []
    k %= len(items)
    return items[k:] + items[:k]
