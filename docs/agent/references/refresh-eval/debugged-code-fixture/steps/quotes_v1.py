from parcelq import rates


def _first_fit(bands, weight_kg):
    for band in bands:
        if weight_kg <= band["max_kg"]:
            return band["price_cents"]
    raise ValueError(f"no band for {weight_kg} kg")


def quote(parcel):
    """Price in cents for one parcel."""
    table = "domestic" if parcel.country == "GB" else "international"
    bands = rates.load_table(table)
    return _first_fit(bands, parcel.weight_kg)
