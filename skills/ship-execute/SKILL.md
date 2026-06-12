---
name: ship-execute
description: >
  Use to EXECUTE an already-written implementation plan — typically a
  `ship-better-plans` plan at `docs/agent/plans/<slug>.md` — building it with a
  fleet of expert subagents, validating every step with real evidence (build +
  tests + acceptance criteria), then vetting the whole result before handing
  off. Triggers when a written plan exists and the user is about to execute it
  (chose "execute now" after `/ship-plan`, or says "execute the plan", "build
  it", "implement the plan"), and via the `/ship-execute` command. Runs the
  plan's task DAG — critical path sequential, independent branches in parallel
  via worktree-isolated agents — behind a mandatory confirmation gate before
  any code is written or command is run, and never opens a PR or pushes without
  explicit permission. For coding tasks it delegates depth to the `ship-code`
  skills (clean / tested / secure / debugged / devops) and `ship-reviewed-prs`
  for final review. Do NOT trigger for: planning new work (use
  `ship-better-plans`), trivial one-off edits, quick questions, or pure
  debugging of a single known bug; and do not run while in plan mode.
allowed-tools: Task, Workflow, Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion
---

## Purpose

Take a written plan and **make it real** — correctly, with evidence, and without surprises. `ship-execute` is the executor half of the `ship-better-plans` → `ship-execute` → `ship-code` family. It runs the plan's task DAG with a fleet of subagents, proves every step works before moving on, vets the whole result, and hands a finished branch to the user for review or PR.

It is **standalone** — it does not depend on the `superpowers` execution skills. For coding depth it delegates to the **`ship-code`** sibling marketplace. It **executes only**; planning is `ship-better-plans`.

---

## Entry points

- **Auto-trigger** — fires when a written plan exists and the user is about to execute it (e.g. picked "execute now" from `ship-better-plans`). On this path the [pre-flight gate](#stage-1--pre-flight) is mandatory.
- **`/ship-execute [plan-path]`** — explicit. Append `solo` to force sequential (no parallel fan-out).

---

## Hard rules (non-negotiable)

1. **Never act before the pre-flight gate.** No code written, no command run, until the user confirms at Stage 1.
2. **Never PR or push without a separate explicit yes.** The handoff menu asks; silence ≠ consent.
3. **Refuse to run in plan mode.** Plan mode forbids the writes/commands execution needs. If a plan-mode system reminder is present, explain and wait — do not partially execute.
4. **Evidence before advancing (E3).** A task is "done" only when its build/tests/acceptance criteria are green AND its review passed. No step advances on assertion alone.
5. **Escalate blockers, never paper over them.** A blocked or failing-after-rework task stops the affected branch and surfaces to the user; it is never silently skipped or faked.
6. **Degrade gracefully if `ship-code` is absent.** Detect it; if missing, warn once and fall back to the built-in lighter review rather than failing.

Full procedure, subagent prompts, status codes, and the worktree/merge protocol are in [`reference.md`](reference.md). Read it before the first run.

---

## The 5 stages

### Stage 1 — Pre-flight
- Load the plan (`docs/agent/plans/<slug>.md` by default). Parse: task DAG, FRs, acceptance criteria, per-task verification, subagent-delegation map. No plan? Suggest `/ship-plan` first; do not improvise a plan here.
- Check for plan mode (rule 3). Check `ship-code` availability (rule 6).
- Create a `docs/agent/status/` entry (coordination — sibling agents see the in-flight work).
- Set up an isolated branch (and worktrees for parallel branches).
- **Gate (mandatory):**
  ```
  "Execute <slug>: <N> tasks (<P> parallelizable), mode <dag|solo>.
   Will write code and run commands (build/tests/git) in <branch>.
   Estimated ~<X>k tokens. Proceed? (yes / dry-run / cancel)"
  ```

### Stage 2 — DAG execution (E2)
- Run the **critical path sequentially**. Run **independent branches in parallel** via the Workflow tool with `isolation: 'worktree'` (parallel code-writers must not share a tree). Reconverge at an **integration-merge gate** (see reference).
- **Fall back to sequential** automatically when the plan exposes no real parallel set, or when `solo` was passed.
- Each task is owned by a fresh subagent per the plan's delegation map (Explore / feature-dev / a `ship-code` skill).

### Stage 3 — Per-step gate (E3)
For every task, in order:
1. **Implement** — TDD where the plan specs tests (write failing test → make it pass).
2. **Run** — build/typecheck + the task's tests + its acceptance criteria. Must be green (verification-before-completion: read real output, never assume).
3. **Review** — delegate non-trivial changes to the right `ship-code` skill (see [delegation map](#ship-code-delegation)).
4. **Rework loop** — on fail, a bounded rework cycle (default 3 attempts); systematic-debugging discipline for bugs. Still failing → escalate (rule 5).

### Stage 4 — Final vetting (rubber-stamp, E5)
The work is stamped only when ALL hold:
- Full test suite green.
- Every acceptance criterion in the plan met (mapped, checked).
- `ship-reviewed-prs` returns **APPROVE** on the whole `BASE..HEAD` diff (multi-persona). Findings loop back to Stage 3.

### Stage 5 — Handoff (E5)
Present an **evidence summary** (what ran, what passed, diff stat, any deferred items) and offer:
```
[1] Review locally — show the diff / walk the changes
[2] Open a PR — REQUIRES explicit confirmation, then push + gh pr create
[3] Keep the branch as-is — stop here
[4] Discard — clean up branch/worktrees
```
Never choose [2] autonomously. On any path, update the plan status (executing → done) and capture decisions/scars discovered during execution.

---

## ship-code delegation

For coding tasks, delegate depth to the `ship-code` sibling skills:

| Change kind | Per-step review |
|-------------|-----------------|
| general code (naming, structure, errors) | `ship-clean-code` |
| tests / coverage | `ship-tested-code` |
| security-sensitive (auth, input, crypto, secrets) | `ship-secure-code` |
| bug fix / regression | `ship-debugged-code` |
| CI / IaC / Dockerfile / deploy | `ship-devops` |
| **final vetting (Stage 4)** | `ship-reviewed-prs` (orchestrates the above) |

Non-coding tasks (docs, config, content) skip code review but still run their relevant checks (link checks, linters, schema validation). If `ship-code` is not installed, warn once and use the built-in lighter review.

---

## Verification (self-check before handoff)

- Every task reached green run-evidence + passed review (no step advanced on assertion).
- Integration-merge gate passed for all parallel branches; no unresolved conflicts.
- Full suite green; every acceptance criterion checked off against its FR.
- `ship-reviewed-prs` APPROVE recorded (or the user explicitly waived it).
- Nothing pushed / no PR opened without an explicit yes.
- Plan status updated; status entry archived; outcome recorded.
