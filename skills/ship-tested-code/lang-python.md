# Python tests: what is easy to miss

The project's runner and its configuration (`pyproject.toml`, `pytest.ini`, `setup.cfg`, `tox.ini`, `conftest.py`) and the existing tests decide the framework, plugins and helpers. Do not add `pytest`, `freezegun`, `factory_boy`, `hypothesis`, `pytest-asyncio` or anything else the project does not already use, and mention one only when it is the fix for a real finding; `unittest` with hand-written fakes is a complete way to test. Several lines below depend on the Python and runner versions: check them before reporting.

Places worth a second look, because the test reads as normal and proves nothing. A match is a reason to look again, not a finding: it becomes one when you can say what goes wrong here.

- **Mock attributes that look like assertions.** `mock.assert_called_once` without the parentheses checks nothing on any version. `mock.called_once()` and `mock.called_with(...)` pass silently before Python 3.12, and on any mock created with `unsafe=True`; on current Python they raise. `assert mock.called` with no check of the arguments is weaker than it reads.
- **`assert` on a tuple or a non-empty value.** `assert (a == b, "message")` is always true. `assertTrue(a, b)` treats `b` as the message; `assertEqual` was meant.
- **Assertions inside `try` / `except Exception`**, or inside a callback or thread: `AssertionError` is caught or lost and the test passes.
- **Code after the raising line inside `pytest.raises` / `assertRaises`.** It never runs. A `raises(Exception)` so broad that a typo's `NameError` satisfies it.
- **An async test whose body never runs.** An `async def` test in a plain `unittest.TestCase` passes with a warning (`IsolatedAsyncioTestCase` is needed); under pytest with no async plugin it is skipped with a warning or, on recent versions, fails. A coroutine called without `await` inside a test does nothing.
- **A test the runner does not collect**: a function or file whose name does not match the pattern, a `unittest` method without the `test` prefix, a class that does not subclass `TestCase` or has an `__init__`, two tests with the same name in one class (the second replaces the first).
- **`MagicMock` standing in for the thing under test's data.** Every attribute exists and every comparison "works"; arithmetic and truthiness on a Mock rarely mean what the test implies.
- **`patch` aimed at where a name is defined, not where it is used**, so the real object still runs; a patch started and not stopped, leaking into later tests.
- **State shared between tests**: module-level objects, class attributes, mutable default arguments in helpers, fixtures with `scope="module"` or `"session"` that tests mutate, environment variables set and not restored.
- **Time**: `datetime.now()` or `date.today()` in the test or the code, hard-coded dates that will pass, naive against aware datetimes, a test that fails near midnight or at month end.
- **Order and equality of unordered things**: comparing a list built from a set or from unordered query results; `==` on floats.
- **Parametrised cases that are all the same path**, or a parametrised list that is empty and so runs nothing.
- **A different engine in tests** (SQLite for PostgreSQL) asserting behaviour that differs between them: locking, JSON, case sensitivity, constraint timing.

Not findings on their own: `unittest` in place of `pytest`, `setUp` in place of fixtures, a helper function in place of a factory, plain `assert`, several assertions about one result, no assertion messages, `unittest.mock.patch` on the module's clock where the code offers no injection point.
