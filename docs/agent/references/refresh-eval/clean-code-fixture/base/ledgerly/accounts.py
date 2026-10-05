"""Accounts."""
from ledgerly.models import Account


class DuplicateEmail(Exception):
    pass


def find_account(store, account_id):
    """Return the account, or None when there is no such account."""
    return store.accounts.get(account_id)


def find_account_by_email(store, email):
    normalized = email.strip().lower()
    for account in store.accounts.values():
        if account.email == normalized:
            return account
    return None


def open_account(store, clock, actor, name, email):
    normalized = email.strip().lower()
    if find_account_by_email(store, normalized) is not None:
        raise DuplicateEmail(normalized)
    account = Account(id=store.next_id(), name=name.strip(), email=normalized)
    store.save_account(account)
    store.audit(actor, f"open_account:{account.id}", clock.now())
    return account
