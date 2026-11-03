"""Shipping cost."""
FREE_SHIPPING_FROM_CENTS = 5000
BASE_CENTS = 499
PER_KG_CENTS = 120
ZONE_MULTIPLIER = {"domestic": 1, "eu": 2, "world": 4}


class UnknownZone(Exception):
    pass


def shipping_cents(subtotal_cents, weight_kg, zone):
    """Cost of shipping in cents. Free when the subtotal is at least FREE_SHIPPING_FROM_CENTS."""
    if zone not in ZONE_MULTIPLIER:
        raise UnknownZone(zone)
    if subtotal_cents > FREE_SHIPPING_FROM_CENTS:
        return 0
    return (BASE_CENTS + weight_kg * PER_KG_CENTS) * ZONE_MULTIPLIER[zone]
