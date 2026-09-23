"""Pair each order with the name of the customer who placed it.

Pattern: nested search by key -> dict.
"""

CUSTOMERS = [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Grace"}]
ORDERS = [
    {"customer_id": 2, "total": 30},
    {"customer_id": 1, "total": 12},
    {"customer_id": 3, "total": 7},
]
EXAMPLES = [(CUSTOMERS, ORDERS), ([], [])]


def slow(customers: list[dict], orders: list[dict]):
    # expect: O(len(customers) * len(orders))
    pairs = []
    for order in orders:
        for customer in customers:
            if customer["id"] == order["customer_id"]:
                pairs.append((customer["name"], order["total"]))
    return pairs


def fast(customers: list[dict], orders: list[dict]):
    # expect: O(len(customers) + len(orders))
    name_by_id = {customer["id"]: customer["name"] for customer in customers}
    return [
        (name_by_id[order["customer_id"]], order["total"])
        for order in orders
        if order["customer_id"] in name_by_id
    ]
