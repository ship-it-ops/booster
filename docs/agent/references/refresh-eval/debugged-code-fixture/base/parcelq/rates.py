"""Rate tables. A table is a list of bands, cheapest band first; the first band that fits wins."""

_TABLES = {
    "domestic": [
        {"max_kg": 2, "price_cents": 450},
        {"max_kg": 10, "price_cents": 890},
        {"max_kg": 30, "price_cents": 1990},
    ],
    "international": [
        {"max_kg": 2, "price_cents": 1450},
        {"max_kg": 10, "price_cents": 3200},
        {"max_kg": 30, "price_cents": 7400},
    ],
}

_CACHE = {}


def _read_table(name):
    # Stands in for a slow read from the pricing service.
    return [dict(band) for band in _TABLES[name]]


def load_table(name):
    if name not in _CACHE:
        _CACHE[name] = _read_table(name)
    return _CACHE[name]


def clear_cache():
    _CACHE.clear()


def round_half_up_cents(value):
    # int() truncates, so add a half first. Prices are never negative.
    return int(value + 0.5)
