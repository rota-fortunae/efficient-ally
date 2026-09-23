"""The smallest difference between any two numbers (None if there are fewer than two).

Pattern: pair scanning -> sort once, compare neighbors.
"""

EXAMPLES = [([5, 1, 9, 4],), ([3],), ([7, 7, 1],)]


def slow(nums: list[int]):
    # expect: O(len(nums)^2)
    best = None
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            gap = abs(nums[i] - nums[j])
            if best is None or gap < best:
                best = gap
    return best


def fast(nums: list[int]):
    # expect: O(len(nums) * log(len(nums)))
    ordered = sorted(nums)
    gaps = [b - a for a, b in zip(ordered, ordered[1:], strict=False)]
    return min(gaps) if gaps else None
