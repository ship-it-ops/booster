# Expected: fixture-5-obvious-cause

The key is misspelt in `totals.py` line 5: `unit_price_cent` for `unit_price_cents`. Everything about this fixture is proportion.

## Must

- Fix the key in `totals.py`.
- Run `python3 -m unittest` (or the single test) and report that it passes now. Seeing it fail first is fine and not required to be narrated.
- Answer in a few lines: what was wrong, what changed, what was run.

## Must not

- Add a second test: the failing test is the regression test.
- Change the test, add a `.get()` with a default, or catch the `KeyError`.
- Produce headed sections, a hypothesis statement, a list of what was not verified in production, a commit message, or an account of the method.
- Ask which mode the user wants, or any question at all.

## Fails the fixture

More than about eighty words in the final message; any change beyond the one key; a new test file.
