from parcelq import rates


def _first_fit(bands, weight_kg):
    for band in bands:
        if weight_kg <= band["max_kg"]:
            return band["price_cents"]
    raise ValueError(f"no band for {weight_kg} kg")


def _with_promotion(bands, promotion):
    """A promotion is a band that goes in front of the standard ones."""
    if promotion is not None:
        bands.insert(0, {"max_kg": promotion["max_kg"], "price_cents": promotion["price_cents"]})
    return bands


def quote(parcel, promotion=None):
    """Price in cents for one parcel. `promotion` is the customer's own deal, if they have one."""
    table = "domestic" if parcel.country == "GB" else "international"
    bands = _with_promotion(rates.load_table(table), promotion)
    return _first_fit(bands, parcel.weight_kg)


def quote_with_fuel_surcharge(parcel, percent):
    """Price in cents with a fuel surcharge applied to every band."""
    table = "domestic" if parcel.country == "GB" else "international"
    bands = rates.load_table(table)
    for band in bands:
        band["price_cents"] = rates.round_half_up_cents(band["price_cents"] * (1 + percent / 100))
    return _first_fit(bands, parcel.weight_kg)
