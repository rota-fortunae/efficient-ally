"""Flatten a list of lists into one list.

Already reasonable: every cell is visited once.
"""

EXAMPLES = [([[1, 2], [3], []],), ([],)]


def flatten(grid: list[list]):
    # expect: O(len(grid) * len(row))
    flat = []
    for row in grid:
        for cell in row:
            flat.append(cell)
    return flat
