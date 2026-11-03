# Conventions

- Lookups return `None` when there is nothing to find. Callers check for `None`; we do not raise for "not found".
- Every function that changes state takes `store`, `clock` and `actor` first, in that order, so an audit entry can be written. Some functions therefore take six or seven parameters; that is fine.
- Time comes from the `clock` argument, never from `time.time()` or `datetime.now()`, so tests can fix it.
- Reservations are plain dicts; they are serialised as they are.
