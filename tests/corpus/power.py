"""base ** exponent, for a non-negative integer exponent.

Pattern: repeated multiplication -> exponentiation by squaring.
"""

EXAMPLES = [(3, 0), (2, 10), (7, 13)]


def slow(base: int, exponent: int):
    # expect: O(exponent)
    result = 1
    for _ in range(exponent):
        result *= base
    return result


def fast(base: int, exponent: int):
    # expect: O(log(exponent))
    result = 1
    while exponent > 0:
        if exponent % 2 == 1:
            result *= base
        base *= base
        exponent //= 2
    return result
