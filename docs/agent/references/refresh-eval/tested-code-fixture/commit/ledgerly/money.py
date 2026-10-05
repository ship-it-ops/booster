CENTS_PER_UNIT = 100


def format_cents(cents):
    """1050 -> '10.50'"""
    cents = int(cents)
    return f"{cents // CENTS_PER_UNIT}.{cents % CENTS_PER_UNIT:02d}"
