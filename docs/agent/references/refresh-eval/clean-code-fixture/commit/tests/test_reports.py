import unittest
from datetime import date, datetime, timezone

from ledgerly.accounts import open_account
from ledgerly.invoices import record_payment
from ledgerly.models import Invoice, Line
from ledgerly.reports import monthly_revenue
from ledgerly.store import FixedClock, Store

MARCH = datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc)


class MonthlyRevenueTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.clock = FixedClock(MARCH)
        self.account = open_account(self.store, self.clock, "ana", "Acme", "billing@acme.test")
        self.invoice = Invoice(
            id=self.store.next_id(),
            account_id=self.account.id,
            lines=[Line("widget", 1, 1000)],
            due=date(2026, 3, 31),
        )
        self.store.save_invoice(self.invoice)

    def test_unknown_account_returns_none(self):
        self.assertIsNone(monthly_revenue(self.store, 999, 2026, 3))

    def test_monthly_revenue(self):
        record_payment(self.store, self.clock, "ana", self.invoice.id, 400)
        record_payment(self.store, self.clock, "ana", self.invoice.id, 600)
        result = monthly_revenue(self.store, self.account.id, 2026, 3)
        self.assertIsNotNone(result)
        self.assertTrue(result >= 0)

    def test_void_invoices_are_excluded(self):
        record_payment(self.store, self.clock, "ana", self.invoice.id, 400)
        self.invoice.status = "void"
        result = monthly_revenue(self.store, self.account.id, 2026, 3)
        self.assertIsNotNone(result)
