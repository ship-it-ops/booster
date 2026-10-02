---
type: plan
status: active
approval: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: <agent-id>
tags: [list, of, tags]
importance: standard
plan_format: 2
base: <branch>@<short-sha>
---

# Plan: {title}

<!-- Delete every comment like this one as you fill the section in. A section that does not apply reads "N/A — reason". -->

## Summary
<!-- 3–5 sentences: what gets built, the chosen approach, the biggest risk, how we will know it is done. Someone who reads only this section knows the plan. -->

## Context
- **Problem:** the observable gap, stated without solution language
- **Why now:** what it costs to leave it, or "not stated"
- **Request:** the user's request, quoted, so the plan can be checked against it

## Success criteria
<!-- Outcomes the user stated or confirmed, each one checkable. Everything below traces back to these. -->
- SC-1: …

## Non-goals
- …

## Constraints
- …

## Facts and assumptions
<!-- What the plan relies on. A fact carries evidence from this session: a path:line you opened, or a command you ran and its result. An assumption says what breaks if it is wrong and what settles it. -->
- F-1: … — `path/to/file.ts:42`
- F-2: … — ran: `command` → result
- A-1: … — if wrong: … — settled by: T1 (spike) | OQ-1 | accepted by the user

## Approach
<!-- Real candidates only. With a single viable approach, drop the table and say which constraint rules out the rest. -->
| Option | Meets the success criteria? | Effort | Main risk | Reversibility | Verdict |
|--------|-----------------------------|--------|-----------|---------------|---------|
| A …    | …                           | S/M/L  | …         | …             | chosen / rejected because … |

- **Chosen:** … — **deciding factor:** …
- **Builds on:** existing code this reuses, with paths

## Risks and rollback
<!-- Each risk points at what handles it: a task, a check, or the user's acceptance. -->
| Risk | Why it matters | Handled by | How we would notice |
|------|----------------|------------|---------------------|
| …    | …              | Tn / AC-n / accepted by the user | … |

- **Rollback:** how to undo the change after it ships
- **Migration:** only when live data, state or schema changes: the order of steps and the way back

## Specification

### Requirements
<!-- A small plan may skip requirements and let acceptance criteria verify the success criteria directly. -->
- FR-1: … (SC-1)

### Acceptance criteria
- AC-1 (FR-1): … — verify: `command`, a named test, or what to observe

### Non-functional targets
<!-- Only the ones that apply, each with a number and where the number came from. Otherwise: N/A — reason. -->

### Interfaces and data shapes
<!-- For each boundary the work adds or changes: inputs, outputs, errors. -->

### Edge cases
| Case | Expected behaviour | Covered by |
|------|--------------------|------------|
| …    | …                  | AC-n / Tn / out of scope because … |

## Verification
<!-- Commands are run from the repository root, exactly as written, including any package filter. -->
- **Setup:** what a fresh checkout needs before anything runs (install, env files, services)
- **Commands:** build `…` · test `…` · lint `…` — defined in (package.json, Makefile, CI workflow)
- **Baseline:** what those commands reported before this work, or "not run" and why
- **Final check:** how each success criterion is demonstrated once every task is done, and by whom if it needs a person or an environment

## Tasks
<!-- A task agent receives its card, the conventions block, and the text of each id in Covers. Nothing else. -->

### Conventions for every task
<!-- Rules every task agent must follow (setup, commit message style, banned dependencies, code conventions). -->
- …

### T1 — {task title}
- **Depends on:** none
- **Covers:** FR-1, AC-1
- **Files:** `path/a.ts` (modify), `path/b.ts` (new)
- **Do:** what to build; the context needed to build it (the interface, the existing pattern to follow and where it lives, decisions already made); which tests to write; what to leave alone.
- **Verify:** `command` → expected result
- **Kind:** code · **Size:** S · **Reversibility:** safe
<!-- When Reversibility is anything but safe, add: - **Gate:** what a person confirms before this task runs -->

### Execution order
<!-- Paste the output of `lint_plan.py --dag`. The cards above are authoritative; this is derived from them, and the linter rejects it when it is stale. -->

## Open questions
<!-- "None" is a fine answer. A blocking question stops approval until it is answered. -->
- OQ-1 (blocking | non-blocking): … — default if unanswered: …

## Audit
<!-- Depth and reviewers run; each confirmed finding with its disposition (fixed in …, accepted by the user, rejected because …); anything the review did not cover. Or: none, by the user's choice. -->

## Status
<!-- Draft → approved → executing → done. What is next, what is blocked. Corrections found during execution are added here with a date. -->

## Related
- Link related notes, e.g. `[slug](../decisions/<slug>.md)` — why related
