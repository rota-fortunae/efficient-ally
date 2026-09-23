"""The even numbers in a list, in order.

Flaw: `evens = evens + [num]` copies the whole list every time it grows.
Pattern: repeated list concatenation -> append.
"""

EXAMPLES = [([1, 2, 3, 4, 6],), ([],), ([1, 3],)]


def slow(nums: list[int]):
    # expect: O(len(nums)^2)
    evens = []
    for num in nums:
        if num % 2 == 0:
            evens = evens + [num]
    return evens


def fast(nums: list[int]):
    # expect: O(len(nums))
    evens = []
    for num in nums:
        if num % 2 == 0:
            evens.append(num)
    return evens
