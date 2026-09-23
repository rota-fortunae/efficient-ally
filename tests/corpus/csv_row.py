"""Format values as one comma-separated line.

Pattern: repeated string concatenation -> str.join.
"""

EXAMPLES = [([1, 2, 3],), ([],), (["a"],)]


def slow(values: list):
    # expect: O(len(values)^2)
    line = ""
    for i, value in enumerate(values):
        if i > 0:
            line += ","
        line += str(value)
    return line


def fast(values: list):
    # expect: O(len(values))
    return ",".join(str(value) for value in values)
