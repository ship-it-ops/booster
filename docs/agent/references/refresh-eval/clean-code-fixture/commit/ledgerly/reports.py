"""Reports."""
from datetime import datetime, timezone

from ledgerly.accounts import find_account
from ledgerly.invoices import find_invoice


def monthly_revenue(store, account_id, year, month):
    """Total cents received in a calendar month for one account, or None for an unknown account."""
    if find_account(store, account_id) is None:
        return None

    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    total_cents = 0
    for payment in store.payments:
        if not start <= payment["at"] < end:
            continue
        invoice = find_invoice(store, payment["invoice_id"])
        if invoice is None or invoice.account_id != account_id:
            continue
        total_cents += payment["amount_cents"]
    return total_cents
