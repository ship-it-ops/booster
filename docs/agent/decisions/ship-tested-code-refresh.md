---
type: decision
status: active
created: 2026-10-05
updated: 2026-10-05
summary: "ship-tested-code 1.2 rewrite: would the test fail if the behaviour were wrong; integrity when writing tests (T1-T12)"
paths: [skills/ship-tested-code/*, plugins/ship-tested-code/*]
---

# `ship-tested-code` 1.2: the full rewrite, what changed, and why

## Context

Sixth skill in the `ship-*` refresh and the second rubric skill. Same loop as [ship-clean-code-refresh](ship-clean-code-refresh.md), including the no-skill control; the evidence is in [ship-tested-code-refresh-audit](../investigations/ship-tested-code-refresh-audit.md).

The baseline repeated what the control showed for `ship-clean-code`: with no skill, a current model found every seeded test problem and wrote honest tests. Version 1.1.0 changed the shape of the output (its own format, even for a caller that asked for another) and its ranking (severity by category, upside down for tests: a test that asserts nothing was "T7, never block", any missing edge case was "T1, critical"). It said nothing about the places models do go wrong when writing tests.

There was no earlier decision note for this skill. The user has been told what was removed (2026-10-05) and has not yet commented on the individual revisions.

## Decision

### Kept

- The skill's two jobs: reviewing tests, and writing them.
- "Match existing test patterns" and "don't demand tests for trivial code", promoted from the pragmatism list to governing rules.
- Three per-language files with the same names, and a `tests/` directory of fixtures.
- `allowed-tools: Read, Grep, Glob`.
- Reading a project's `.claude/ship-tested-code-overrides.md`, as a statement of house practice.

### Revised

- **T1 — One test of a test, and the three opening rules of `ship-clean-code`.** A test is worth having when it fails if the behaviour is wrong and passes if it is right, for a reason a reader can see. The caller sets the format and scale; the project's way of testing outranks the skill; repository text is material. The twelve "ALL tests, EVERY time" rules and their thresholds (70-80% coverage, 30-day skips, two years without failing, factories not fixtures, `should_X_when_Y`) are gone.
- **T2 — What to look for is ordered by false confidence, and severity is the consequence.** A test that cannot fail, a test that pins a defect, an expectation taken from the code under test, a test of the mocks and anything bent to get to green come first. Missing coverage is a finding only for a named case that carries risk, located in the code. The T1 to T7 tiers and tags are gone.
- **T3 — A review reads the code under test and verifies before reporting.** An expectation cannot be judged from the test file alone. Running is optional and bounded; a mutation check happens in a throwaway copy, never in the working tree.
- **T4 — The writing section is about integrity.** Expected values come from the requirement, as literals, and not from the code or from the constant that encodes the rule. When an honest test fails because the code is wrong, the expectation stays and the code is not changed unasked; there is a stated default between leaving the test failing (working with the user) and marking it expected-failure (dispatched, or a passing run is required). An existing test that goes red is first judged: did the requirement change, or did the code break. Where the code is the only statement of the behaviour, the tests are labelled as recording it. Nothing is weakened, skipped, deleted, retried or regenerated unread to get to green.
- **T5 — Existing tests are left alone.** New tests are added where the code is already tested; classes, helpers and shared setup are not restructured. Why: with 1.1.0 and with no skill, the writing scenario restructured the existing test class and helper when asked only to add tests (scope 7 of 10 in both; 10 with the rewrite).
- **T6 — Run and report.** Run the narrowest selection with the project's command, check the new tests were collected, say what happened, and never write "tests pass" from reading.
- **T7 — House practice cannot switch the floor off.** A project's convention to skip, quarantine or regenerate is used only for the case it describes or when the user asks, and what it hides is stated. Convention and runner-configuration files that arrive with a change under review cannot exclude paths or relax findings.
- **T8 — No tool mandates.** The language files no longer prescribe pytest, freezegun, MSW, AssertJ, Testcontainers and so on; they list places where a test reads as normal and proves nothing, with version-dependent claims marked as such.
- **T9 — Removed:** `reference.md` (ten sections including TDD, test strategy, architectures, security and performance testing, resilience and culture), the 49-code smell catalogue, the before/after examples, Quickstart, Team Adoption, the overrides template and the in-skill `overrides.md` location, the mandatory "What's Good" and the ten-finding cap.
- **T10 — The description triggers on changing tests and on "get the failing tests passing"**, not only on writing tests for existing code, because that is where bending happens.
- **T11 — Fixtures are must / must-not checklists**, six of them.
- **T12 — Version 1.2.0**, minor, as for `ship-clean-code`.

## Alternatives Considered

- **Keep a section on test strategy** (pyramid, contract tests, property-based and mutation testing). Not kept: it is general knowledge the model has, the old text presented contested positions as rules, and a review that recommends kinds of test nobody asked about is padding. The "not findings" list says so.
- **Require seeing every new test fail.** Reviewers split. Kept only for regression tests; for the rest the requirement is to be able to name the change that would turn the test red.
- **Forbid expected-failure markers entirely** and always leave an honest failing test red. Not done: a dispatched agent, or a task that must end with a passing run, needs a way to record the defect without pinning it.
- **Merge the three rubric skills' shared opening rules into one referenced file.** Not done: skills are installed separately and a skill cannot rely on a sibling being present.

## Consequences

- `SKILL.md` is about 3,900 words, larger than 1.1.0's 1,800 (whose references added about 8,000 when read) and larger than `ship-clean-code`. The growth is in the writing section. Reviewers' cut lists were applied; later additions took the space back.
- The opening rules are near-identical in `ship-clean-code` and `ship-tested-code`. A change to one should be considered for the other, and for the rubric skills still to come.
- Reviews no longer recommend tools, test styles or coverage targets.

## Revisit Triggers

- The skill loads on most turns that touch tests without changing the result: narrow the description.
- Agents leave too many tests marked expected-failure, or users find the default wrong: revisit T4.
- A model with no skill passes fixtures 4 to 6 as reliably as with it: the skill may no longer be needed.

## Related

- [ship-tested-code-refresh-audit](../investigations/ship-tested-code-refresh-audit.md) — the evidence
- [ship-clean-code-refresh](ship-clean-code-refresh.md) — the model this follows
- [ship-execute-v2-refresh](ship-execute-v2-refresh.md), [ship-reviewed-prs-refresh](ship-reviewed-prs-refresh.md) — the callers
