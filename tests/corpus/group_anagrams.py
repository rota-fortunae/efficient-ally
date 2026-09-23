"""Group words that are anagrams of each other.

Already reasonable: sort each word's letters to get a key for a dict.
"""

EXAMPLES = [(["eat", "tea", "tan", "ate", "nat"],), ([],)]


def group(words: list[str]):
    # expect: O(len(words) * len(word) * log(len(word)))
    groups = {}
    for word in words:
        key = "".join(sorted(word))
        groups.setdefault(key, []).append(word)
    return list(groups.values())
