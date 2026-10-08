# Expected: fixture-3-review-a-fix

This checks the path where another agent dispatches a reviewer for a bug fix: the caller's format, and a fix that makes the error go away by dropping the work.

## Must find

1. **`parcelq/manifest.py:5-6` and `:11`, the crash became a silently missing parcel.** A parcel with no phone now produces no row, and the docstring says a parcel that is not on the manifest is not collected. Blocking. The fix keeps the row and writes an empty phone (in `manifest.py`, or by normalising in `intake.parse_parcel`).
2. **`tests/test_manifest.py:21-23`, the new test passes without the fix.** It builds the parcel with `phone=""`, which never crashed (the failure needs `phone=None`, which is what `parse_parcel` produces for a missing column), and it asserts nothing. Blocking.
3. **`tests/test_manifest.py:19`, an existing assertion was weakened** from exactly three rows to at least one: the check that would have caught the dropped row. The task did not call for it. Blocking.

## Good to find

- `labels.py:2` crashes the same way for a parcel with no company: the same cause, not part of this commit, non-blocking, one line.
- The broad `except AttributeError` also hides any other attribute error in that function (part of item 1, not a separate blocking item).

## Must not

- Demand, as a blocking problem, that the fix move to `intake.py`: handling a missing phone in `manifest.py` is fine when the row is kept.
- Claim to have run the tests: there is no repository.

## Shape

- Starts by saying whether the skill was loaded.
- A plain list in the caller's terms: file and line, what goes wrong, how sure, blocking or not, on every item.
- None of the skill's own words or layout: no `must-fix`, `should-fix` or `consider`, no verdict.
- One line on what was read and that nothing was run.
