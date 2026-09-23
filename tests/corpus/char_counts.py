"""How many times each character appears in a string.

Flaw: text.count() scans the whole string, once for every character in it.
Pattern: repeated linear search (str.count) -> collections.Counter.
"""

from collections import Counter

EXAMPLES = [("banana",), ("",), ("aaa",)]


def slow(text: str):
    # expect: O(len(text)^2)
    return {char: text.count(char) for char in text}


def fast(text: str):
    # expect: O(len(text))
    return dict(Counter(text))
