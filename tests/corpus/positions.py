"""For each query, its position in a list of names (-1 if it isn't there).

Pattern: repeated linear search (list.index) -> dict of positions.
"""

EXAMPLES = [(["ann", "bo", "cy", "bo"], ["cy", "bo", "zed"]), ([], ["a"])]


def slow(names: list[str], queries: list[str]):
    # expect: O(len(names) * len(queries))
    result = []
    for query in queries:
        if query in names:
            result.append(names.index(query))
        else:
            result.append(-1)
    return result


def fast(names: list[str], queries: list[str]):
    # expect: O(len(names) + len(queries))
    position = {}
    for i, name in enumerate(names):
        position.setdefault(name, i)
    return [position.get(query, -1) for query in queries]
