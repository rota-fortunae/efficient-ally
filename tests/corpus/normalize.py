"""Scale numbers so the largest one becomes 1.0.

Pattern: repeated computation inside a loop -> compute it once, before the loop.
"""

EXAMPLES = [([2, 4, 8],), ([5],), ([],)]


def slow(values: list[float]):
    # expect: O(len(values)^2)
    return [value / max(values) for value in values]


def fast(values: list[float]):
    # expect: O(len(values))
    if not values:
        return []
    largest = max(values)
    return [value / largest for value in values]
