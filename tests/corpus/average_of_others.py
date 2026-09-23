"""For each number, the average of all the *other* numbers (needs at least two).

Flaw: adding up the whole list again for every number.
Pattern: repeated computation inside a loop -> compute the total once.
"""

EXAMPLES = [([1.0, 2.0, 3.0],), ([4.0, 8.0],)]


def slow(nums: list[float]):
    # expect: O(len(nums)^2)
    return [(sum(nums) - num) / (len(nums) - 1) for num in nums]


def fast(nums: list[float]):
    # expect: O(len(nums))
    total = sum(nums)
    return [(total - num) / (len(nums) - 1) for num in nums]
