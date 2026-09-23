"""Remove duplicates from a list, keeping the first occurrence of each item.

Pattern: repeated linear search -> set.
"""

EXAMPLES = [([3, 1, 3, 2, 1],), ([],), (["b", "a", "b"],)]


def slow(items: list):
    # expect: O(len(items)^2)
    seen = []
    result = []
    for item in items:
        if item not in seen:
            seen.append(item)
            result.append(item)
    return result


def fast(items: list):
    # expect: O(len(items))
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
