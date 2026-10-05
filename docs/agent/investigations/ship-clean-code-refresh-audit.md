---
type: investigation
status: active
created: 2026-10-05
updated: 2026-10-05
summary: "ship-clean-code audit: six reviewers, three judged scenarios, a no-skill control, three rounds"
---

# Multi-persona audit and before/after evaluation of `ship-clean-code`, with a no-skill control

## Symptoms

`ship-clean-code` 1.1.0 was written in early 2026 and migrated here unchanged. The user asked for the same full audit and rewrite the four previous skills got. The hand-off also noted that `ship-reviewed-prs` now ignores the rubric skills' finding codes, severity tiers and output format, and that the rubrics still describe a world in which they own those.

## Method

1. **A fixture library** (`docs/agent/references/refresh-eval/clean-code-fixture/`): a small Python invoicing library whose `CONTRIBUTING.md` states conventions that contradict generic clean-code rules (lookups return `None`, state-changing functions take five parameters, time comes from a clock argument, money is integer cents). Ground truth is kept away from the agent under test.
2. **Three scenarios**, each judged by an agent that had the ground truth and did not know what instructions the worker had:
   - *review a file* with seven seeded defects (an off-by-one on exact payment, a swallowed failure reported as success, a mutable default, a query that mutates and sends reminders, float tax in a cents field, wall-clock time, a third copy of a calculation that had drifted) and five decoys that a rulebook flags and the project does on purpose;
   - *write a feature* (void an invoice) in that file without being asked to clean it;
   - *review one commit* as a reviewer dispatched with `ship-execute`'s prompt and answer format, with four seeded problems (a crash in December, a requirement not implemented, hollow tests, an unrequested constant change) and older defects next to the diff.
3. **A control**: every scenario also run with no skill loaded.
4. **Six reviewers**, one lens each, blind to each other: prompt engineering for current models; a cold-start walkthrough (feature work, a file review, dispatched by `ship-execute`); the consumer (the calling skills, and the developer who receives a review); a staff engineer on the content; a red team; daily developer experience.
5. **Rewrite**, all six reviewers and the three scenarios again; fixes; three reviewers (prompt, cold-start, red team) and the scenarios on the revised text; a last round of fixes that was not re-audited.
6. **Three of the new fixtures run with fresh agents**, with and without the skill, on the final text.

The workflow script is [`eval-ship-clean-code.workflow.js`](../references/refresh-eval/eval-ship-clean-code.workflow.js); `build.sh` in the fixture directory builds the three repositories.

## Root Cause (the findings on the existing skill)

81 findings, 17 critical. The reviewers converged on:

- **Absolute rules outranked the project.** "These 12 rules apply to ALL code, ALL languages, EVERY time", with a hard ceiling of 50 lines, at most three arguments, never return null, never a boolean flag, every literal a named constant. The pragmatism section that contradicted them came later and exempted none.
- **No rule that a caller's format wins**, although both calling skills require it. The fixed template had no file path, no confidence and no blocking mark.
- **Severity was the category.** Every "P1" was critical, including unreachable code; a compatibility break was "P5" and could not be.
- **No scope and no verification.** A commit review became a whole-file audit; line numbers, fixes with code and a severity were demanded for every finding with no step to check any of it.
- **The examples and fixtures were not good reviews.** They missed real defects, misnumbered lines, praised a broken line under the compulsory "What's Good", and the before/after examples changed public contracts.
- **Writing mode said "apply all principles" and "without commentary"**, which is how an unrequested refactor reaches a diff unannounced.
- **Override files were read from the repository under review** and could disable any rule.
- The same rule was stated in up to six places and the places disagreed; a third of `SKILL.md` addressed a human team lead; the text cited a slash command that does not exist and a delegation from `ship-reviewed-prs` that was never true.

## Fix

The rewrite, released as 1.2.0, described in [ship-clean-code-refresh](../decisions/ship-clean-code-refresh.md).

### Results

Judged scenarios (scores out of 10). "None" is the model with no skill.

| Scenario | Measure | 1.1.0 | None | Rewrite, first draft | Rewrite, revised |
|----------|---------|-------|------|----------------------|------------------|
| Review a file | Detection | 10 | 10 | 10 | 10 |
| Review a file | Precision | 8 | 9 | 9 | 9 |
| Review a file | Priority | 7 | 9 | 9 | 9 |
| Review a file | Actionability | 9 | 9 | 9 | 9 |
| Review a file | Proportion | 6 | 8 | 8 | 8 |
| Write a feature | Correctness | 9 | 9 | 9 | 9 |
| Write a feature | Conventions | 9 | 9 | 10 | 9 |
| Write a feature | Scope | 10 | 9 | 10 | 10 |
| Write a feature | Surfacing existing problems | 8 | 7 | 10 | 10 |
| Write a feature | Communication | 9 | 8 | 9 | 8 |
| Review a commit | Detection | 10 | 10 | 10 | 10 |
| Review a commit | Precision | 9 | 10 | 10 | 9 |
| Review a commit | Caller's format | 4 | 9 | 9 | 9 |
| Review a commit | Scope | 10 | 10 | 10 | 9 |
| Review a commit | Proportion | 6 | 8 | 8 | 8 |

Read this table for what it says and no more. Detection was 10 in all twelve runs: on these fixtures the model finds the defects and the skill does not. 1.1.0 was worse than no skill on format, priority and proportion. The rewrite removes that harm and is level with no skill on reviewing; its measurable gain is on the writing path, where it told the user about existing defects that interact with the new feature and left them alone. Differences of one point between single runs are noise.

The new fixtures, run on the final text with fresh agents:

| Fixture | With the skill | With no skill |
|---------|----------------|---------------|
| 4, commit reviewed for a calling agent | All four must-find items, the steering comment reported and not obeyed, the caller's format with no skill vocabulary, the older defect as one labelled line | not run (the commit scenario above is the control) |
| 5, small change | Two lines changed; reported the silently dropped rows next to the change | Two lines changed; did not mention the dropped rows |
| 6, open-ended clean-up | Changed nothing, proposed four changes with reasons and what each would do to callers | Deleted the apparently unused function and the commented line, renamed locals, re-wrapped a line |

Fixture 6 with the skill was over-cautious about the commented-out line; the text now says commented-out code can go in a clean-up.

Reviewer findings: all six reviewers, 81 with 17 critical on 1.1.0; 73 with none critical and 30 major on the first rewrite. The three reviewers present in every round (prompt, cold-start, red team): critical 8, 0, 0; major 27, 11, 12. The third round's majors were new ones the second round's fixes exposed (the clean-up default contradicting "behaviour stays the same", the two-level mapping overriding a caller's definition of blocking, a writing trigger no request would match, standing disclaimers as a new form of padding); all were fixed in the last pass.

Cost: 1.40, 0.92 and 0.66 million subagent tokens for the three rounds, plus about 0.3 million for the five fixture runs.

## What is still weak

- **Nothing has run through an installed plugin.** Evaluation agents were given the skill's path and told it was loaded. Whether the new description triggers on ordinary feature work, and how often, is untested; that is the one thing the fixtures README asks a person to record.
- **The last round of fixes was not re-audited**, beyond the three fixture runs: the caller's-definition rule for blocking, the behaviour-neutral clean-up default, the private-only rule for removing code a change orphaned, the bounded running of code, the conditional closing line, and the trimmed look-for list.
- **Single runs.** Each cell in the table is one run and one judge.
- **Python only in the scenarios.** The TypeScript and Java notes were reviewed by the staff reviewer and corrected, not exercised; fixture 2 is TypeScript and was not run.
- **`SKILL.md` grew to about 3,400 words** against 1,800 for 1.1.0 (whose references added another 9,000 or so when read). Two reviewers proposed cuts of 200 to 350 words; about half were taken.
- **Not done**, from the reviewers: a fixture where the change itself edits `CONTRIBUTING.md` or adds an overrides file; neighbouring files in fixture 5 beyond one caller; a note in the default report naming the skill so a user can tell it ran.
- **The other rubric skills still refer to this one in the old terms** (`ship-tested-code`, `ship-debugged-code`, `ship-devops` say "invoke `ship-clean-code`" for naming and SRP). Harmless, and theirs to fix in their own refresh.

## Prevention

- Run a no-skill control. Without it this audit would have credited the old skill with the model's own detection, as the earlier audits' notes suspected.
- For a rubric skill, judge what the text changes, not what the output contains. Fixtures a bare model passes can only show harm.
- A capable model also hides a skill's contradictions: both 1.1.0 runs listed the instructions they could not follow and worked around them.

## Related

- [ship-clean-code-refresh](../decisions/ship-clean-code-refresh.md) — the decisions this evidence produced
- [ship-reviewed-prs-refresh-audit](ship-reviewed-prs-refresh-audit.md) — the previous audit, same method without the control
