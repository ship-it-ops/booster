---
type: investigation
status: active
created: 2026-10-01
updated: 2026-10-01
author: claude-fable-5-1
tags: [ship-better-plans, audit, evaluation, personas, workflow, plan-linter]
importance: core
---

# Multi-persona audit and before/after evaluation of `ship-better-plans`

## Symptoms

`ship-better-plans` 1.0 was written in June 2026 for older models and an older harness. The user asked for a full audit and refresh, evaluated through multiple agent personas, so that the skill reliably produces the best execution plan.

## Method

1. **Persona audit of 1.0.** Six independent reviewers, each with one lens and no shared conclusions: prompt engineering for current models, a cold-start walkthrough as the agent following the skill (normal, plan mode, headless), the downstream executor, a staff engineer on planning method, an audit-harness red team, and daily developer experience.
2. **Baseline.** 1.0 planned two real scenarios in this repo (validate plugin command files in CI; migrate plugin symlinks to generated copies), unattended, with the review skipped. Each plan was judged by a cold-read executor and a grounding checker that verified its claims against the repository.
3. **Rewrite**, then the same six reviewers on the rewrite, then fixes, then three of them again on the final text.
4. **After.** The rewritten skill planned the same two scenarios under the same conditions and judges, twice (draft and final). Two further judges compared old and new plans blind, as X and Y.
5. **The audit script was run for real** four times: standard on an old-format plan, standard on a new-format plan, light, and recheck.

## Root Cause (the findings on 1.0)

90 findings, 14 critical. All six reviewers converged on the same core:

- **Tasks were not executable cold.** Tasks existed only as Mermaid node labels; the executor needs, per task, a prompt, acceptance criteria, a verify command and file paths. The dependency graph was stated three ways that could disagree.
- **Nothing was grounded.** Neither the planner nor the reviewers were required to check claims against the repository; the audit saw only pasted plan text. Open questions were an escape hatch for assumptions one grep would have settled.
- **Intake before discovery.** Eight fields, one question at a time, before any code was read; no approach checkpoint and no approval step outside plan mode.
- **The audit could not converge or be trusted.** Ultra re-read an unchanged plan with an exact-title dedup key and no round cap; the refute pass dropped findings on one uncertain vote; failed agents looked like a clean audit; the cost estimate could not be computed; there was no path without the Workflow tool.
- **No unattended path**, no right-sizing (every section mandatory), stale tool names (`Task`, `TodoWrite`), hand-off pointing at superpowers instead of `ship-execute`, and example plans that broke the skill's own rules.

## Fix

Version 2.0, described in [ship-better-plans-v2-refresh](../decisions/ship-better-plans-v2-refresh.md): discovery first and a single checkpoint; self-contained task cards; a deterministic plan linter; a rewritten review (repository-grounded reviewers, three-way verification, bounded ultra, recheck, light depth, Agent fallback); explicit draft and approval; three example plans that pass the linter; `ship-execute` 1.1.0 reading the new format.

### Results

Plans written unattended with no review, judged by the same two judges:

| Scenario | Skill | Cold executability | Blocking / costly ambiguities | Grounding | False claims / checked | Lines |
|----------|-------|--------------------|-------------------------------|-----------|------------------------|-------|
| Command validation | 1.0 | 6/10 | 1 / 5 | 8/10 | 2 / 53 | 382 |
| Command validation | 2.0 | 8/10 | 0 / 1 | 8/10 | 2 / 68 | 214 |
| Symlink migration | 1.0 | 5/10 | 2 / 9 | 8/10 | 2 / 56 | 348 |
| Symlink migration | 2.0 | 7/10 | 1 / 2 | 9/10 | 1 / 82 | 300 |

The remaining blocking ambiguity in the 2.0 migration plan is the plan's own `approval: draft`, which is the intended behaviour of an unattended run.

Blind pairwise comparison (old against the 2.0 draft, order randomized): the new plan was chosen in both scenarios at about 80% stated confidence. Executability 9 against 5 and 9 against 4. The old plans were rated higher on end-to-end proof (showing a new check fail before it passes, a real install before merge) and, in one scenario, on grounding; both points were folded into 2.0 (a new check must be shown failing; expected behaviours that rest on existing code are claims to check).

Reviewer findings by round, for the three reviewers present in every round (prompt, cold-start, executor): critical 6 → 1 → 0; major 29 → 19 → 14. All six reviewers: 90 findings with 14 critical on 1.0; 79 with 1 critical on the rewrite draft (the one critical, `ship-execute` not honouring the new format, was fixed by `ship-execute` 1.1.0).

Live runs of the review script on real plans:

| Run | Agents | Raised → after merge → serious confirmed | Subagent tokens | Time |
|-----|--------|------------------------------------------|-----------------|------|
| Standard, 1.0-format plan (script draft) | 11 | 20 → 12 → 3 (+3 downgraded to minor) | 1.1M | 12 min |
| Standard, 2.0-format plan (final script) | 12 | 33 → 16 → 3 (+1 downgraded) | 1.4M | 14 min |
| Light, 2.0-format plan | 1 | 2 raised, returned unverified | 0.14M | 6 min |
| Recheck, unrevised plan with two prior findings | 4 | both prior findings correctly reported unresolved; 5 new minor | 0.36M | 13 min |

Both standard runs independently found what the separate judges had found (a vacuous diff gate, a card pointing at "the reference implementation above", weak proof of a working install) plus findings the judges missed. No finding was dropped in either run, and verifiers corrected reviewers' overstatements in their evidence.

## What is still weak

- **Grounding without a review did not improve** (8 → 8, 8 → 9). The discovery rules help, but the grounding reviewer is what catches false claims; a plan written with review depth "none" is only lint-checked.
- **Plan mode and the interactive checkpoint were not exercised end to end.** Evaluation agents ran unattended without `AskUserQuestion`, `Agent` or `Workflow`; the interactive path is verified by reading and by the reviewers' walkthroughs, not by a live session.
- **The third reviewer round still found 14 major issues** in the final text. The cheap ones were fixed (recheck rules as one table, light-review findings, unattended detection, linter false positives, reference split into step-scoped files); the rest are narrower and listed in the session's evaluation data, not all addressed.
- **`ship-execute` has only had its plan contract updated.** Its pre-flight gate, tool names elsewhere and execution model are due their own refresh.
- **Review cost is real:** over a million subagent tokens for a full review of a 300-line plan.

## Prevention

- Refresh the remaining `ship-*` skills with the same loop: independent persona audit, a baseline run on real scenarios with blind judges, rewrite, re-audit, re-run. The loop found problems each author-only pass missed, including in the rewrite itself.
- Do not edit a file that a running evaluation agent is reading; it nearly contaminated the first audit of the review script.
- Mechanical properties belong in a checker with tests and a CI job, not in a prose self-check.
- Example plans are tested artifacts: CI lints them with the linter they illustrate.

## Related

- [ship-better-plans-v2-refresh](../decisions/ship-better-plans-v2-refresh.md) — the decisions this evidence produced
- [ship-better-plans-design-audit](ship-better-plans-design-audit.md) — the June 2026 audit of the 1.0 design
- [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md) — D1–D7
