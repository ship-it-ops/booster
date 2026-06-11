---
type: decision
status: active
created: 2026-06-11
updated: 2026-06-11
author: claude-opus-4-8
tags: [skill, plugin, execution, workflow, ship-family, ship-code]
importance: core
---

# `ship-execute` architecture: standalone DAG-aware execution engine that leverages `ship-code`

## Context

`ship-better-plans` produces audited plans and ends by offering an execution choice (Q1). `ship-execute` is that executor — a new booster skill that takes a written plan and builds it with a fleet of expert subagents, validates every step, vets the whole result, then hands off to the user for review or PR. The user's framing: "tackle problems in the most effective fleshed-out way with a fleet of expert agents as needed; validate every step to ensure solutions are correct; vet all work before rubber-stamping; then send to the user for review or ask permission to PR. For coding tasks, leverage the sister `ship-code` repo's skills."

Five decisions locked with the user (each from a multiple-choice question). The full design is in [ship-execute-design](../plans/ship-execute-design.md).

## Decision

### E1 — Architecture: **Standalone engine + `ship-code` delegation**

`ship-execute` owns its execution engine (fleet supervision, per-step verification, final vetting, handoff). It does **not** depend on the superpowers execution skills (subagent-driven-development, finishing-a-development-branch, etc.) — that would be an undeclared dependency and the exact upstream coupling [ship-better-plans-architecture](ship-better-plans-architecture.md) D1 rejected. It delegates **coding depth** to the `ship-code` sibling marketplace (`/Users/mohamede/Repos/Ship-It-Ops/ship-code`): `ship-clean-code`, `ship-tested-code`, `ship-secure-code`, `ship-debugged-code`, `ship-devops`, and `ship-reviewed-prs` for final vetting. Only declared dependency: `ship-code`.

### E2 — Engine: **DAG-aware hybrid (Workflow + worktrees)**

Read the plan's task DAG. Run the critical path sequentially; run independent branches in **parallel** via the Workflow tool with **per-agent worktree isolation** (so parallel code-writers don't collide), then reconverge at an **integration-merge gate**. Falls back to sequential when the plan has no real parallel set.

### E3 — Per-step gate: **Run + review (evidence-based)**

Each task advances only on real evidence: implement (TDD where the plan specs tests) → **run** (build/typecheck + the task's tests + its acceptance criteria must be green — verification-before-completion discipline) → **ship-code review** for non-trivial changes → fail loops into a bounded rework cycle; blockers escalate to the user, never silently skipped.

### E4 — Trigger/safety: **Auto-trigger after a plan, with a mandatory gate**

Auto-triggers when a written plan exists and the user is about to execute it; also `/ship-execute [plan]` (`solo` forces sequential). `disable-model-invocation` stays **off** (auto-trigger on), but a **mandatory pre-flight confirmation gate** always fires before any side effect ("Execute this plan? N tasks, runs commands + writes code, ~X tokens") — this gate is the Workflow opt-in. **PR/push always needs a separate explicit yes** (no-push-without-asking). **Refuses to run in plan mode** (plan mode forbids the writes/commands it needs).

### E5 — Final vetting + handoff (proposed, accepted)

Rubber-stamp requires: full suite green + all acceptance criteria met + a `ship-reviewed-prs` multi-persona APPROVE on the whole `BASE..HEAD` diff. Then present an evidence summary + diff stat and offer **review locally / open PR (asks permission) / keep branch / discard** — never auto-PR.

## Alternatives Considered

- **E1 compose-with-superpowers** — least to build, but undeclared superpowers dependency + upstream coupling. Rejected for family consistency. **Hybrid** (own engine, reuse `finishing-a-development-branch` for git/PR) rejected to keep the dependency surface to `ship-code` only.
- **E2 sequential subagent loop** — simpler, no worktree/merge complexity, but forfeits the plan DAG's parallel speedup. Kept as the automatic fallback. **Parallel-by-default Workflow** rejected — conflict/failure-prone, overkill for linear plans.
- **E3 run-only** (skips per-step quality lens) and **review-only** ("looks correct" ≠ "runs correctly") — both rejected; the user wants demonstrated correctness.
- **E4 explicit-only + `disable-model-invocation: true`** — safest, but the user chose the seamless auto-trigger+gate flow. Acceptable because the mandatory gate neutralizes the side-effect risk (same reasoning as ship-better-plans D6/D7), and PR/push stays explicit.

## Consequences

- **ship-code is a hard dependency for coding tasks.** The skill must detect whether `ship-code` skills are installed and **degrade gracefully** (warn + use its own lighter review) rather than failing.
- **Parallel worktree execution + integration merge is the riskiest subsystem.** Mitigated by per-task verification, an explicit integration-merge gate, and the sequential fallback.
- **Auto-trigger scoping is high-leverage.** The description must be tight ("a written plan exists and the user is about to execute it") with anti-triggers, or it fires on every "build X" conversation. Test explicitly.
- **Plan-mode refusal** keeps it from violating plan-mode write rules — the inverse of ship-better-plans D5 (which cooperates with plan mode because it only writes markdown).
- Pairs with [ship-better-plans-architecture](ship-better-plans-architecture.md): plan → execute → (ship-code quality), all siblings, no superpowers dependency.

## Revisit Triggers

- If the auto-trigger fires on non-execution conversations → tighten the description or flip to explicit-only.
- If parallel worktree merges routinely conflict → default to sequential and make parallelism opt-in.
- If `ship-code` proves frequently absent for users → consider bundling or a clearer install prerequisite.
- If `ship-reviewed-prs` final vetting is too heavy for small plans → add a depth scale (mirror ship-better-plans Q2).

## Related

- [ship-execute-design](../plans/ship-execute-design.md) — full design, flow, plugin layout, verification
- [ship-better-plans-architecture](ship-better-plans-architecture.md) — the planner this executes the output of; D1 (standalone) precedent
- [ship-better-plans-design](../plans/ship-better-plans-design.md) — Q1 hands off to this skill
