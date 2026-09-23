"""Number of paths across a rows x cols grid from the top-left corner to the
bottom-right corner, moving only right or down.

Pattern: repeated expensive function -> functools.cache.
"""

from functools import cache

EXAMPLES = [(1, 1), (3, 3), (4, 6)]


def slow(rows: int, cols: int):
    # expect: O(2^(cols + rows))
    if rows == 1 or cols == 1:
        return 1
    return slow(rows - 1, cols) + slow(rows, cols - 1)


def fast(rows: int, cols: int):
    # expect: O(cols * rows)
    @cache
    def paths(r, c):
        if r == 1 or c == 1:
            return 1
        return paths(r - 1, c) + paths(r, c - 1)

    return paths(rows, cols)
