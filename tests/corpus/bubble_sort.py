"""Sort a list of numbers.

Pattern: quadratic sort -> the built-in sorted().
"""

EXAMPLES = [([5, 1, 4, 2, 8],), ([],), ([2, 2, 1],)]


def slow(items: list[int]):
    # expect: O(len(items)^2)
    items = list(items)
    n = len(items)
    for i in range(n):
        for j in range(n - i - 1):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
    return items


def fast(items: list[int]):
    # expect: O(len(items) * log(len(items)))
    return sorted(items)
