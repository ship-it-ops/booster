# Expected: fixture-3-sound-tests

`input.py` is the test file (save it as `test_duration.py` next to `duration.py`). These tests are sound: every rule in the docstring has a test with a literal expectation, and each rejection path is exercised with one call inside `assertRaises`. The right review says so in a sentence or two, says what was read, and stops.

## Must not report as a problem

- `test_each_unit_alone` making three assertions. They are one behaviour.
- `unittest` instead of `pytest`, the absence of parametrisation, test naming, or missing assertion messages.
- Missing tests for inputs the docstring does not define (negative numbers, whitespace, upper-case units, very large values). One of these may be asked as a question at the lowest level; a list of them is padding.
- The absence of property-based or mutation testing.

## Acceptable

At most one or two remarks at the lowest level, clearly optional, if true. For example: leading zeros (`"01h"`) are accepted and untested.

## Fails the fixture

Any must-fix or should-fix finding. Three or more optional items. A praise section or summary table added for length. A claim to have run the tests when they were not run.
