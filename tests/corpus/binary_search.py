"""Position of target in a sorted list of distinct numbers, or -1.

Pattern: linear search over sorted data -> binary search.
"""

EXAMPLES = [([1, 3, 5, 7, 9], 7), ([1, 3, 5], 4), ([], 1)]


def slow(sorted_items: list[int], target: int):
    # expect: O(len(sorted_items))
    for i, item in enumerate(sorted_items):
        if item == target:
            return i
    return -1


def fast(sorted_items: list[int], target: int):
    # expect: O(log(len(sorted_items)))
    lo, hi = 0, len(sorted_items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if sorted_items[mid] == target:
            return mid
        if sorted_items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
