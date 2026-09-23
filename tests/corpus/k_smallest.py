"""The k smallest numbers, in increasing order.

Pattern: repeated minimum search -> heapq.nsmallest.
"""

import heapq

EXAMPLES = [([9, 4, 7, 1, 8], 3), ([2, 1], 5), ([], 2)]


def slow(nums: list[int], k: int):
    # expect: O(k * len(nums))
    remaining = list(nums)
    result = []
    for _ in range(min(k, len(remaining))):
        smallest = min(remaining)
        remaining.remove(smallest)
        result.append(smallest)
    return result


def fast(nums: list[int], k: int):
    # expect: O(len(nums) * log(k))
    return heapq.nsmallest(k, nums)
