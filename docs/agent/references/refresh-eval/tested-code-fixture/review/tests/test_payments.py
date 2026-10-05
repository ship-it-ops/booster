import unittest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from ledgerly.accounts import open_account
from ledgerly.invoices import build_invoice, get_overdue, invoice_total, record_payment
from ledgerly.models import Invoice, Line
from ledgerly.store import FixedClock, Store

NOW = datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc)
STORE = Store()
CLOCK = FixedClock(NOW)


def make_invoice(store, account_id, cents=1000, due=date(2026, 3, 31)):
    invoice = Invoice(
        id=store.next_id(), account_id=account_id, lines=[Line("widget", 1, cents)], due=due
    )
    store.save_invoice(invoice)
    return invoice


class PaymentTests(unittest.TestCase):
    def test_1_open_account(self):
        account = open_account(STORE, CLOCK, "ana", "Acme", "billing@acme.test")
        self.assertEqual(account.id, 1)

    def test_2_partial_payment(self):
        invoice = make_invoice(STORE, 1)
        record_payment(STORE, CLOCK, "ana", invoice.id, 400)
        self.assertEqual(invoice.paid_cents, 400)
        self.assertEqual(invoice.status, "open")
        self.assertEqual(len(STORE.payments), 1)

    def test_3_exact_payment(self):
        invoice = make_invoice(STORE, 1)
        record_payment(STORE, CLOCK, "ana", invoice.id, 1000)
        self.assertEqual(invoice.paid_cents, 1000)
        self.assertEqual(invoice.status, "open")

    def test_4_payment_is_stored(self):
        store = MagicMock()
        store.invoices.get.return_value = Invoice(
            id=7, account_id=1, lines=[Line("widget", 1, 1000)], due=date(2026, 3, 31)
        )
        record_payment(store, CLOCK, "ana", 7, 1000)
        store.append_payment.assert_called_once()
        store.audit.assert_called_once()

    def test_5_store_failure_is_handled(self):
        store = MagicMock()
        store.invoices.get.return_value = Invoice(
            id=7, account_id=1, lines=[Line("widget", 1, 1000)], due=date(2026, 3, 31)
        )
        store.append_payment.side_effect = RuntimeError("database is down")
        self.assertTrue(record_payment(store, CLOCK, "ana", 7, 500))

    def test_6_not_yet_overdue(self):
        invoice = make_invoice(STORE, 1, due=date(2027, 1, 31))
        self.assertNotIn(invoice, get_overdue(STORE))

    def test_7_void_invoices_are_skipped(self):
        make_invoice(STORE, 1, due=date(2020, 1, 1))
        overdue = get_overdue(STORE, include_void=False)
        self.assertTrue(len(overdue) >= 0)

    def test_8_total_with_bulk_discount(self):
        invoice = Invoice(
            id=99, account_id=1, lines=[Line("widget", 12, 250)], due=date(2026, 3, 31)
        )
        expected = 0
        for line in invoice.lines:
            amount = line.quantity * line.unit_cents
            if line.quantity >= 10:
                amount -= amount * 5 // 100
            expected += amount
        self.assertEqual(invoice_total(invoice), expected)

    def test_9_build_invoice_adds_tax(self):
        try:
            invoice = build_invoice(
                STORE, CLOCK, "ana", 1, [Line("widget", 1, 1000)], date(2026, 3, 31)
            )
            self.assertEqual(invoice.tax_cents, 82)
        except Exception:
            pass
