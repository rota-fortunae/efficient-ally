"""Print jobs in arrival order; return the running page total after each job.

Pattern: repeated array shifting (list.pop(0)) -> collections.deque.
"""

from collections import deque

EXAMPLES = [([3, 1, 4],), ([],)]


def slow(jobs: list[int]):
    # expect: O(len(jobs)^2)
    queue = list(jobs)
    totals = []
    printed = 0
    while queue:
        printed += queue.pop(0)
        totals.append(printed)
    return totals


def fast(jobs: list[int]):
    # expect: O(len(jobs))
    queue = deque(jobs)
    totals = []
    printed = 0
    while queue:
        printed += queue.popleft()
        totals.append(printed)
    return totals
