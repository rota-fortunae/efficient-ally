"""Reverse a string.

Pattern: repeated string concatenation (prepending) -> slicing.
"""

EXAMPLES = [("hello",), ("",), ("ab",)]


def slow(text: str):
    # expect: O(len(text)^2)
    result = ""
    for char in text:
        result = char + result
    return result


def fast(text: str):
    # expect: O(len(text))
    return text[::-1]
