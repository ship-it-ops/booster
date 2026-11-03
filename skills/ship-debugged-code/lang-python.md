# Python: evidence without a debugger, and causes that mislead

Read this when the cause is not evident from the code and one run. A match is a place to look, not a diagnosis: confirm it the way `SKILL.md` describes. Use what the project already has; several flags below depend on the Python and runner versions.

## Getting evidence

- The whole traceback, including "The above exception was the direct cause" and "During handling of the above exception" chains: the first exception is usually the cause, the last one is what you were shown.
- One test, verbosely, stopping at the first failure: `python -m pytest path::test -x -vv -l --tb=long` or `python -m unittest -v path.to.TestCase.test_name`. `-l` prints local variables, which can include credentials: do not quote them.
- A never-awaited coroutine is already reported as a `RuntimeWarning` in a normal run; `python -X dev` adds where it was created and reports unclosed resources. These are printed, not raised (under pytest, in the warnings summary at the end): read the output. `-W error` turns warnings into exceptions and can break the import of a library that emits a deprecation warning.
- A hang: under pytest, `-o faulthandler_timeout=20`; in a script of your own, `faulthandler.dump_traceback_later(20)` at the top. Both print every thread's stack without attaching anything, and neither stops the run: bound the command with a time limit. `-X faulthandler` alone dumps only on a fatal signal.
- Repeating and ordering tests needs a plugin the project may not have; a shell loop around the test command works everywhere.
- Which code is running: `module.__file__`, and `importlib.metadata.version("name")` for the installed version (`__version__` is often absent).
- Timing and memory with the standard library: `time.perf_counter()` around a section, `python -m cProfile -s cumulative`, `tracemalloc` snapshots compared before and after a repeated operation.
- Never leave `breakpoint()` or `pdb.set_trace()` in a run: it waits for input that will not come.

## Causes that look like something else

- **State that survives between calls:** a module-level list or dict, a class attribute used as an instance attribute, an `lru_cache` or hand-written cache whose returned object a caller mutates. The symptom is "wrong only the second time" or "goes away on restart", and tests that reset state in `setUp` never see it.
- **Two clocks:** `datetime.now()` and `date.today()` are local to the machine; compared with UTC values, or with a clock the test replaces, the result depends on the hour and differs between a laptop, CI and production.
- **Patching the wrong name:** `mock.patch` must target where the name is looked up, not where it is defined; otherwise the real thing still runs and the test passes or fails by accident.
- **A coroutine that was never awaited** does nothing and returns a coroutine object, which is truthy.
- **A broad `except` that hides the real error,** including one that catches the `AssertionError` of a test.
- **A different version installed** from the one in the lock file, or a different copy of the module imported than the one you are editing.
