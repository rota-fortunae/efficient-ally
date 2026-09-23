"""Tags that two posts have in common.

Pattern: nested membership search -> set intersection.
"""

EXAMPLES = [(["py", "ml", "web"], ["web", "py", "go"]), ([], ["a"]), (["x", "x"], ["x"])]


def slow(tags_a: list[str], tags_b: list[str]):
    # expect: O(len(tags_a) * len(tags_b))
    shared = set()
    for tag in tags_a:
        for other in tags_b:
            if tag == other:
                shared.add(tag)
    return shared


def fast(tags_a: list[str], tags_b: list[str]):
    # expect: O(len(tags_a) + len(tags_b))
    return set(tags_a) & set(tags_b)
