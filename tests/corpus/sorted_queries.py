"""Answer queries of the form "what's the i-th smallest value?".

Pattern: repeated sorting -> sort once, before the loop.
"""

EXAMPLES = [([5, 3, 9, 1], [0, 3, 1]), ([2], [0, 0])]


def slow(values: list[int], queries: list[int]):
    # expect: O(len(queries) * len(values) * log(len(values)))
    answers = []
    for i in queries:
        answers.append(sorted(values)[i])
    return answers


def fast(values: list[int], queries: list[int]):
    # expect: O(len(queries) + len(values) * log(len(values)))
    ordered = sorted(values)
    return [ordered[i] for i in queries]
