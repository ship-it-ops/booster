def order_total(lines):
    """Sum of quantity times unit price, in cents."""
    total = 0
    for line in lines:
        total += line["quantity"] * line["unit_price_cent"]
    return total
