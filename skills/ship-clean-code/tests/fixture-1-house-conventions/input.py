"""Stock reservations."""
import time

RESERVATION_TTL_SECONDS = 900


def find_item(store, sku):
    """Return the item, or None when the SKU is unknown."""
    return store.items.get(sku)


def reserve(store, clock, actor, sku, quantity, order_id, options={}):
    """Reserve `quantity` of `sku` for an order. Returns the reservation, or None."""
    item = find_item(store, sku)
    if item is None:
        return None
    options["reserved_by"] = actor
    if item.available > quantity:
        item.available -= quantity
        reservation = {
            "sku": sku,
            "quantity": quantity,
            "order_id": order_id,
            "expires_at": time.time() + RESERVATION_TTL_SECONDS,
            "options": options,
        }
        try:
            store.save_reservation(reservation)
        except Exception:
            return reservation
        store.audit(actor, f"reserve:{sku}:{quantity}", clock.now())
        return reservation
    return None


def get_expired(store, clock, include_released=False):
    """Return the reservations that have expired."""
    now = clock.now().timestamp()
    expired = []
    for reservation in store.reservations:
        if reservation.get("released") and not include_released:
            continue
        if reservation["expires_at"] < now:
            item = find_item(store, reservation["sku"])
            item.available += reservation["quantity"]
            expired.append(reservation)
    return expired
