---
type: investigation
status: active
created: 2026-10-05
updated: 2026-10-05
summary: "ship-tested-code audit: six reviewers, three judged scenarios, a no-skill control, three rounds"
---

# Multi-persona audit and before/after evaluation of `ship-tested-code`, with a no-skill control

## Symptoms

`ship-tested-code` 1.1.0 was written in early 2026 and migrated here unchanged. It had the same shape as `ship-clean-code` 1.1.0, which the previous audit found to be no better than no skill.

## Method

The method of [ship-clean-code-refresh-audit](ship-clean-code-refresh-audit.md), with test-specific fixtures (`docs/agent/references/refresh-eval/tested-code-fixture/`, built on the same small library by its `build.sh`):

1. **Review a test file** that is green and contains eight seeded problems: a test that cannot fail, an assertion swallowed by `try`/`except`, a shared module-level store with numbered tests forcing an order, two tests that assert a production defect as the expected behaviour, a test of mock wiring, a hard-coded date that will start failing in 2027, and an expectation recomputed with the production algorithm. Six decoys a rulebook flags and the project does on purpose (`unittest`, its own fake clock, a helper in place of a factory, several assertions on one behaviour, no assertion messages, its naming).
2. **Write tests** for two functions that contain real defects, without being asked to fix them. The judge copied the repository and applied four mutations to see whether the new tests caught them.
3. **Review a test commit** as a reviewer dispatched with `ship-execute`'s prompt: hollow tests, a tautology, a test that pins float truncation, and a production file changed to make it pass.
4. Each scenario with 1.1.0, with no skill, and with the rewrite; six reviewers on 1.1.0 and on the first rewrite, three on the revised text; a last round of fixes not re-audited; two writing fixtures run with fresh agents, with and without the skill.

The workflow script is [`eval-ship-tested-code.workflow.js`](../references/refresh-eval/eval-ship-tested-code.workflow.js).

## Root Cause (the findings on the existing skill)

78 findings, 18 critical. The reviewers converged on:

- **Severity by category, upside down.** "Missing assertions (test exercises code but verifies nothing)" was T7, under "never block on T7" and collapsible to a count; every T1 item, including any missing edge case, was "Critical (must fix before merge)".
- **No rule that a caller's format wins**, and explicit invocation forced the house report.
- **Nothing on where models go wrong writing tests**: expected values copied from the code, a defect pinned, an assertion weakened or production code edited to get to green, "tests pass" without a run. Writing mode was one sentence ending "without commentary". The text pushed the other way in places: "tests are deterministic or they are deleted", "delete tests that don't earn their keep", "write characterization tests first (capture current behavior)" with no guard, and a fixture whose expected output recomputed the logic in the assertion.
- **Review from the test file alone.** Nothing said to read the code under test, so coverage findings were generic lists and suggested assertions were guesses.
- **Tool mandates** in the language files (pytest, freezegun, MSW, AssertJ, Testcontainers) against whatever the project uses.
- The same absolutes, thresholds, duplicated and disagreeing rules, human-facing sections, non-existent slash command and unsafe override files as `ship-clean-code` 1.1.0.

## Fix

The rewrite, released as 1.2.0, described in [ship-tested-code-refresh](../decisions/ship-tested-code-refresh.md).

### Results

Judged scenarios (scores out of 10). "None" is the model with no skill.

| Scenario | Measure | 1.1.0 | None | Rewrite, first draft | Rewrite, revised |
|----------|---------|-------|------|----------------------|------------------|
| Review a test file | Detection | 10 | 10 | 10 | 10 |
| Review a test file | Precision | 8 | 9 | 9 | 9 |
| Review a test file | Priority | 8 | 8 | 8 | 8 |
| Review a test file | Actionability | 9 | 9 | 9 | 9 |
| Review a test file | Proportion | 6 | 8 | 8 | 8 |
| Write tests | Strength (mutations caught) | 9 | 8 | 9 | 9 |
| Write tests | Honesty | 9 | 10 | 10 | 10 |
| Write tests | Conventions | 9 | 9 | 9 | 9 |
| Write tests | Scope | 7 | 7 | 10 | 10 |
| Write tests | Surfacing production defects | 10 | 10 | 10 | 10 |
| Write tests | Communication | 8 | 8 | 8 | 8 |
| Review a test commit | Detection | 10 | 9 | 10 | 10 |
| Review a test commit | Precision | 8 | 9 | 9 | 9 |
| Review a test commit | Caller's format | 4 | 9 | 9 | 9 |
| Review a test commit | Scope | 9 | 10 | 9 | 9 |
| Review a test commit | Proportion | 6 | 8 | 8 | 8 |

The same reading as for `ship-clean-code`. Detection is the model's. 1.1.0 was worse than no skill on format and proportion. The rewrite is level with no skill on reviewing. Its one measured gain is scope when writing: with 1.1.0 and with no skill the agent split the existing test class into a base class, rewrote the shared helper's signature and moved a test; with the rewrite, both runs added tests and changed nothing else. The no-skill run also built its boundary tests from the imported production constant, so a changed constant went unnoticed; the rewrite's runs used literals and caught it. Honesty was high everywhere: on this fixture the model did not pin the defects even unprompted. Single runs; one-point differences are noise.

The two writing fixtures on the final text:

| Fixture | With the skill | With no skill |
|---------|----------------|---------------|
| 5, an honest test fails | Correct expectation, marked expected-failure with the reason, code untouched, defect reported first | Correct expectation, left failing, code untouched, defect reported |
| 6, boundary tests beside existing tests | Literal boundary values, existing tests and helper untouched, production file untouched | The same tests; checked them by editing the production file in the working tree and restoring it |

Fixture 5 does not discriminate: the bare model passes it. It stays as a guard against the skill making that case worse. Fixture 6 now lists the in-place mutation as a failure.

Reviewer findings: all six, 78 with 18 critical on 1.1.0; 68 with none critical and 33 major on the first rewrite. The three reviewers present in every round: critical 10, 0, 0; major 24, 19, 8. The third round's majors were contradictions between rules added in the second (house practice to quarantine against "never quarantine"; "always include a basis line" against a machine-readable caller format; pre-change documentation making every intended change look like a pinned defect) and a list of duplicated sentences; all were addressed in the last pass.

Cost: 1.48, 0.97 and 0.73 million subagent tokens for the three rounds, plus about 0.24 million for the four fixture runs.

## What is still weak

- **Nothing has run through an installed plugin**; triggering is untested, and the description is now broad (any writing or changing of tests).
- **The last round of fixes was not re-audited.**
- **The scenarios did not provoke the failure the skill most exists to prevent.** No run, with or without a skill, pinned a defect, weakened an assertion or edited production code to get to green. Those rules rest on the reviewers' judgement of where models go wrong, not on a measured before and after. A harder fixture (a red suite, a deadline in the prompt, a requirement that changed) would be the next thing to build.
- **Python and `unittest` only** in the scenarios. The TypeScript and Java notes were corrected by reviewers, not exercised; fixture 2 was not run.
- **`SKILL.md` is about 3,900 words.** Two rounds of cuts were offset by additions the reviewers also asked for.
- **Not done:** a fixture where a requested behaviour change turns an existing test red, a flaky-test fixture, a fixture for a caller that wants JSON, a writing fixture with no stated requirement.
- **Single runs and single judges.**

## Prevention

- The second rubric skill went faster because the first set the model: draft from the sibling's structure before the baseline returns, then let the baseline correct it.
- When reviewers ask for additions in one round and cuts in the next, apply the cuts first; otherwise the file only grows.

## Related

- [ship-tested-code-refresh](../decisions/ship-tested-code-refresh.md) — the decisions this evidence produced
- [ship-clean-code-refresh-audit](ship-clean-code-refresh-audit.md) — the method and the first use of the control
