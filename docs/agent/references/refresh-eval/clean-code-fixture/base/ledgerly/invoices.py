"""Invoices: building, totals, payments, overdue handling and statements."""
from datetime import datetime

from ledgerly.accounts import find_account
from ledgerly.models import Invoice
from ledgerly.money import format_cents

TAX_RATE = 0.0825
GRACE_DAYS = 5
BULK_QUANTITY = 10
BULK_DISCOUNT_PERCENT = 5
STATEMENT_WIDTH = 48


class UnknownAccount(Exception):
    pass


def find_invoice(store, invoice_id):
    """Return the invoice, or None when there is no such invoice."""
    return store.invoices.get(invoice_id)


def build_invoice(store, clock, actor, account_id, lines, due, tags=[]):
    if find_account(store, account_id) is None:
        raise UnknownAccount(account_id)
    tags.append("auto")
    subtotal = 0
    for line in lines:
        amount = line.quantity * line.unit_cents
        if line.quantity >= BULK_QUANTITY:
            amount -= amount * BULK_DISCOUNT_PERCENT // 100
        subtotal += amount
    invoice = Invoice(
        id=store.next_id(), account_id=account_id, lines=list(lines), due=due, tags=tags
    )
    invoice.tax_cents = subtotal * TAX_RATE
    store.save_invoice(invoice)
    store.audit(actor, f"build_invoice:{invoice.id}", clock.now())
    return invoice


def invoice_total(invoice):
    subtotal = 0
    for line in invoice.lines:
        amount = line.quantity * line.unit_cents
        if line.quantity >= BULK_QUANTITY:
            amount -= amount * BULK_DISCOUNT_PERCENT // 100
        subtotal += amount
    return subtotal + invoice.tax_cents


def record_payment(store, clock, actor, invoice_id, amount_cents):
    invoice = find_invoice(store, invoice_id)
    if invoice is None:
        return False
    invoice.paid_cents += amount_cents
    if invoice.paid_cents > invoice_total(invoice):
        invoice.status = "paid"
    try:
        store.append_payment(invoice_id, amount_cents, actor, clock.now())
        store.audit(actor, f"record_payment:{invoice_id}", clock.now())
    except Exception:
        pass
    return True


def get_overdue(store, account_id=None, include_void=False):
    """Return the overdue invoices, optionally for one account."""
    today = datetime.now().date()
    overdue = []
    for invoice in store.invoices.values():
        if account_id is not None and invoice.account_id != account_id:
            continue
        if invoice.status == "void" and not include_void:
            continue
        if invoice.status == "paid":
            continue
        if (today - invoice.due).days > GRACE_DAYS:
            invoice.status = "overdue"
            store.outbox.append(("reminder", invoice.account_id, invoice.id))
            overdue.append(invoice)
    return overdue


def statement_rows(store, account_id):
    rows = []
    for invoice in store.invoices.values():
        if invoice.account_id != account_id:
            continue
        subtotal = 0
        for line in invoice.lines:
            subtotal += line.quantity * line.unit_cents
        rows.append((invoice.id, invoice.due, subtotal + invoice.tax_cents, invoice.status))
    return rows


def render_statement(store, account_id):
    """Return the account's statement as plain text, or None for an unknown account."""
    account = find_account(store, account_id)
    if account is None:
        return None

    rule = "-" * STATEMENT_WIDTH
    out = []
    out.append(f"Statement for {account.name}")
    out.append(f"Account {account.id} <{account.email}>")
    out.append(rule)
    out.append(f"{'Invoice':<10}{'Due':<14}{'Status':<10}{'Amount':>14}")
    out.append(rule)

    billed_cents = 0
    outstanding_cents = 0
    rows = statement_rows(store, account_id)
    for invoice_id, due, amount_cents, status in rows:
        out.append(
            f"{invoice_id:<10}{due.isoformat():<14}{status:<10}{format_cents(amount_cents):>14}"
        )
        if status == "void":
            continue
        billed_cents += amount_cents
        if status != "paid":
            outstanding_cents += amount_cents

    if not rows:
        out.append("No invoices.")

    out.append(rule)
    out.append(f"{'Billed':<34}{format_cents(billed_cents):>14}")
    out.append(f"{'Outstanding':<34}{format_cents(outstanding_cents):>14}")
    out.append(rule)
    return "\n".join(out)
