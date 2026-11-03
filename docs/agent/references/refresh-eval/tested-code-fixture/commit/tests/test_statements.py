import unittest
from datetime import date, datetime, timezone

from ledgerly.accounts import open_account
from ledgerly.invoices import render_statement, statement_rows
from ledgerly.models import Invoice, Line
from ledgerly.money import format_cents
from ledgerly.store import FixedClock, Store

NOW = datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc)


class StatementTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.clock = FixedClock(NOW)
        self.account = open_account(self.store, self.clock, "ana", "Acme", "billing@acme.test")

    def _invoice(self, cents, status="open", quantity=1):
        invoice = Invoice(
            id=self.store.next_id(),
            account_id=self.account.id,
            lines=[Line("widget", quantity, cents)],
            due=date(2026, 3, 31),
            status=status,
        )
        self.store.save_invoice(invoice)
        return invoice

    def test_unknown_account_returns_none(self):
        self.assertIsNone(render_statement(self.store, 999))

    def test_statement_lists_each_invoice_with_its_amount(self):
        self._invoice(1000)
        self._invoice(2500)
        text = render_statement(self.store, self.account.id)
        self.assertIn("Statement for Acme", text)
        self.assertEqual(len(statement_rows(self.store, self.account.id)), 2)

    def test_void_invoices_are_excluded_from_totals(self):
        self._invoice(1000)
        self._invoice(500, status="void")
        text = render_statement(self.store, self.account.id)
        self.assertIn("Billed", text)
        self.assertIn(format_cents(1000), text)

    def test_paid_invoices_are_not_outstanding(self):
        self._invoice(1000, status="paid")
        self._invoice(700)
        rows = statement_rows(self.store, self.account.id)
        outstanding = sum(amount for _, _, amount, status in rows if status not in ("paid", "void"))
        text = render_statement(self.store, self.account.id)
        self.assertIn(format_cents(outstanding), text)

    def test_bulk_order_amount(self):
        self._invoice(1000, quantity=12)
        text = render_statement(self.store, self.account.id)
        self.assertIn("120.00", text)

    def test_statement_with_tax(self):
        invoice = self._invoice(1000)
        invoice.tax_cents = 82.5
        text = render_statement(self.store, self.account.id)
        self.assertIn("10.82", text)
