"""The largest sum of a contiguous, non-empty run of the list.

Pattern: re-adding overlapping ranges -> Kadane's algorithm.
"""

EXAMPLES = [([-2, 1, -3, 4, -1, 2, 1, -5, 4],), ([-3, -1, -2],), ([5],)]


def slow(nums: list[int]):
    # expect: O(len(nums)^2)
    best = nums[0]
    for i in range(len(nums)):
        total = 0
        for j in range(i, len(nums)):
            total += nums[j]
            best = max(best, total)
    return best


def fast(nums: list[int]):
    # expect: O(len(nums))
    best = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)
        best = max(best, current)
    return best
