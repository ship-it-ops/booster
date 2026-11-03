# Contributing

- Standard library only; tests use `unittest` and live in `tests/`, one file per module.
- The current time comes from `parcelq.clock.now()`, which is UTC. Nothing else reads the system clock, so that tests can replace it.
- A bug fix comes with a test that fails without the fix, and a commit message that says what the cause was.
- Keep a fix to the fix. Tidying goes in its own commit.
