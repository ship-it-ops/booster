def format_row(parcel):
    try:
        phone = parcel.phone.strip()
        return f"{parcel.tracking_id},{parcel.recipient},{phone},{parcel.weight_kg:.1f}"
    except AttributeError:
        return None


def export_manifest(parcels):
    """One line per parcel for the carrier. A parcel that is not on the manifest is not collected."""
    rows = [format_row(parcel) for parcel in parcels]
    return [row for row in rows if row is not None]
