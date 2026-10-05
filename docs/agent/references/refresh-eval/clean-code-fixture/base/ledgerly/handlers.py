"""Request handlers. Each takes (store, clock, actor, payload) and returns a dict."""
from ledgerly.accounts import DuplicateEmail, open_account
from ledgerly.invoices import record_payment


def handle_open_account(store, clock, actor, payload):
    try:
        account = open_account(store, clock, actor, payload["name"], payload["email"])
    except DuplicateEmail:
        return {"ok": False, "error": "duplicate_email"}
    return {"ok": True, "account_id": account.id}


def handle_record_payment(store, clock, actor, payload):
    recorded = record_payment(
        store, clock, actor, payload["invoice_id"], payload["amount_cents"]
    )
    if not recorded:
        return {"ok": False, "error": "not_found"}
    return {"ok": True}
