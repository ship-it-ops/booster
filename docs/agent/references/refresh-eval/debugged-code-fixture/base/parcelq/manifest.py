def format_row(parcel):
    phone = parcel.phone.strip()
    return f"{parcel.tracking_id},{parcel.recipient},{phone},{parcel.weight_kg:.1f}"


def export_manifest(parcels):
    """One line per parcel for the carrier. A parcel that is not on the manifest is not collected."""
    return [format_row(parcel) for parcel in parcels]
