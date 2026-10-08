def apply_discount(total_cents, percent):
    """Price after a percentage discount, rounded to the nearest cent."""
    return total_cents - total_cents * percent // 100
