"""Build a list with the items in reverse order.

Pattern: repeated array shifting (insert at the front) -> append, reverse once.
"""

EXAMPLES = [([1, 2, 3],), ([],)]


def slow(items: list):
    # expect: O(len(items)^2)
    result = []
    for item in items:
        result.insert(0, item)
    return result


def fast(items: list):
    # expect: O(len(items))
    result = []
    for item in items:
        result.append(item)
    result.reverse()
    return result
