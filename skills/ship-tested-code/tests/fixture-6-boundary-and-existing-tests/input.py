"""Loyalty tiers. A customer is gold from 500 points, silver from 100, otherwise basic."""
GOLD_FROM_POINTS = 500
SILVER_FROM_POINTS = 100


def tier(points):
    if points >= GOLD_FROM_POINTS:
        return "gold"
    if points >= SILVER_FROM_POINTS:
        return "silver"
    return "basic"


def discount_percent(points):
    """Gold customers get 10%, silver 5%, basic none."""
    return {"gold": 10, "silver": 5, "basic": 0}[tier(points)]
