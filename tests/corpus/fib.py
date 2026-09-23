"""The n-th Fibonacci number.

Pattern: repeated expensive function -> memoization, or a simple loop.
"""

EXAMPLES = [(0,), (1,), (10,), (20,)]


def slow(n: int):
    # expect: O(2^n)
    if n < 2:
        return n
    return slow(n - 1) + slow(n - 2)


def fast(n: int):
    # expect: O(n)
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
