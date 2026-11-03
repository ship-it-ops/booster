# Two test reviews in the default format

These show tone and proportion for a plain "review these tests" with no other instructions. When a caller asks for another format, use theirs.

## A green suite that proves less than it looks

The request: "Review `tests/test_quota.py`. It's green; can we rely on it?" The project uses `unittest` and its own `FakeClock`. The code under test:

```python
# quota.py
12  def remaining(account, clock):
13      """Requests left in the current month. Never negative."""
14      used = account.usage.get(clock.now().strftime("%Y-%m"), 0)
15      return account.monthly_limit - used
```

```python
# tests/test_quota.py
 8  class RemainingTest(unittest.TestCase):
 9      def test_remaining(self):
10          account = Account(monthly_limit=100, usage={"2026-03": 40})
11          self.assertEqual(remaining(account, FakeClock("2026-03-15")), 60)
12
13      def test_over_limit(self):
14          account = Account(monthly_limit=100, usage={"2026-03": 130})
15          self.assertEqual(remaining(account, FakeClock("2026-03-15")), -30)
16
17      def test_new_month_resets(self):
18          account = Account(monthly_limit=100, usage={"2026-03": 40})
19          result = remaining(account, FakeClock("2026-04-01"))
20          self.assertIsNotNone(result)
21
22      def test_limit_from_plan(self):
23          account = MagicMock()
24          remaining(account, FakeClock("2026-03-15"))
25          account.usage.get.assert_called_once()
```

The review:

> Not yet: one test asserts a wrong result as correct, and two would pass whatever the function returned. `test_remaining` is sound. All three confirmed by reading `quota.py` against the tests; nothing was run.
>
> **must-fix**
>
> - `tests/test_quota.py:13-15`, `test_over_limit` — expects `-30`, but the docstring on `quota.py:13` says the result is never negative. The code is wrong (`quota.py:15` has no floor) and this test makes the wrong value look intended. The defect is in `remaining`; the test should expect `0`, and will fail until the code is fixed.
> - `tests/test_quota.py:17-20`, `test_new_month_resets` — `assertIsNotNone` is true for any number, so the test passes even if April still counted March's usage (read `quota.py:14`: the month key is what makes it reset). Expect the value: `assertEqual(result, 100)`.
> - `tests/test_quota.py:22-25`, `test_limit_from_plan` — the account is a `MagicMock`, so `monthly_limit - used` is arithmetic on mocks, and the only assertion is that `usage.get` was called. It cannot fail for anything `remaining` returns. Build a real `Account` and assert the number, or delete it if `test_remaining` already covers what was meant.
>
> **consider**
>
> - No test for usage exactly at the limit (`0` remaining).
>
> Read `quota.py` and the test file; judged against the existing `unittest` style.

What to notice: the opening answers the question. The first finding says the production code is wrong, not just the test. Each finding names the wrong behaviour that would go unnoticed. Nothing is said about test names, the absence of a factory, or `unittest`.

## A test file with nothing wrong

The request: "Review `tests/test_slug.py`."

```python
 5  class SlugifyTest(unittest.TestCase):
 6      def test_lowercases_and_joins_words_with_hyphens(self):
 7          self.assertEqual(slugify("Hello World"), "hello-world")
 8
 9      def test_strips_punctuation(self):
10          self.assertEqual(slugify("What's new?"), "whats-new")
11
12      def test_collapses_runs_of_separators(self):
13          self.assertEqual(slugify("a  --  b"), "a-b")
14
15      def test_empty_string_stays_empty(self):
16          self.assertEqual(slugify(""), "")
17
18      def test_non_ascii_letters_are_transliterated(self):
19          self.assertEqual(slugify("Crème brûlée"), "creme-brulee")
```

The review:

> These tests are sound. Each one states a rule of `slugify` and expects a literal a person can check by eye; I read `slug.py` alongside them and every branch in it has a test that would fail if the branch were wrong. Nothing was run.

What to notice: no invented findings, no suggestion to parametrise five clear tests, no call for more cases the function does not have. A review that says this and stops is the right one.
