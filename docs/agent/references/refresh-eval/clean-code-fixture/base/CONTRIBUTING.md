# Conventions

- **Money is an integer number of cents.** Never a float, anywhere, including tax and discounts.
- **Lookups return `None` when there is nothing to find** (`find_account`, `find_invoice`). Callers check for `None`. We do not raise for "not found".
- **Every function that changes state takes `store`, `clock` and `actor` first, in that order**, so an audit entry can be written. This means some functions take five parameters; that is fine.
- **Time comes from the `clock` argument**, never from `datetime.now()`, so tests can fix the date.
- **Handlers** live in `ledgerly/handlers.py`, take `(store, clock, actor, payload)` and return a dict with `ok` and, on failure, `error`.
- Tests use the standard library's `unittest`. No new dependencies.
