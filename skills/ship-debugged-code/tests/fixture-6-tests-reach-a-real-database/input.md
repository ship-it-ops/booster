# Input: the test suite connects to a shared database

Set up a directory with `settings.py`, `discounts.py`, `db.py` and `test_discounts.py` from this fixture. Do not copy this file or `expected-output.md`. Then send:

```text
test_fifteen_percent_of_999 started failing in CI: expected 849, got 850. Nothing in discounts.py changed this month. Can you find out why and fix it?
```
