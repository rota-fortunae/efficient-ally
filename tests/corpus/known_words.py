"""Count how many words in a text appear in a vocabulary.

Pattern: nested membership search -> set.
"""

EXAMPLES = [
    (["the", "cat", "sat", "zzz"], ["cat", "the", "dog"]),
    ([], ["a"]),
    (["a", "a"], []),
]


def slow(words: list[str], vocabulary: list[str]):
    # expect: O(len(vocabulary) * len(words))
    return sum(1 for word in words if word in vocabulary)


def fast(words: list[str], vocabulary: list[str]):
    # expect: O(len(vocabulary) + len(words))
    known = set(vocabulary)
    return sum(1 for word in words if word in known)
