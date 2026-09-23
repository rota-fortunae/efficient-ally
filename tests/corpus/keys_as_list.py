"""Items on a shopping list that aren't in the inventory.

Flaw: copying the dict's keys into a list and searching it, instead of asking the dict.
Pattern: repeated linear search -> dict membership.
"""

INVENTORY = {"eggs": 12, "milk": 1, "flour": 3}
EXAMPLES = [(INVENTORY, ["milk", "sugar", "eggs", "yeast"]), ({}, ["x"])]


def slow(inventory: dict[str, int], wanted: list[str]):
    # expect: O(len(inventory) * len(wanted))
    missing = []
    for item in wanted:
        if item not in list(inventory.keys()):
            missing.append(item)
    return missing


def fast(inventory: dict[str, int], wanted: list[str]):
    # expect: O(len(wanted))
    return [item for item in wanted if item not in inventory]
