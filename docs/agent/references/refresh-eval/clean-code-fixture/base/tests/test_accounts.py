import unittest
from datetime import datetime, timezone

from ledgerly.accounts import DuplicateEmail, find_account, open_account
from ledgerly.handlers import handle_open_account
from ledgerly.store import FixedClock, Store

NOW = datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc)


class AccountsTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.clock = FixedClock(NOW)

    def test_open_account_normalizes_email_and_audits(self):
        account = open_account(self.store, self.clock, "ana", " Acme ", " Billing@Acme.test ")
        self.assertEqual(account.email, "billing@acme.test")
        self.assertEqual(account.name, "Acme")
        self.assertEqual(self.store.audit_log, [(NOW, "ana", f"open_account:{account.id}")])

    def test_duplicate_email_is_rejected(self):
        open_account(self.store, self.clock, "ana", "Acme", "billing@acme.test")
        with self.assertRaises(DuplicateEmail):
            open_account(self.store, self.clock, "ana", "Acme 2", "BILLING@acme.test")

    def test_find_account_returns_none_when_missing(self):
        self.assertIsNone(find_account(self.store, 999))

    def test_handler_reports_duplicate(self):
        payload = {"name": "Acme", "email": "billing@acme.test"}
        self.assertTrue(handle_open_account(self.store, self.clock, "ana", payload)["ok"])
        again = handle_open_account(self.store, self.clock, "ana", payload)
        self.assertEqual(again, {"ok": False, "error": "duplicate_email"})
