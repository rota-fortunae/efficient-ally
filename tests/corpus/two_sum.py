"""Indices (i, j), i < j, of two numbers that add up to target, or None.

Returns the pair with the smallest j, and then the smallest i.
Pattern: pair scanning -> dict of values seen so far.
"""

EXAMPLES = [([2, 7, 11, 15], 9), ([3, 3], 6), ([1, 3, 3, 5], 6), ([1, 2], 7), ([], 0)]


def slow(nums: list[int], target: int):
    # expect: O(len(nums)^2)
    for j in range(len(nums)):
        for i in range(j):
            if nums[i] + nums[j] == target:
                return (i, j)
    return None


def fast(nums: list[int], target: int):
    # expect: O(len(nums))
    first_index = {}
    for j, num in enumerate(nums):
        if target - num in first_index:
            return (first_index[target - num], j)
        first_index.setdefault(num, j)
    return None
