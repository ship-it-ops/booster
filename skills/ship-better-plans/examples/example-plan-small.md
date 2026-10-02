---
type: plan
status: active
approval: approved
created: 2026-09-30
updated: 2026-09-30
author: claude-opus-5-5
tags: [cli, report]
importance: standard
plan_format: 2
base: main@91f3c0d
---

# Plan: JSON output for the report command

<!-- Example of a right-sized plan for small work: three tasks, one viable approach, no separate requirements, a light review. Do not reuse its decisions. It passes `lint_plan.py --no-paths` (the repository it describes is fictional). -->

## Summary
Add a `--json` flag to the `report` command so scripts can consume its output without scraping the text table. A second renderer sits beside the existing table renderer and the flag chooses between them. The only real risk is changing the default output, which an existing snapshot test guards. Done when `report --json` emits the same rows and totals as the table and the default output is unchanged.

## Context
- **Problem:** `report` prints only a text table, so scripts that consume it parse columns by position.
- **Why now:** not stated.
- **Request:** "Add a --json flag to the report command."

## Success criteria
- SC-1: `report --json` prints one JSON document with the same rows and totals as the table. (stated)
- SC-2: without the flag, the output is byte-for-byte what it is today. (inferred, confirmed at the checkpoint)

## Non-goals
- Other formats (CSV, YAML).
- Changing which columns the report has.

## Constraints
- Standard library only; `tools/` has no third-party dependencies (F-4).

## Facts and assumptions
- F-1: rows are built by `build_rows()`, which returns a list of `Row` dataclasses, separately from rendering — `tools/report/rows.py:18`
- F-2: the table is rendered by `render_table(rows)` — `tools/report/render.py:9`
- F-3: arguments are parsed with `argparse` in `main()` — `tools/report/cli.py:22`
- F-4: the project declares no dependencies — `pyproject.toml:12`
- F-5: a snapshot test pins the default output — `tools/report/tests/test_cli.py:31`
- F-6: the tests pass before this work — ran: `python3 -m pytest tools/report` → 14 passed

## Approach
One viable approach: add `render_json` beside `render_table` and choose with the flag.

- **Chosen:** a second renderer — **deciding factor:** rows are already built separately from rendering (F-1, F-2), so nothing else has to change, and the standard-library constraint rules out a serialisation library.

## Risks and rollback
- **Risk:** the default output changes by accident. Handled by AC-2 (the existing snapshot test, F-5).
- **Rollback:** revert the change; it is additive.
- **Migration:** N/A — no stored data.

## Specification

### Acceptance criteria
- AC-1 (SC-1): on the fixture data, `report --json` prints JSON whose `rows` equal the `build_rows()` output and whose `totals` equal the table's totals row — verify: `python3 -m pytest tools/report/tests/test_json.py`
- AC-2 (SC-2): the existing snapshot test passes unchanged — verify: `python3 -m pytest tools/report/tests/test_cli.py`

### Non-functional targets
N/A — a local command-line tool; no performance, security or accessibility surface changes.

### Interfaces and data shapes
- `render_json(rows: list[Row]) -> str` in `tools/report/render.py`.
- Output: `{ "rows": [ { <Row field>: <value> } ], "totals": { <numeric field>: <sum> } }`. Keys are the `Row` field names. `Decimal` values are written as strings so no precision is lost.

### Edge cases
| Case | Expected behaviour | Covered by |
|------|--------------------|------------|
| No rows | `{"rows": [], "totals": {}}` | AC-1 |
| Non-ASCII names | Written as-is (`ensure_ascii=False`) | AC-1 |
| Very large reports | Out of scope because the table path already builds every row in memory | N/A |

## Verification
- **Setup:** none; Python 3.11 and the repository are enough.
- **Commands:** test `python3 -m pytest tools/report` · lint `ruff check tools` — defined in `pyproject.toml`
- **Baseline:** `python3 -m pytest tools/report` → 14 passed (F-6).
- **Final check:** SC-1 by AC-1 and SC-2 by AC-2, both in the test run.

## Tasks

### Conventions for every task
- Standard library only.
- Tests go in `tools/report/tests/`, in the style of `tools/report/tests/test_cli.py`.

### T1 — JSON renderer
- **Depends on:** none
- **Covers:** AC-1
- **Files:** `tools/report/render.py` (modify), `tools/report/tests/test_json.py` (new)
- **Do:** Add `render_json(rows)` beside `render_table` in `tools/report/render.py`. It returns a JSON string of the form `{"rows": [...], "totals": {...}}`: each row is the `Row` dataclass as a dict keyed by field name, totals are the sums of the numeric fields, `Decimal` values are written as strings, and `ensure_ascii` is false. Write tests first for the fixture data, for no rows, and for a non-ASCII name. Do not touch `render_table`.
- **Verify:** `python3 -m pytest tools/report/tests/test_json.py` → passes
- **Kind:** code · **Size:** S · **Reversibility:** safe

### T2 — The --json flag
- **Depends on:** T1
- **Covers:** AC-1, AC-2
- **Files:** `tools/report/cli.py` (modify), `tools/report/tests/test_json.py` (modify)
- **Do:** In `main()` in `tools/report/cli.py`, add a `--json` boolean argument to the existing `argparse` parser. When it is set, print `render_json(rows)` from `tools/report/render.py` instead of `render_table(rows)`. Add a test that runs the command with `--json` on the fixture data and compares the parsed output with `build_rows()`. Change nothing on the default path.
- **Verify:** `python3 -m pytest tools/report` → passes, including the unchanged snapshot test in `tools/report/tests/test_cli.py`
- **Kind:** code · **Size:** S · **Reversibility:** safe

### T3 — Document the flag
- **Depends on:** T2
- **Covers:** none — enabling: users can find the flag
- **Files:** `docs/report.md` (modify)
- **Do:** In `docs/report.md`, add a short "JSON output" section after the usage section: the `--json` flag, the output shape with one small example, and the note that decimal values are strings.
- **Verify:** `grep -c -- "--json" docs/report.md` → prints 2 or more
- **Kind:** docs · **Size:** S · **Reversibility:** safe

### Execution order
- Sequential: T1 → T2 → T3

## Open questions
None.

## Audit
Light review: one cold-read reviewer. Two findings, both checked against the code by the planner and applied; the changed card was re-read, and no recheck was run.

- [major] totals would have been written as floats and lost precision → the interface now writes `Decimal` values as strings, and T1 tests it.
- [minor] the empty report was undefined → edge case and T1 test added.

## Status
Approved by the user on 2026-09-30. Next: `/ship-execute docs/agent/plans/json-output-for-the-report-command.md solo`. Nothing blocked.

## Related
None.
