# Expected: fixture-3-nothing-to-report

This file is sound. The right review says so in a sentence or two, says what was looked at, and stops.

## Must not report as a problem

- `decode_cursor` returning `None` for the first page. It is documented and the caller handles it.
- The `include_total` boolean parameter.
- `paginate` taking four parameters, or "doing two things".
- Missing type hints, the bare `class InvalidCursor(ValueError): pass`, or the absence of a docstring on `encode_cursor`.
- The cursor being unsigned base64 "and therefore insecure". It encodes a position, not a permission; a client that edits it only moves its own page.
- Performance of filtering `rows` in memory. The function is documented as taking rows.

## Acceptable

At most one or two remarks at the lowest level, clearly marked optional, if they are true. For example: `total` counts all rows, not the rows after the cursor, which is the usual meaning but could be said in the docstring; a negative id in a forged cursor simply returns the first page. A review whose answer is "nothing needs changing" with no remarks at all is the best result.

## Fails the fixture

Any must-fix or should-fix finding. A list of three or more "consider" items. A section of praise or a summary table added to give the review some length. A claim to have run tests or read callers: the fixture has none, and saying so is right. A security caveat is not expected here.
