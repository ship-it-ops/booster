---
type: plan
status: completed
created: 2026-06-09
updated: 2026-06-10
author: claude-opus-4-7
tags: [skill, plugin, planning, audit, workflow]
importance: core
---

# Plan: `ship-better-plans` skill + plugin

> ✅ **SHIPPED 2026-06-10 (commit `47be8cc`, branch `ship-plans`).** Skill + plugin built at `skills/ship-better-plans/` + `plugins/ship-better-plans/`, validated clean (validate-skills.py, check-skill-links.py, markdownlint). Design closed: control-flow resolved as D5–D7 in [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md); all 7 open questions resolved (table below); the layout below is the corrected one that was built. Not yet merged to `main` / not yet install-tested via `/plugin install` (see Verification).

## Context

The user is building a new skill called `ship-better-plans` in this repo. Goal: produce **bulletproof, fully-specified, audited execution plans** — noticeably better and more efficient than the existing `superpowers:brainstorming` + `superpowers:writing-plans` flow.

User's framing of why the current flow is insufficient:
- Under-specifies requirements, misses gaps.
- Doesn't force tradeoff documentation.
- Doesn't audit itself.
- Doesn't structure execution as a DAG with subagent delegation for parallel speedup.
- Specs and decisions get retrofitted, not captured upfront.

This skill joins the `ship-*` family and ships as its own plugin: `plugins/ship-better-plans/` with `skills/ship-better-plans/SKILL.md` inside. Pattern reference: `plugins/ship-agent-context/`.

The user paused mid-brainstorm to commit this work into repo memory before handing off to a fresh agent. The plan-mode scratchpad lived at `~/.claude/plans/alright-we-have-staged-whisper.md`; this file is the durable, branch-tracked version.

## Locked Decisions

Captured in detail in [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md). Summary:

| # | Decision |
|---|----------|
| D1 | Parallel skill — leaves `brainstorming` / `writing-plans` alone. |
| D2 | Audit phase runs via the **Workflow tool**, parallel fan-out, structured-output schemas. |
| D3 | Plan artifacts live at `docs/agent/plans/<slug>.md`, indexed in `MANIFEST.md`; decisions / open-questions / instructions emit to sibling `docs/agent/` dirs. |
| D4 | Trigger: auto-trigger skill description + explicit slash command. Both supported. |

## Resolved Design Decisions (Q1–Q7, closed 2026-06-10)

All resolved with the user. Control-flow decisions D5–D7 live in [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md); the scope decisions below are the build parameters.

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Scope boundary at end of planning | **Offer execution choice** post-approval: "execute now / pick executor / stop here". Execution itself ships as a **separate future skill** (not part of ship-better-plans). |
| Q2 | Mode/depth scaling | **Two modes: `standard` (default, single Workflow pass, 3 core personas) and `ultra` (full personas + adversarial-verify + loop-until-dry).** No quick mode. |
| Q3 | Audit persona set | **Core + context-adaptive.** Always: Adversarial / Pragmatist / Production. Conditionally added by plan content: Test-strategist (tests), Data-migrations (schema/live data), DevOps/SRE (CI/IaC). Personas may delegate to ship-secure-code / ship-tested-code / ship-devops. Mirrors `ship-reviewed-prs`. |
| Q4 | Slash-command name | **`/ship-plan`** (with `/ship-plan ultra`). No conflict; on-brand with the ship-* family. |
| Q5 | Hooks | **Skill-only, no bundled hook.** ship-agent-context's SessionStart hook already surfaces in-flight plans + MANIFEST; a second hook would double-fire. |
| Q6 | Visual companion | **Yes — emit a Mermaid DAG** of the execution graph in the plan, with the markdown task list as fallback. Text-based, no rendering dependency. |
| Q7 | Cost surfacing | **Audit gate only (D6).** Single cost decision point at the audit confirmation; discovery Explore agents run without a separate prompt. (Phase 5's per-phase *execution* budget is separate and stays — it's an estimate for the future executor skill.) |

## Expanded Scope — 8 Phases

The complete scope the SKILL.md must cover. None of these should be lost in implementation.

### Phase 1 — Intake (captured upfront, before any design)
- Problem statement: the **what** and the **why**, separated.
- Success criteria: measurable, verifiable, agreed before design starts.
- Non-goals / out-of-scope: explicitly listed.
- Hard constraints: time, tech, compliance, blocked-on-others.
- Stated assumptions: flagged AS assumptions, not facts.
- Stakeholders / approvers.
- Effort budget: tokens, wall-clock, parallel-agent count.
- **Scope-decomposition check:** if the ask is multiple independent subsystems, refuse to plan as one — force decomposition first.

### Phase 2 — Context discovery (auto-pulled, not asked)
- Reuse audit — existing utils/functions/patterns to reuse, with file paths.
- `docs/agent/` lookup — past decisions, scars, open questions on this topic.
- Standing user instructions check (`docs/agent/instructions/`).
- AGENTS.md / CLAUDE.md compliance pass.
- Adjacent in-flight work (`docs/agent/status/`, recent branches).
- Dispatch Explore subagents in parallel for codebase discovery.

### Phase 3 — Design with forced tradeoffs
- 2–3 alternative approaches with scored tradeoffs table (effort / risk / reversibility / blast radius).
- Recommended approach + reasoning (why this, why not the others).
- Risk register: probability × impact, with mitigations.
- Reversibility classification per step: safe / hard-to-reverse / destructive.
- Rollback plan.
- Migration plan (only if touching live state/data/schemas).

### Phase 4 — Specification clarity gates
- Functional requirements: atomic, verifiable, numbered.
- Non-functional: perf, security, a11y, observability budgets.
- Acceptance criteria: testable conditions, mapped to functional reqs.
- Interface contracts: inputs, outputs, errors per boundary.
- Data shapes / schemas.
- Edge cases enumerated: empty, max, malformed, concurrent, partial-failure.
- Open questions flagged (not silently assumed).

### Phase 5 — Execution plan (the differentiator vs writing-plans)
- **Task DAG** with dependencies (not a flat list).
- **Parallelization plan** — what runs concurrent, what blocks.
- **Subagent delegation map** — task → agent type (Explore / feature-dev / code-reviewer / Workflow fan-out).
- **Checkpoints / gates** between phases.
- **Verification strategy per phase**, not just at the end.
- **Token/effort budget per phase** so the executor scales depth.

### Phase 6 — Audit (Workflow-based, parallel)
- Adversarial skeptic: tries to break the plan, find missing edge cases / false assumptions.
- Pragmatist: over-engineering, YAGNI violations, scope creep.
- Production reviewer: security, infra, observability, rollback, compliance.
- Convergence loop — iterate until N audit rounds find nothing new (loop-until-dry, not fixed-count).
- Self-review checklist — placeholders, contradictions, ambiguity, scope creep.
- Confidence scoring per finding — low-confidence findings dropped or flagged.

### Phase 7 — Outputs
- Main plan: `docs/agent/plans/<slug>.md` (frontmatter + index entry).
- Decisions made during planning → `docs/agent/decisions/<slug>.md`.
- Open questions → `docs/agent/open-questions/<slug>.md`.
- Standing user instructions captured during the session → `docs/agent/instructions/<slug>.md`.
- Scars referenced when relevant (read, not written).
- `MANIFEST.md` updated atomically (use the ledger pattern from ship-agent-context).

### Phase 8 — UX rules the skill itself follows
- One question at a time (no question dumps).
- Multiple choice preferred over open-ended.
- Loud about assumptions — never silent.
- Hard gate before exiting planning — refuses to finish until all required sections are non-empty and no placeholders remain.
- Bails on scope creep — flags multi-project asks, requires decomposition.

## Corrected Plugin Layout (supersedes the original; mirrors `plugins/ship-agent-context/`)

Source of truth is the **repo-root `skills/ship-better-plans/`**; the plugin tree holds **per-file symlinks** (this is the scarred convention — see the two scars). `plugin.json` lives under `.claude-plugin/` and carries **no `skills` field**.

```
skills/ship-better-plans/                 # SOURCE OF TRUTH
  SKILL.md                                # lean: frontmatter + trigger + dispatch (<500 lines)
  reference.md                            # full 8-phase procedure, persona prompts, schemas
  templates/{plan,decision,open-question,instruction}.md
  workflows/audit.workflow.js             # real Workflow script (valid `meta`, .filter(Boolean) guards)
  examples/{example-plan-feature.md,example-plan-refactor.md}
plugins/ship-better-plans/
  .claude-plugin/plugin.json              # name/description/version/author/license — NO `skills` field
  skills/ship-better-plans/
    SKILL.md      -> ../../../../skills/ship-better-plans/SKILL.md
    reference.md  -> ../../../../skills/ship-better-plans/reference.md
    templates     -> ../../../../skills/ship-better-plans/templates
    workflows     -> ../../../../skills/ship-better-plans/workflows
    examples      -> ../../../../skills/ship-better-plans/examples
  commands/ship-plan.md                   # slash command (no root mirror; commands aren't CI-validated → test install)
  # no hooks/  (Q5: skill-only)
.claude-plugin/marketplace.json           # NEW entry: name, source "./plugins/ship-better-plans", description, version (== plugin.json), category
```

**Build sequencing (audit A3):** the first commit must be a complete CI-green vertical slice — root `skills/ship-better-plans/SKILL.md` + `.claude-plugin/plugin.json` + all symlinks + the marketplace entry — because `validate-skills.py` enforces skill↔plugin↔marketplace consistency atomically. Subsequent commits enrich (reference.md, templates, workflow, command).

## Audit Workflow — Concrete Shape

> ⚠️ **Illustrative pseudocode — do NOT copy verbatim** (audit C1). The real script at `skills/ship-better-plans/workflows/audit.workflow.js` must (a) begin with `export const meta = {...}`, (b) `.filter(Boolean)` the `parallel()` result before `flatMap`, and (c) pin `id` + `title` in `FINDINGS_SCHEMA`. SKILL.md must Read this file and pass its contents as the Workflow `script` (or pass `scriptPath`) — the `.js` file does not run itself (C2).

```javascript
phase('Audit')
const findings = await parallel(PERSONAS.map(p => () =>
  agent(p.prompt + planText, { phase: 'Audit', schema: FINDINGS_SCHEMA, label: `audit:${p.key}` })
))

phase('Verify')
const verified = await pipeline(
  findings.flatMap(r => r.findings),
  f => agent(`Adversarially try to refute: ${f.title}. Default refuted=true if uncertain.`,
             { phase: 'Verify', schema: VERDICT_SCHEMA, label: `verify:${f.id}` })
)

return { confirmed: verified.filter(v => v && !v.refuted) }
```

Per Q2: **standard** = single `parallel()` persona pass + the `pipeline()` refute verify; **ultra** = wrap in a loop-until-dry harness (repeat until N rounds find nothing new). No quick mode. Per D6, the skill confirms estimated tokens before either runs.

## Verification — How to know it works end-to-end

Once built, validate against a real planning task:

1. Trigger the slash command with a moderately complex feature request.
2. Confirm the skill:
   - Asks intake questions one at a time.
   - Pulls `docs/agent/` context automatically.
   - Produces 2–3 tradeoff options before recommending.
   - Calls Workflow with the persona-audit script.
   - Writes the plan to `docs/agent/plans/<slug>.md` and updates `MANIFEST.md`.
   - Emits decisions to `docs/agent/decisions/` when applicable.
   - Refuses to exit with placeholders or empty required sections.
3. Read the produced plan with fresh eyes — does it meet the "bulletproof" bar?
4. Run a second invocation in quick mode (if Q2 resolves yes) to confirm depth scales down.

## Related

- [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md) — locked decisions D1–D4 with full rationale
- [ship-better-plans-handoff](../status/ship-better-plans-handoff.md) — the fresh-agent pickup instructions
- [agent-context-initialized](../decisions/agent-context-initialized.md) — the `docs/agent/` foundation this plan integrates with
- [add-user-instructions-to-skill](../decisions/add-user-instructions-to-skill.md) — the `instructions/` content type Phase 7 emits to
