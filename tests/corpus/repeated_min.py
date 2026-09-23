"""Sort numbers by repeatedly taking out the smallest one.

Pattern: repeated minimum search -> heap.
"""

import heapq

EXAMPLES = [([5, 2, 8, 1, 2],), ([],)]


def slow(nums: list[int]):
    # expect: O(len(nums)^2)
    remaining = list(nums)
    ordered = []
    while remaining:
        smallest = min(remaining)
        remaining.remove(smallest)
        ordered.append(smallest)
    return ordered


def fast(nums: list[int]):
    # expect: O(len(nums) * log(len(nums)))
    heap = list(nums)
    heapq.heapify(heap)
    return [heapq.heappop(heap) for _ in range(len(heap))]
