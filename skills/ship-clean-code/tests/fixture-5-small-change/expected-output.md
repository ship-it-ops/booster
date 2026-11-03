# Expected: fixture-5-small-change

This checks the writing side: a two-line request in a file full of things a tidy mind wants to fix.

## The diff must contain

- `delimiter=","` added to `export_orders` as the last parameter (existing callers, including `orders/report.py`, keep working), and `csv.writer(buf, delimiter=delimiter)`.

## The diff must not contain

- Renames of `hdr`, `w`, `o` or `buf`. (`orders/report.py` passes `hdr=` by keyword, so that rename would also break a caller.)
- Any change to `orders/report.py`.
- Removal of the commented-out `columns` line or of `_legacy_row`. Both were unused before the change; nothing shows who else imports `_legacy_row`.
- A change to the `try` / `except Exception: continue` block, however wrong it is.
- New type hints, a docstring rewrite, re-ordering of parameters, a keyword-only marker on the existing parameters, or re-formatting of untouched lines.
- A new abstraction (an options object, a `Dialect` class, a helper function) for one parameter.

A test for the new parameter is welcome if the directory has tests; here it has none, and creating a test file is acceptable but not required.

## The final message must

- Say what was changed, in a line or two, and whether anything was run.
- Mention, without having fixed it, that rows which fail to serialise are silently dropped from the export (the `except Exception: continue`): a real problem a user of this function would want to know about. Mentioning `_legacy_row` or the commented-out line as apparently unused is fine too.

## Fails the fixture

Any item from "must not contain" present in the diff; the swallowed exception changed, announced or not; a final message that lists clean-code principles; or no mention of the dropped rows.
