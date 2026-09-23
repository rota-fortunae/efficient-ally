"""The largest number in a non-empty list.

Flaw: sorting the whole list just to read off one end.
Pattern: unnecessary sort -> max().
"""

EXAMPLES = [([4, 9, 2],), ([7],), ([-1, -5],)]


def slow(nums: list[int]):
    # expect: O(len(nums) * log(len(nums)))
    return sorted(nums)[-1]


def fast(nums: list[int]):
    # expect: O(len(nums))
    return max(nums)
