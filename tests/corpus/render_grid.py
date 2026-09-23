"""Draw a width x height checkerboard as text, one line per row.

Pattern: repeated string concatenation -> build each row, join once.
"""

EXAMPLES = [(3, 2), (0, 0), (1, 4)]


def slow(width: int, height: int):
    # expect: O(height^2 * width^2)
    board = ""
    for y in range(height):
        for x in range(width):
            board += "#" if (x + y) % 2 == 0 else "."
        board += "\n"
    return board


def fast(width: int, height: int):
    # expect: O(height * width)
    lines = []
    for y in range(height):
        lines.append("".join("#" if (x + y) % 2 == 0 else "." for x in range(width)) + "\n")
    return "".join(lines)
