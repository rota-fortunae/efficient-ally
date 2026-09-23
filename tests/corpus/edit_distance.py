"""The fewest single-character inserts, deletes, or substitutions that turn a into b.

Pattern: repeated expensive function -> dynamic programming.
"""

EXAMPLES = [("cat", "cut"), ("", "abc"), ("abc", ""), ("ab", "ba")]


def slow(a: str, b: str):
    # expect: O(3^(len(a) + len(b)))
    if not a:
        return len(b)
    if not b:
        return len(a)
    if a[0] == b[0]:
        return slow(a[1:], b[1:])
    return 1 + min(slow(a[1:], b), slow(a, b[1:]), slow(a[1:], b[1:]))


def fast(a: str, b: str):
    # expect: O(len(a) * len(b))
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]
