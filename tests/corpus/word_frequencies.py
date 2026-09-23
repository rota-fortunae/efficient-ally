"""How many times each word appears.

Already reasonable: one pass with a dict.
"""

EXAMPLES = [(["a", "b", "a"],), ([],)]


def frequencies(words: list[str]):
    # expect: O(len(words))
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return counts
