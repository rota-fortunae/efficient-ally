"""Items of `a` that also appear in `b`, in the order they appear in `a`.

Pattern: nested membership search -> set.
"""

EXAMPLES = [([1, 2, 3, 4], [4, 2, 9]), ([], [1]), ([1, 1], [1])]


def slow(a: list, b: list):
    # expect: O(len(a) * len(b))
    return [x for x in a if x in b]


def fast(a: list, b: list):
    # expect: O(len(a) + len(b))
    b_items = set(b)
    return [x for x in a if x in b_items]
