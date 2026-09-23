"""Multiply two square matrices, each a list of rows.

Already reasonable: the textbook triple loop.
"""

EXAMPLES = [([[1, 2], [3, 4]], [[5, 6], [7, 8]]), ([], [])]


def multiply(a: list[list[float]], b: list[list[float]]):
    # expect: O(len(a)^3)
    n = len(a)
    result = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result[i][j] += a[i][k] * b[k][j]
    return result
