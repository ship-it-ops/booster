---
name: ship-better-plans
description: >
  Use when starting non-trivial new development work that warrants a written,
  audited implementation plan — a new feature, a refactor spanning multiple
  files, a migration, an integration, or any task where getting the plan right
  up front matters more than starting fast. Produces a bulletproof,
  fully-specified plan: structured intake (problem / success criteria /
  non-goals / constraints / assumptions), automatic `docs/agent/` + codebase
  discovery, 2–3 scored tradeoff options before a recommendation, numbered
  specs with edge cases and interface contracts, a task DAG with
  parallelization and subagent-delegation, and a parallel multi-persona audit
  (adversarial / pragmatist / production) that runs before the plan is written
  to `docs/agent/plans/`. Also triggers on the `/ship-plan` command (append
  `ultra` for the convergence-loop audit). Do NOT trigger for trivial one-line
  changes, quick factual questions, pure debugging of a single known bug, or
  when the user just wants a fast answer rather than a plan; and do not hijack
  an in-progress `superpowers` brainstorming / writing-plans flow the user is
  already running.
allowed-tools: Read, Write, Edit, Glob, Grep, Task, Workflow, TodoWrite, AskUserQuestion, ExitPlanMode, Bash(mkdir -p *)
---

## Purpose

Produce **bulletproof, fully-specified, audited execution plans** — measurably better than an unaided brainstorm. This skill exists because ad-hoc planning under-specifies requirements, skips tradeoff documentation, never audits itself, and hands the executor a flat task list instead of a parallelizable DAG. `ship-better-plans` fixes all four: it forces intake rigor, captures specs and decisions *upfront*, audits the plan with adversarial reviewers before you commit to it, and structures execution for subagent parallelism.

It is a **standalone alternative** to `superpowers:brainstorming` + `superpowers:writing-plans`, not a wrapper. It writes its outputs into `docs/agent/` (see `ship-agent-context`) so future agents inherit the plan, the decisions, and the open questions.

It **plans only**. Execution is a separate skill — this one ends by offering the user an execution choice (see [Completion](#completion)).

---

## Entry points & modes

- **Auto-trigger** — fires on the description above when the user begins non-trivial new work. On this path you MUST hit the [audit cost gate](#phase-6--audit-workflow-d6) before spending tokens.
- **`/ship-plan`** — explicit invocation. `/ship-plan ultra` selects ultra mode.

| Mode | Audit | When |
|------|-------|------|
| `standard` (default) | one parallel persona pass + adversarial-verify of findings | most plans |
| `ultra` | full persona set + adversarial-verify + **loop-until-dry** convergence | high-stakes, irreversible, or large-blast-radius work |

There is no "quick" mode — if a task is too small to audit, it is too small for this skill; just do it.

---

## Operating rules (non-negotiable)

1. **One question at a time.** Use `AskUserQuestion`, multiple-choice whenever possible. Never dump a question list.
2. **Loud about assumptions.** Every assumption is flagged AS an assumption, never silently baked in.
3. **Plan-mode aware (D5).** Detect Claude Code plan mode (a plan-mode system reminder is present). See [Plan-mode behavior](#plan-mode-behavior-d5).
4. **Audit cost gate (D6).** ALWAYS surface the estimated token cost and wait for a yes before launching the Workflow audit — on both entry paths.
5. **Hard exit gate.** Refuse to finish while any required plan section is empty or contains a placeholder (`TBD`, `???`, `<...>`). Either fill it or convert it to an explicit open question.
6. **Bail on scope creep.** If the ask is really multiple independent subsystems, STOP and require decomposition before planning — plan one coherent unit at a time.

The full procedure, persona prompts, and output schemas live in [`reference.md`](reference.md). Read it before running the first time.

---

## The 8 phases

Run in order. Phases 1–6 are read-only-safe (no repo writes); Phase 7 is the only write step.

### Phase 1 — Intake
Capture, before any design: **problem** (what) and **why**, separated · measurable **success criteria** · explicit **non-goals** · hard **constraints** (time/tech/compliance/blocked-on) · **assumptions** (flagged) · stakeholders/approvers · effort budget. Run the **scope-decomposition check** (rule 6) here.

### Phase 2 — Context discovery (pulled, not asked)
Dispatch `Task` Explore subagents in parallel for codebase discovery. Always also: a **reuse audit** (existing utils/functions/patterns to reuse, with file paths) · `docs/agent/` lookup (prior decisions, scars, open questions, patterns) · standing-instruction check (`docs/agent/instructions/`) · `AGENTS.md`/`CLAUDE.md` compliance · adjacent in-flight work (`docs/agent/status/`, recent branches).

### Phase 3 — Design with forced tradeoffs
2–3 alternative approaches in a **scored tradeoff table** (effort / risk / reversibility / blast-radius) · recommended approach + why-this-why-not-others · risk register (probability × impact + mitigations) · per-step reversibility (safe / hard-to-reverse / destructive) · rollback plan · migration plan (only if touching live state/data/schema).

### Phase 4 — Specification clarity gates
Numbered, atomic, verifiable **functional requirements** · non-functionals (perf/security/a11y/observability) · **acceptance criteria** mapped to requirements · interface contracts (inputs/outputs/errors per boundary) · data shapes · **edge cases** enumerated (empty/max/malformed/concurrent/partial-failure) · open questions flagged.

### Phase 5 — Execution plan (the differentiator)
A **task DAG** with dependencies (not a flat list), emitted as a **Mermaid graph** with a markdown task list as fallback · **parallelization plan** (what runs concurrent, what blocks) · **subagent-delegation map** (task → Explore / feature-dev / code-reviewer / Workflow fan-out) · checkpoints/gates between phases · **per-phase verification strategy** · per-phase effort budget so the executor scales depth.

### Phase 6 — Audit (Workflow, D6)
See [below](#phase-6--audit-workflow-d6).

### Phase 7 — Outputs (the only write step)
Write per [Outputs](#phase-7-outputs).

### Phase 8 — UX
The operating rules above are themselves Phase 8 — they govern how every other phase talks to the user.

---

## Phase 6 — Audit (Workflow, D6)

The audit runs the script at [`workflows/audit.workflow.js`](workflows/audit.workflow.js) via the **Workflow tool**. The `.js` file does not run itself — **Read it and pass its contents as the Workflow `script`** (or pass its path as `scriptPath`). The skill's instructions here are the explicit user opt-in the Workflow tool requires.

**Before launching, ALWAYS (D6):** state the mode, the persona count, and an estimated token cost, then wait for the user's yes.

```
"Ready to audit this plan in <standard|ultra> mode:
 <N> personas (Adversarial, Pragmatist, Production<, +context personas>)
 <+ adversarial-verify + loop-until-dry, for ultra>.
 Estimated ~<X>k tokens. Run it? (yes / switch mode / skip audit)"
```

**Personas — core + context-adaptive (Q3):**
- Always: **Adversarial** (break the plan, find false assumptions / missing edge cases), **Pragmatist** (YAGNI, over-engineering, scope creep), **Production** (security, infra, observability, rollback, compliance).
- Add by plan content: **Test-strategist** (plan involves tests), **Data-migrations** (schema/live-data changes), **DevOps/SRE** (CI/IaC/deploy). These may delegate to `ship-secure-code`, `ship-tested-code`, `ship-devops` for depth.

The script fans personas out with `parallel()`, then `pipeline()`s each finding through an adversarial **refute** pass (default `refuted=true` when uncertain) and keeps only the unrefuted. **Ultra** wraps this in a loop-until-dry harness (repeat until a round surfaces nothing new). Fold confirmed findings back into the plan, then re-state what changed.

---

## Plan-mode behavior (D5)

**If a plan-mode system reminder is present** (Claude Code plan mode is active):
- Run Phases 1–6 normally — they are read-only-safe (discovery reads, the audit Workflow only analyzes plan text and returns findings; it must not write to the repo).
- Write the plan-mode scratchpad as plan mode allows, call `ExitPlanMode` for approval.
- **Defer all `docs/agent/` writes (Phase 7) until AFTER approval.** The `ExitPlanMode` approval doubles as the skill's hard exit gate.

**If not in plan mode:** write Phase 7 artifacts inline as they are produced; no `ExitPlanMode`.

This skill keeps auto-trigger enabled and does **not** set `disable-model-invocation` despite having side effects. That CONTRIBUTING guidance targets deploy/commit-class effects; here the only writes are git-tracked markdown under `docs/agent/`, and the one costly action (the audit) is always gated by D6 — so auto-discovery is worth more than the side-effect lockdown.

---

## Phase 7 outputs

Written via `ship-agent-context` conventions (templates in [`templates/`](templates/)):

- **Plan** → `docs/agent/plans/<slug>.md` (frontmatter + `## Related`).
- **Decisions** made during planning → `docs/agent/decisions/<slug>.md`.
- **Open questions** raised → `docs/agent/open-questions/<slug>.md`.
- **Standing user instructions** captured during the session → `docs/agent/instructions/<slug>.md`.
- **Scars** — read when relevant (Phase 2), never written here.
- **`MANIFEST.md`** — add/update entries directly (this repo does not use the ledger pattern; reach for it only if multiple agents write concurrently).

Run `mkdir -p docs/agent/{plans,decisions,open-questions,instructions}` defensively first. If `docs/agent/` does not exist at all, offer to scaffold it via `ship-agent-context`.

---

## Completion

After the plan is written and approved, **offer an execution choice (Q1)** — do not auto-execute:

```
"Plan saved to docs/agent/plans/<slug>.md. Next:
  [1] Execute now (e.g. superpowers:executing-plans / the dedicated execution skill)
  [2] Subagent-driven execution in this session
  [3] Stop here — resume from the plan later"
```

Execution is intentionally a **separate skill**. This one's job ends at a great, approved, persisted plan.

---

## Verification (self-check before declaring done)

- Every required section non-empty, no placeholders (rule 5).
- Tradeoff table has ≥2 options with scores and a justified recommendation.
- Task DAG renders (Mermaid block present) and dependencies are acyclic.
- Audit ran (or the user explicitly skipped it) and confirmed findings were folded in.
- Plan file written to `docs/agent/plans/` and indexed in `MANIFEST.md` (or deferred correctly per D5).
