---
type: plan
status: completed
created: 2026-06-11
updated: 2026-06-11
author: claude-opus-4-8
tags: [skill, plugin, execution, workflow, ship-code]
importance: core
---

# Plan: `ship-execute` skill + plugin

## Goal

A booster skill that executes a written plan ([ship-better-plans](ship-better-plans-design.md) output) with a fleet of expert subagents, validates every step with real evidence, vets the whole result, and hands off to the user for review or PR. Decisions E1–E5 in [ship-execute-architecture](../decisions/ship-execute-architecture.md).

## Approach

Standalone engine (E1); DAG-aware hybrid execution with Workflow + worktrees (E2); evidence-based run+review per-step gate (E3); auto-trigger + mandatory confirmation gate (E4); `ship-reviewed-prs` final vetting then a handoff options menu (E5). Coding depth delegated to `ship-code`.

### Execution flow (the 5 stages)

1. **Pre-flight** — load the plan file, parse the task DAG / FRs / acceptance criteria / per-task verification / delegation map; refuse if in plan mode; create a `docs/agent/status/` entry; set up an isolated branch/worktree; show the E4 gate.
2. **DAG execution (E2)** — critical path sequential; independent branches in parallel via Workflow with `isolation: 'worktree'`; integration-merge gate on reconverge; sequential fallback when no parallel set.
3. **Per-step gate (E3)** — implement (TDD if specced) → run (build/typecheck + task tests + acceptance criteria green) → ship-code review for non-trivial tasks → bounded rework loop on fail; escalate blockers.
4. **Final vetting (E5)** — full suite green + all acceptance criteria + `ship-reviewed-prs` APPROVE on `BASE..HEAD`. Findings loop back.
5. **Handoff (E5)** — evidence summary + diff stat → options: review locally / open PR (asks permission) / keep branch / discard. Never auto-PR.

### ship-code leverage

Per-step review + final vetting delegate to `ship-code`: `ship-clean-code` / `ship-tested-code` / `ship-secure-code` / `ship-debugged-code` (blockers) / `ship-devops` (CI/IaC), and `ship-reviewed-prs` for the final multi-persona pass. Non-coding tasks skip code review but still run their checks. Detect-and-degrade if `ship-code` is absent.

### docs/agent integration

Status entry while running (coordination); flip the plan's status executing→done; capture decisions/scars discovered mid-execution; record outcome.

## Files to Touch

Mirror `plugins/ship-better-plans/` exactly (symlink convention + scars):

- `skills/ship-execute/SKILL.md` — lean dispatcher: trigger, gate, 5-stage flow, operating rules.
- `skills/ship-execute/reference.md` — full procedure, subagent prompts, status codes, worktree/merge protocol, ship-code delegation map, schemas.
- `skills/ship-execute/workflows/execute.workflow.js` — DAG-aware parallel executor (worktree isolation, per-task verify, integration gate).
- `skills/ship-execute/templates/` — execution-status / outcome note templates.
- `skills/ship-execute/examples/` — one worked execution (feature) + one parallel-DAG example.
- `plugins/ship-execute/.claude-plugin/plugin.json` (no `skills` field), `plugins/ship-execute/skills/ship-execute/` per-file symlinks, `plugins/ship-execute/commands/ship-execute.md`.
- `.claude-plugin/marketplace.json` — new entry, inlined `./plugins/ship-execute` source, matching version, category.

## Status

SHIPPED 2026-06-11 (commit `0eeeba8`, branch `ship-plans`). Built at `skills/ship-execute/` + `plugins/ship-execute/`; validated clean (validate-skills.py, check-skill-links.py, markdownlint, node --check). Not yet merged to `main` / not yet install-tested via `/plugin install` or exercised end-to-end on a real plan.

## Related

- [ship-execute-architecture](../decisions/ship-execute-architecture.md) — E1–E5 with rationale
- [ship-better-plans-design](ship-better-plans-design.md) — produces the plan this consumes
- [add-user-instructions-to-skill](../decisions/add-user-instructions-to-skill.md) — docs/agent content types this writes
