# Python: what is easy to miss

The project's declared Python version, its type-checker and linter settings and its test framework decide what is available and what is convention. Check them (`pyproject.toml`, `setup.cfg`, `tox.ini`, `ruff.toml`, `mypy.ini`) before suggesting syntax, type hints or tools. Neither suggest nor add type hints, `pytest`, `pydantic` or anything else the code base does not already use.

Places worth a second look, because the defect reads as normal code. A match is a reason to look again, not a finding: it becomes one when you can say what goes wrong here.

- **Mutable default arguments.** `def f(items=[])` or `={}` shares one object across calls. Also a class attribute `tags = []` mutated through instances, `attr.ib(default=[])`, and any default evaluated once at definition, such as `def f(at=datetime.now())`.
- **Closures created in a loop** (`lambda: x`, a nested `def`) capture the variable, not its value at that iteration.
- **`except:` and `except Exception:` that continue.** A bare `except` also catches `KeyboardInterrupt` and `SystemExit`. Either is a problem when the handler hides the failure; `except Exception` that logs with the traceback and re-raises, or that sits at a deliberate top-level boundary, is fine. A bare `raise` inside an `except` block is the correct way to re-raise.
- **A new exception raised inside `except`.** The cause is kept either way; what gets lost is the context when the new message drops the operation and the input. `from None` hides the cause on purpose: check that this is wanted.
- **Truthiness used for presence.** `if value:` when `0`, `""` or an empty list are valid values; `x or default` for the same reason. Use `is None`.
- **`is` for value comparison** (`is 1000`, `is "ok"`): true or false depending on interning.
- **Floats for money or for equality.** Use integers of the smallest unit, or `Decimal` built from strings.
- **Naive datetimes and `datetime.now()` / `utcnow()`** mixed with aware ones: comparison raises, and local time leaks into stored data. Note where the project injects a clock.
- **Iterators consumed twice.** A generator, `map`, `zip` or file object passed to something that iterates it, then iterated again: the second pass is silently empty.
- **Mutating a collection while iterating it**, and returning or storing a caller's list or dict without copying when either side goes on to change it.
- **Blocking calls inside `async def`** (`requests`, `time.sleep`, ordinary file or database I/O) stall the event loop. A coroutine that is called but not awaited does nothing; a task created and not kept can be garbage-collected mid-flight.
- **Resources opened without `with`**, so they are not released on the exception path.
- **Module-level state**: a cache, connection or registry at module level that is shared across requests, threads or tests that are meant to be isolated; real work done at import time.
- **`assert` used for validation**: stripped under `-O`.
- **Dict and attribute access on external data** (`payload["key"]`, `row[3]`) with no handling for absence, where the surrounding code does handle it.

Not findings on their own: returning `None` for "not found" (say so in the type or docstring if the project uses them), single-letter names in a comprehension, a function longer than a screen that reads top to bottom, missing type hints in a code base without them, `print` in a command-line tool.
