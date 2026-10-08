def render(parcel):
    lines = [parcel.recipient]
    lines.append(parcel.company.upper())
    lines.append(parcel.country)
    lines.append(f"[{parcel.tracking_id}]")
    # WIP: barcode line, not finished
    lines.append("*" + parcel.tracking_id + "*")
    return "\n".join(lines)
