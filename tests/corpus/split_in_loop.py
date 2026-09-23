"""Which of the given words appear in a text.

Flaw: splitting the whole text again for every word, then searching the resulting list.
Pattern: repeated computation + linear search -> split once, into a set.
"""

EXAMPLES = [("the quick brown fox", ["fox", "dog", "the"]), ("", ["a"]), ("a b", [])]


def slow(text: str, words: list[str]):
    # expect: O(len(text) * len(words))
    return [word for word in words if word in text.split()]


def fast(text: str, words: list[str]):
    # expect: O(len(text) + len(words))
    present = set(text.split())
    return [word for word in words if word in present]
