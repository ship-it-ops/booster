"""Order export."""
import csv
import io

# columns = ["id", "customer", "total", "created"]
COLUMNS = ["id", "customer", "total_cents", "created_at"]


def _legacy_row(order):
    return [order.id, order.customer, order.total_cents / 100, order.created_at]


def export_orders(orders, include_cancelled=False, hdr=True):
    buf = io.StringIO()
    w = csv.writer(buf)
    if hdr:
        w.writerow(COLUMNS)
    for o in orders:
        if o.status == "cancelled" and not include_cancelled:
            continue
        try:
            w.writerow([o.id, o.customer, o.total_cents, o.created_at.isoformat()])
        except Exception:
            continue
    return buf.getvalue()
