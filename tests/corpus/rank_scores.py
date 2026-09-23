"""Each score's rank, where 1 is the highest (tied scores share a rank).

Flaw: re-sorting every score, then searching the sorted copy, once per score.
Pattern: repeated sorting -> sort once and remember each score's position.
"""

EXAMPLES = [([70, 95, 80, 95],), ([],), ([5],)]


def slow(scores: list[int]):
    # expect: O(len(scores)^2 * log(len(scores)))
    ranks = []
    for score in scores:
        ranks.append(sorted(scores, reverse=True).index(score) + 1)
    return ranks


def fast(scores: list[int]):
    # expect: O(len(scores) * log(len(scores)))
    rank = {}
    for i, score in enumerate(sorted(scores, reverse=True)):
        rank.setdefault(score, i + 1)
    return [rank[score] for score in scores]
