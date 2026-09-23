"""Whether any item appears more than once.

Pattern: duplicate scanning -> set.
"""

EXAMPLES = [([1, 2, 3, 1],), ([1, 2, 3],), ([],)]


def slow(items: list):
    # expect: O(len(items)^2)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                return True
    return False


def fast(items: list):
    # expect: O(len(items))
    return len(set(items)) != len(items)
