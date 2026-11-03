"""In-memory store. The production store has the same interface over a database."""
from datetime import datetime, timezone


class Clock:
    def now(self):
        return datetime.now(timezone.utc)


class FixedClock(Clock):
    def __init__(self, at):
        self.at = at

    def now(self):
        return self.at


class Store:
    def __init__(self):
        self.accounts = {}
        self.invoices = {}
        self.payments = []
        self.outbox = []
        self.audit_log = []
        self._next_id = 1

    def next_id(self):
        allocated = self._next_id
        self._next_id += 1
        return allocated

    def save_account(self, account):
        self.accounts[account.id] = account

    def save_invoice(self, invoice):
        self.invoices[invoice.id] = invoice

    def append_payment(self, invoice_id, amount_cents, actor, at):
        self.payments.append(
            {"invoice_id": invoice_id, "amount_cents": amount_cents, "actor": actor, "at": at}
        )

    def audit(self, actor, action, at):
        self.audit_log.append((at, actor, action))
