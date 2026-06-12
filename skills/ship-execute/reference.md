# ship-execute — Reference

Full execution procedure, subagent prompts, status codes, the worktree/merge protocol, and schemas. `SKILL.md` is the lean dispatcher; read this before the first run.

---

## Stage 1 — Pre-flight (detail)

1. **Resolve the plan.** Default `docs/agent/plans/<slug>.md`; accept an explicit path arg. Parse out:
   - the **task DAG** (tasks + dependencies + the parallelizable set + critical path),
   - **functional requirements** (FR-n) and **acceptance criteria** (mapped to FRs),
   - **per-task verification** strategy and **per-phase budgets**,
   - the **subagent-delegation map** (task → agent type).
   If the file has no DAG (e.g. a non-ship-better-plans plan), build a minimal linear DAG from its task list and tell the user you did.
2. **Plan-mode check.** If a plan-mode system reminder is present, STOP — explain that execution writes files and runs commands, which plan mode forbids, and wait for the user to exit plan mode.
3. **ship-code check.** Probe for the `ship-code` skills (e.g. is `ship-reviewed-prs` available?). Record availability; if absent, warn once and set the degrade flag.
4. **Isolation.** Create the working branch off the base branch. For parallel branches, prepare git worktrees (the Workflow tool's `isolation: 'worktree'` handles per-agent trees).
5. **Status entry.** Write `docs/agent/status/ship-execute-<slug>.md` (type: status, status: active, branch, agent id) so sibling agents see the in-flight work.
6. **Gate.** Show the mandatory confirmation (tasks, parallel count, mode, branch, token estimate). `dry-run` → walk the DAG + per-task plan without executing. `cancel` → tear down branch/worktrees and the status entry.

---

## Stage 2 — DAG execution (detail)

- **Topological order.** Compute ready-sets from the DAG. A task is ready when all its dependencies are merged into the integration branch.
- **Critical path** runs sequentially on the integration branch.
- **Independent branches** (a ready-set with >1 task and no inter-dependency) fan out via the Workflow tool, each task in its own worktree (`isolation: 'worktree'`). See `workflows/execute.workflow.js`.
- **Sequential fallback.** If no ready-set ever has >1 independent task, or `solo` was passed, run everything sequentially on the integration branch — skip worktrees entirely.

### Integration-merge gate

When a parallel set completes, merge each branch back into the integration branch **one at a time**, in dependency-stable order:
1. Merge branch → if conflict, hand the conflict to a fresh resolver subagent with both sides + the relevant FRs; never auto-resolve blindly.
2. After each merge, **re-run the affected tests** (a clean per-branch result does not prove the merged result — verification-before-completion).
3. Only when the integration branch is green does the next dependent set become ready.

---

## Stage 3 — Per-step gate (detail)

Each task runs as a fresh subagent. Give it the task text, its FRs/acceptance criteria, and the relevant file paths (do NOT make it re-read the whole plan). The loop:

1. **Implement.** If the plan specs tests for this task: TDD (write the failing test, see it fail, make it pass, refactor). Otherwise implement, then add the tests the acceptance criteria imply.
2. **Run (evidence).** Execute the task's verification: typecheck/build, the task's tests, and a check of each acceptance criterion. Capture real command output + exit codes. Green is required.
3. **Review.** For non-trivial changes, delegate to the matching `ship-code` skill (see SKILL.md delegation map). Address P1/Tier-1 findings before advancing; record minor ones.
4. **Rework loop.** On any red, loop (default `MAX_REWORK = 3`). For bugs, apply systematic-debugging (root cause before fix; no random patches). Past the limit → mark the task `BLOCKED` and escalate.

### Subagent status codes

Each task subagent returns one of:
- `DONE` — implemented, run-green, review-clean.
- `DONE_WITH_CONCERNS` — green, but carries non-blocking notes (record them for Stage 4).
- `NEEDS_CONTEXT` — missing info/decision; ship-execute gathers it (or asks the user) and re-dispatches.
- `BLOCKED` — cannot proceed after rework; stops the affected branch and escalates to the user with the evidence.

---

## Stage 4 — Final vetting (detail)

Rubber-stamp requires all of:
- **Full suite green** — run the project's complete test/build, read the output.
- **Acceptance audit** — every FR's acceptance criteria explicitly checked against the working tree.
- **`ship-reviewed-prs` APPROVE** — dispatch it on the full `BASE..HEAD` diff. It runs its multi-persona review (SE/SC/IN/+conditional) and returns a deterministic verdict. `REQUEST_CHANGES` → route each finding back into Stage 3's rework loop, then re-vet. Only `APPROVE` (or an explicit user waiver) clears the stamp.

If `ship-code` is absent: run the built-in fallback review (a focused multi-lens self-review for correctness, security, and tests) and clearly label the result as the lighter fallback.

---

## Stage 5 — Handoff (detail)

Assemble the **evidence summary**:
- tasks completed / total, with each one's run-evidence (the command that proved it).
- full-suite result, acceptance-criteria checklist, `ship-reviewed-prs` verdict.
- `git diff --stat` for `BASE..HEAD`, and any `DONE_WITH_CONCERNS` / deferred items.

Then the options menu (review / PR / keep / discard). **PR path:** confirm explicitly, then push and `gh pr create` with a body summarizing the plan + evidence (no co-author line — repo norm). **Discard:** remove branch + worktrees + the status entry.

On completion: flip the plan's frontmatter `status` to `completed`, move the `status/` entry to `archive/` (or delete), and capture anything durable — a decision made mid-execution → `docs/agent/decisions/`; a sharp lesson → `docs/agent/scars/`.

---

## Schemas

```javascript
// TASK_RESULT_SCHEMA — what each task subagent returns
{
  type: 'object',
  properties: {
    taskId:   { type: 'string' },
    status:   { type: 'string', enum: ['DONE', 'DONE_WITH_CONCERNS', 'NEEDS_CONTEXT', 'BLOCKED'] },
    evidence: { type: 'string' },                 // the command(s) run + result that prove it
    concerns: { type: 'array', items: { type: 'string' } },
    filesTouched: { type: 'array', items: { type: 'string' } }
  },
  required: ['taskId', 'status', 'evidence']
}

// MERGE_RESULT_SCHEMA — integration-merge gate
{
  type: 'object',
  properties: {
    branch:    { type: 'string' },
    merged:    { type: 'boolean' },
    conflicts: { type: 'array', items: { type: 'string' } },
    testsGreen:{ type: 'boolean' }
  },
  required: ['branch', 'merged', 'testsGreen']
}
```

---

## Anti-patterns (do not do)

- Writing code or running commands before the Stage-1 gate.
- Opening a PR or pushing without an explicit, separate yes.
- Running in plan mode (refuse and wait).
- Advancing a task on a subagent's word without green run-evidence.
- Auto-resolving a merge conflict without understanding both sides.
- Silently skipping a BLOCKED task to keep the run "green".
- Re-using one worktree across parallel code-writers.

---

## Related skills

- `ship-better-plans` — produces the plan this consumes (the task DAG, FRs, acceptance criteria).
- `ship-agent-context` — the `docs/agent/` substrate (status entry, outcome capture).
- `ship-code` (sibling marketplace): `ship-clean-code`, `ship-tested-code`, `ship-secure-code`, `ship-debugged-code`, `ship-devops`, `ship-reviewed-prs` — coding-depth and final-vetting delegates.
