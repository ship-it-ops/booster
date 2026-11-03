"""Stock arithmetic for the inventory tool."""


def total(items):
    """Sum the quantities of all items. An empty inventory totals 0."""
    return sum(item["qty"] for item in items)
