---
type: decision
status: active
created: 2026-10-04
updated: 2026-10-04
author: claude-opus-5-5
tags: [skill, plugin, execution, workflow, worktree, ship-family, ship-better-plans]
importance: core
---

# `ship-execute` 2.0: what changed from the 1.0 architecture, and why

## Context

Second skill in the `ship-*` refresh, done with the same loop as [ship-better-plans-v2-refresh](ship-better-plans-v2-refresh.md): six independent reviewers audited the existing skill, the existing skill was run on real work with independent judges, then rewrite, re-audit and re-run. The evidence is in [ship-execute-refresh-audit](../investigations/ship-execute-refresh-audit.md).

The 1.0 architecture is recorded as E1–E5 in [ship-execute-architecture](ship-execute-architecture.md). This note records what 2.0 keeps and what it revises.

## Decision

### Kept

- **E1 (standalone engine, sibling review skills for depth).** The sibling skills are now optional: a reviewer loads one when it is installed and reviews without it when it is not.
- **E2 (plan DAG, parallel worktrees, Workflow tool)**, with the mechanics that were missing now specified (X1, X2).
- **E3 (evidence before a task advances)**, made stricter (X3).
- **E4 (auto-trigger plus `/ship-execute`; a start confirmation always; push and pull request need a separate explicit yes; no plan mode).** The start confirmation stays mandatory in interactive use, as decided in June. It is now one question, asked after a read-only look and before anything changes.

### Revised

- **X1 — A deterministic plan reader.** `scripts/plan_tasks.py` parses the task cards, generates each task agent's briefing, computes the ready set, checks a task's commit against its card, and keeps the run ledger. Why: 1.0 left all of this to the model reading a long plan by eye, and the briefing existed only inside the parallel path's script.
- **X2 — An explicit git protocol.** One commit per task. Every task agent, alone or in a wave, works in an isolated worktree; its commit is checked, cherry-picked onto a `ship/<plan>` branch, and verified there; a commit whose check fails is reverted. Files are staged by path. Why: 1.0 never said to commit, so parallel work had no route back from its worktree (17 critical findings, most of them this), and the baseline run swept caches into commits with `git add -A` and rewrote history to remove them. A probe confirmed how isolation behaves: a worktree under `.claude/worktrees/` on a throwaway branch cut from the checked-out commit.
- **X3 — The orchestrator verifies; the task agent only claims.** The card's `Verify` is re-run on the execution branch before a task is marked done, the suite runs after each wave, and every task's `Verify` runs again at the end. The ledger refuses `done` without a verification note and a commit on the branch. Why: in 1.0 the evidence was a free-text string from the agent that did the work.
- **X4 — E5 revised: the final review is local.** 1.0 required a `ship-reviewed-prs` APPROVE on the diff before hand-off, but that skill reviews a GitHub pull request, which the skill's own rules forbid creating at that point. 2.0 uses an independent reviewer agent over the diff from the start commit, given the plan's criteria and non-goals, with fix rounds capped at two. `ship-reviewed-prs` is offered after the user opens a pull request. Per-task review is limited to `security`, `migration` and `infra` tasks.
- **X5 — A run ledger inside `.git`, and resume.** It replaces the `docs/agent/status/` entry, which dirtied the branch and was invisible to other sessions anyway. It records each task's state, commit, verification, worktree and branch, and the run's branch, start and baseline.
- **X6 — The plan and reality.** A card that contradicts the code or an existing test, or whose check cannot pass as written, returns `needs-decision` and goes to the user. One fresh retry for an ordinary failure, then `blocked`. The run continues with what does not depend on it. Plan corrections are a defined procedure with their own commit.
- **X7 — Gates are enforced by the ledger.** A gated task cannot be marked running, and its briefing cannot be written for an agent, until the user's answer is recorded for the card as it is now; an approval covers one dispatch; a gated task never appears in a parallel wave, and the wave script refuses a briefing that carries a gate line. A card with no `Reversibility` field stops execution.
- **X8 — The user's repository.** Uncommitted tracked changes stop the start and are never stashed. The uncommitted plan file straight after `/ship-plan` is committed as the branch's first commit. Discard deletes only what the run created and asks twice. A plan is marked `completed` only when it is.
- **X9 — Narrowed tool pre-approval.** `allowed-tools` lists the plan reader and the specific safe shapes of the git commands a run needs (no wildcard `git branch`, `git worktree`, `git restore` or `git add`) instead of bare `Bash`; worktree removal goes through the script's `cleanup`, so the plan's own commands (tests, builds, anything a plan author wrote) go through the user's normal permission mode.
- **X11 — E4 revised by the user (2026-10-04): "approve and build now" counts as the start confirmation.** When the user has just made that choice for the plan at the end of `ship-better-plans`, `ship-execute` shows its start summary and begins without a second question, unless its read-only look found something that needs a decision. In every other interactive case the start question is still asked.
- **X10 — An unattended mode.** With nobody to answer, an explicit invocation on an approved plan is the go-ahead; gated tasks are left for the user; nothing is pushed or discarded.

## Alternatives Considered

- **Sequential tasks in the main checkout, worktrees only for waves.** Simpler and cheaper per task, but it lets unverified commits land on the execution branch and leaves a failed task's debris in the user's checkout. Rejected after the second review round; kept only as the fallback when there is no Agent tool.
- **Merge worktree branches instead of cherry-picking.** Rejected: merges of single-commit throwaway branches add merge commits and make "one commit per task" harder to read and revert.
- **Undo a failed commit with `git reset --hard`.** Rejected in favour of `git revert`: reset in the user's checkout can destroy work if anything changed underneath.
- **Skip the start confirmation after any explicit `/ship-execute` on an approved plan.** Two reviewers asked for this. Not done in general: the question carries real information (branch, gates, agent count). The narrower case was accepted; see X11.
- **Keep the in-flight `docs/agent/status/` entry.** Rejected: see X5.

## Consequences

- A run needs git, and Python 3 for the plan reader. Each isolated task agent starts from a fresh checkout and pays the plan's setup cost; the start summary says how many.
- Plans in the old format, or with problems, are not executed by the card-based path; the user is offered a revision or a guarded step-by-step run.
- The skill ships 57 unit tests for the plan reader, run in CI together with a check that the reader accepts the planner's example plans, so the two skills cannot drift apart.
- The templates and the two old examples are gone; one example run replaces them.

## Revisit Triggers

- Per-task worktree setup makes small sequential plans slow → allow main-checkout execution for plans of a few small tasks, with the same acceptance checks.
- The commit check's file patterns produce false failures on real projects → make them configurable from the plan's conventions.
- The Workflow or Agent isolation behaviour changes (worktree location, branch naming, whether commits persist) → re-run the isolation probe and the live wave test.

## Related

- [ship-execute-refresh-audit](../investigations/ship-execute-refresh-audit.md) — the evidence behind the revisions
- [ship-execute-architecture](ship-execute-architecture.md) — E1–E5, the 1.0 decisions this note keeps or revises
- [ship-better-plans-v2-refresh](ship-better-plans-v2-refresh.md) — the plan format this executor reads
