import unittest
from datetime import date, datetime, timezone

from ledgerly.accounts import open_account
from ledgerly.handlers import handle_record_payment
from ledgerly.invoices import find_invoice, invoice_total, record_payment
from ledgerly.models import Invoice, Line
from ledgerly.store import FixedClock, Store

NOW = datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc)


class InvoicesTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.clock = FixedClock(NOW)
        self.account = open_account(self.store, self.clock, "ana", "Acme", "billing@acme.test")

    def _invoice(self, lines):
        invoice = Invoice(
            id=self.store.next_id(), account_id=self.account.id, lines=lines, due=date(2026, 3, 31)
        )
        self.store.save_invoice(invoice)
        return invoice

    def test_find_invoice_returns_none_when_missing(self):
        self.assertIsNone(find_invoice(self.store, 999))

    def test_total_applies_bulk_discount_per_line(self):
        invoice = self._invoice([Line("widget", 10, 1000), Line("gadget", 2, 500)])
        self.assertEqual(invoice_total(invoice), 9500 + 1000)

    def test_overpayment_marks_invoice_paid(self):
        invoice = self._invoice([Line("widget", 1, 1000)])
        self.assertTrue(record_payment(self.store, self.clock, "ana", invoice.id, 1200))
        self.assertEqual(invoice.status, "paid")
        self.assertEqual(len(self.store.payments), 1)

    def test_payment_handler_reports_missing_invoice(self):
        result = handle_record_payment(
            self.store, self.clock, "ana", {"invoice_id": 999, "amount_cents": 100}
        )
        self.assertEqual(result, {"ok": False, "error": "not_found"})
