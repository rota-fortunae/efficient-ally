"""The list without its negative numbers.

Flaw: list.remove() searches for the item and shifts everything after it, per removal.
Pattern: repeated array shifting -> build a new list.
"""

EXAMPLES = [([3, -1, 4, -1, -5, 9],), ([],), ([-2, -2],)]


def slow(nums: list[int]):
    # expect: O(len(nums)^2)
    for num in list(nums):
        if num < 0:
            nums.remove(num)
    return nums


def fast(nums: list[int]):
    # expect: O(len(nums))
    return [num for num in nums if num >= 0]
