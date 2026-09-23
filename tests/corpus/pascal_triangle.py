"""The first n rows of Pascal's triangle.

Already reasonable: each entry is computed once from the row above.
"""

EXAMPLES = [(5,), (0,), (1,)]


def triangle(n: int):
    # expect: O(n^2)
    rows = []
    for i in range(n):
        row = [1] * (i + 1)
        for j in range(1, i):
            row[j] = rows[i - 1][j - 1] + rows[i - 1][j]
        rows.append(row)
    return rows
