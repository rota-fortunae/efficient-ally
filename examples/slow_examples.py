"""Deliberately slow code, one function per pattern from the roadmap.

Try it:  efficient-ally examples/slow_examples.py

Functions marked "not detected yet" are good targets for new rules. When you
add a rule, also add a test in tests/ (the examples here are just for demos).
"""


def common_items(a: list[int], b: list[int]) -> list[int]:
    # Nested membership search -> set. Detected by list-membership-in-loop.
    return [x for x in a if x in b]


def unique_in_order(items):
    # Repeated linear search -> set. Detected by list-membership-in-loop.
    seen = []
    result = []
    for item in items:
        if item not in seen:
            seen.append(item)
            result.append(item)
    return result


def csv_line(values):
    # Repeated string concatenation -> "".join. Detected by string-concat-in-loop.
    line = ""
    for v in values:
        line += str(v) + ","
    return line


def has_duplicates(items):
    # Duplicate scanning -> set. Not detected yet.
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                return True
    return False


def process_queue(tasks: list):
    # Repeated array shifting -> collections.deque. Not detected yet, but the
    # estimator already knows that pop(0) is O(len(tasks)).
    done = []
    while tasks:
        done.append(tasks.pop(0))
    return done


def smallest_first(nums: list[int]):
    # Repeated minimum search -> heapq. Not detected yet.
    out = []
    while nums:
        smallest = min(nums)
        nums.remove(smallest)
        out.append(smallest)
    return out


def match_orders(customers, orders):
    # Nested search by key -> dict. Not detected yet.
    pairs = []
    for order in orders:
        for customer in customers:
            if customer["id"] == order["customer_id"]:
                pairs.append((customer["name"], order["total"]))
    return pairs


def running_medians(stream):
    # Repeated sorting -> bisect.insort or two heaps. Not detected yet.
    seen = []
    medians = []
    for x in stream:
        seen.append(x)
        seen.sort()
        medians.append(seen[len(seen) // 2])
    return medians


def fib(n):
    # Repeated expensive function -> @functools.cache. Not detected yet (needs
    # the call graph from month 2).
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
