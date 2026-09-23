"""Whether a string reads the same forwards and backwards.

Flaw: building a reversed copy of the whole string on every iteration.
Pattern: repeated computation inside a loop -> do it once.
"""

EXAMPLES = [("racecar",), ("ab",), ("",)]


def slow(text: str):
    # expect: O(len(text)^2)
    for i in range(len(text)):
        if text[i] != text[::-1][i]:
            return False
    return True


def fast(text: str):
    # expect: O(len(text))
    return text == text[::-1]
