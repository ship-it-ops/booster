from parcelq.models import Parcel


def parse_parcel(row):
    """Build a Parcel from one row of an uploaded order sheet."""
    return Parcel(
        tracking_id=row["tracking_id"].strip(),
        weight_kg=float(row["weight_kg"]),
        country=row["country"].strip().upper(),
        recipient=row["recipient"].strip(),
        phone=row.get("phone"),
        company=row.get("company"),
    )
