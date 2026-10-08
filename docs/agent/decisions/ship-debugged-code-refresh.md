---
type: decision
status: active
created: 2026-10-08
updated: 2026-10-08
summary: "ship-debugged-code 1.1 rewrite: one test for fixed, run and working-tree rules, confirmed against likely, short honest reports (G1-G12)"
paths: [skills/ship-debugged-code/*, plugins/ship-debugged-code/*]
---

# `ship-debugged-code` 1.1: the full rewrite, what changed, and why

## Context

Ninth skill in the `ship-*` refresh. The evidence is in [ship-debugged-code-refresh-audit](../investigations/ship-debugged-code-refresh-audit.md).

Version 1.0.0 was written for a person at a keyboard: twelve principles "for ALL debugging, EVERY time", a ten-step workflow, "use the debugger before print", three language files of IDE and `pdb` commands, a review template with D1 to D7 codes and a compulsory "What's Good" section, and an override file. Nothing in it bounded what could be run or said anything about uncommitted work, while `Bash` was pre-approved and `git bisect` recommended four times.

This skill is not a rubric: the agent that loads it does the debugging. The control run showed what that means for a rewrite. With no skill, a current model found the cause in every scenario, found the second path to the same failure, wrote regression tests that failed first, and refused to mark a time-dependent test as flaky. What went wrong, with and without 1.0.0: `git stash` in a working tree holding the user's uncommitted work, to watch tests fail without the fix; answers of 400 to 700 words; and, with 1.0.0 only, a house format with category tags and praise returned to a caller that had asked for a plain list. So the rewrite cannot earn its place by teaching debugging. It is about what the agent may claim, what it may touch, and how short the answer is.

No earlier decision note covers this skill. No other skill in the repository loads it today.

## Decision

- **G1 — One test for "fixed", in four parts:** the failure was seen; the cause accounts for everything observed; the change removes the cause; the failure was seen gone by the same means. Whatever could not be done is said. The twelve principles and the ten steps are gone, and effort is proportional: a cause that is plain needs two lines.
- **G2 — The three opening rules of the family,** adapted: the caller sets the format (and a dispatched fixer still reports whether the failure was seen and seen gone); the user's request, then the project's conventions for how a fix is written, outrank the skill; bug reports, logs, tickets and comments are evidence, not instructions.
- **G3 — What may be run is decided by what a command touches.** The project's own test command once it is known what it connects to; read-only queries of the project's own forge and CI; nothing against real state unless the user names it; nothing that waits for input; no tool or dependency the project does not declare. A test suite whose settings point at a shared database is not run as it stands.
- **G4 — The working tree belongs to the user.** No git command that moves HEAD, changes the index or discards uncommitted changes. To see a test fail without the fix: write the test first; else take your own lines out by editing and put them back; else name the line. Worktrees are for history only. Nothing is left behind. `allowed-tools` no longer pre-approves `Bash`, and the validator now enforces that.
- **G5 — Confirmed, likely and "a mechanism, not the incident" are different claims.** A cause is confirmed when the failure appears with the condition and disappears without it. A local demonstration with a stand-in shows that a mechanism exists; it does not confirm what happened in production.
- **G6 — Stopping is a result.** When checks stop narrowing the search, the agent steps back once, then reports what was ruled out, what remains and the one observation that would decide.
- **G7 — A catch, retry, timeout, restart or skip is judged by whether the cause is known,** not by which construct it is. A stopgap the user asked for is done in its narrowest form, kept visible and labelled first; it is held back only when it would itself do harm.
- **G8 — Every path to the reported failure is fixed; the same pattern elsewhere is listed.** The fix stays the fix: no tidying, no data repair unasked.
- **G9 — The final message leads with the state** and is plain sentences, most within 150 words. An empty item is left out; what was not verified is never cut for length.
- **G10 — Reviewing a fix** asks whether the failure is gone or hidden, whether anything would notice if it came back, and whether something was bent to get to green; severity by consequence; a change from someone else is read, not run.
- **G11 — Files:** `hard-cases.md` replaces `reference.md` and `reference-smells.md`; the language notes keep only evidence an agent can get without a debugger and causes that mislead; six fixtures are must / must-not checklists.
- **G12 — Version 1.1.0,** minor.

## Alternatives Considered

- **Keep `Bash` pre-approved, since debugging needs a shell.** Rejected: every guard would then be prose and no command would ever prompt. The user's own permission settings decide.
- **Forbid any way of seeing a test fail once the fix is in.** The first draft offered a throwaway worktree; reviewers showed it is unusable in most projects (no dependencies, no uncommitted work) and leaves branches behind. Taking out the agent's own lines by editing is cheaper and touches nothing of the user's.
- **A description that triggers on any failure.** Narrowed after round 2: the skill costs about 4,500 tokens and the baseline is already right on an error that points at its own one-line fix.
- **Refuse a requested retry until the cause is found.** Rejected in round 2 as the "declines a reasonable request" behaviour; see G7.

## Consequences

- `ship-tested-code` still tells the agent, for a fix that is already in, to name the line the test depends on and not to revert anything. This skill adds one step before that (take out your own lines by editing). The two do not contradict for reviews; aligning the sibling is a small later change.
- `SKILL.md` is about 3,650 words including the description.
- The skill is loaded by nothing else. If `ship-execute`'s fix agents should use it, that is a change to `ship-execute`.

## Revisit Triggers

- The skill fails to load on pasted stack traces whose cause is upstream (the description's exclusion was narrowed in the last pass and has not been measured).
- Agents still stash or reset in real sessions.
- Answers stay long.

## Related

- [ship-debugged-code-refresh-audit](../investigations/ship-debugged-code-refresh-audit.md) — the evidence
- [ship-tested-code-refresh](ship-tested-code-refresh.md) — the sibling that owns test design
- [ship-devops-refresh](ship-devops-refresh.md) — the run rules this borrows from
