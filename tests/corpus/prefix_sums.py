"""Running totals: result[i] = nums[0] + ... + nums[i].

Pattern: repeated computation over overlapping ranges -> keep a running total.
"""

EXAMPLES = [([1, 2, 3, 4],), ([],), ([-1, 1],)]


def slow(nums: list[int]):
    # expect: O(len(nums)^2)
    return [sum(nums[: i + 1]) for i in range(len(nums))]


def fast(nums: list[int]):
    # expect: O(len(nums))
    totals = []
    running = 0
    for num in nums:
        running += num
        totals.append(running)
    return totals
