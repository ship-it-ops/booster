---
type: decision
status: active
created: 2026-06-09
updated: 2026-06-10
author: claude-opus-4-7
tags: [skill, plugin, planning, audit, workflow, ship-family]
importance: core
---

# `ship-better-plans` architecture: parallel skill, Workflow-based audit, `docs/agent/` integration

## Context

The user is building `ship-better-plans` — a new skill in this repo that produces bulletproof, fully-specified, audited execution plans. It joins the `ship-*` family and ships as `plugins/ship-better-plans/` with the skill at `skills/ship-better-plans/SKILL.md`.

Four architectural decisions were locked during the initial brainstorm (each chosen by the user from a 3-way multiple-choice question). Capturing them here so the rationale survives implementation handoff. The full design is in [ship-better-plans-design](../plans/ship-better-plans-design.md).

## Decision

### D1 — Relationship to existing skills: **Parallel**

`ship-better-plans` is a standalone alternative to `superpowers:brainstorming` + `superpowers:writing-plans`. It does not wrap, replace, or depend on either.

### D2 — Audit engine: **Workflow tool, parallel fan-out**

The audit phase invokes the `Workflow` tool to run persona reviewers concurrently with structured-output schemas. Supports the canonical `parallel()` + `pipeline()` + loop-until-dry patterns from the Workflow tool docs.

The skill's `SKILL.md` must explicitly authorize Workflow calls so it counts as user opt-in (per Workflow tool's "explicit opt-in" requirement — skill instructions are one of the listed authorization sources).

### D3 — Artifact location: **`docs/agent/`**

- Main plan → `docs/agent/plans/<slug>.md`
- Decisions made during planning → `docs/agent/decisions/<slug>.md`
- Open questions → `docs/agent/open-questions/<slug>.md`
- Standing user instructions captured during the session → `docs/agent/instructions/<slug>.md`
- `MANIFEST.md` updated atomically (use the ledger pattern from `ship-agent-context`).

### D4 — Trigger model: **Auto-trigger skill + explicit slash command**

Two entry points:
- A carefully-scoped skill description that auto-triggers when the user is starting non-trivial planning work.
- An explicit slash command (name TBD — `/ship-plan` is the working candidate) for direct invocation.

### D5 — Plan-mode behavior: **Mode-aware hybrid**

The skill detects whether Claude Code plan mode is active (via the plan-mode system reminder). If active: all discovery, design, and the audit run read-only, the skill calls `ExitPlanMode` for approval, and **only after approval** writes the `docs/agent/` artifacts. If not active: it writes artifacts inline as produced. Resolves the B1 conflict (Phase 7 writes vs. plan-mode's write ban).

### D6 — Workflow audit launch: **Always confirm first**

Before launching the Workflow audit, the skill **always** surfaces a cost/scope confirmation ("Run the N-persona audit? ~X tokens") and waits for a yes — on both the `/ship-plan` and auto-trigger paths. Satisfies the Workflow tool's explicit-opt-in contract uniformly and makes Open Question #7 (cost surfacing) a hard gate rather than optional. Resolves B2.

### D7 — Entry-point shape: **Single skill, auto-trigger retained**

One skill with auto-trigger enabled (`disable-model-invocation` unset/false) plus the `/ship-plan` command. Justified because D5 defers writes in plan mode and D6 always gates the only costly action — and writing a git-tracked markdown plan is not a deploy/commit-class side effect, so CONTRIBUTING's `disable-model-invocation: true` guidance doesn't squarely apply. SKILL.md must document this exemption reasoning. Resolves B3; supersedes the bare D4 by pinning it to a single non-split skill.

## Alternatives Considered

### D1 alternatives
- **Replace both with one end-to-end skill.** Rejected — would couple us to changes in superpowers and lose the spec/plan separation users on superpowers already rely on.
- **Compose — wrap superpowers' flow and add audit + intake rigor on top.** Rejected — creates upstream-coupling fragility; superpowers updates could silently change behavior.

### D2 alternatives
- **Agent tool, sequential.** Simple, cheap, predictable, but caps the audit depth and wall-clock — running 3 personas takes 3× as long. Doesn't reach the rigor bar the user wants.
- **Both — mode-driven (Agent for quick/standard, Workflow for ultra).** Rejected for v1 — adds two execution paths to maintain. Open Question #2 may revisit this later for quick mode.

### D3 alternatives
- **Custom dir `docs/ship-plans/`.** Loses auto-indexing and discovery via `ship-agent-context`; future agents wouldn't see the plan at session start.
- **Configurable, default `docs/agent/plans/`.** Adds config surface for marginal benefit — the right default works for ~all users.

### D4 alternatives
- **Slash command + modes only (`/ship-plan [quick|standard|ultra]`).** Predictable but misses the auto-trigger opportunity for users mid-conversation who don't think to type a slash command.
- **Slash command only, no auto-trigger.** Most predictable but highest friction.

## Consequences

- **D1 (Parallel):** Some users will have both `superpowers` and `ship-better-plans` installed. The skill description must be specific enough that triggering doesn't fight with superpowers' `brainstorming` skill. Test this explicitly in development.
- **D2 (Workflow):** Audit cost is bounded by Workflow's concurrency cap (~10 concurrent agents). For a 3-persona standard audit this is fine. Ultra mode with adversarial-verify can spawn 10+ agents per round — the skill should surface a token budget heads-up before launching (Open Question #7).
- **D3 (`docs/agent/`):** Plan-mode native location (`~/.claude/plans/...`) is bypassed. If the user is in Claude Code plan mode when triggering the skill, the skill should still respect plan-mode semantics (read-only edits except the plan file). Implementation must thread this carefully.
- **D4 (Auto-trigger):** Skill description is high-leverage. Risk: over-firing on planning-adjacent conversations (e.g., "what should I do next" is planning-adjacent but not a `ship-better-plans` trigger). Mitigation: scope the description to "starting non-trivial new work that warrants a written plan" and include anti-trigger phrases.

## Revisit Triggers

- If the auto-trigger fires on conversations the user didn't mean as planning sessions → tighten the description.
- If standard-mode audits routinely miss findings that ultra catches → consider promoting one of the ultra-mode features (e.g., adversarial verify) into standard.
- If Workflow cost becomes a complaint → revisit Open Question #7 (cost surfacing) and consider a "preview the audit shape and cost, confirm" gate.
- If the `superpowers` flow updates with intake-rigor / audit features that subsume parts of this skill → revisit D1 and consider deprecating overlapping phases.

## Related

- [ship-better-plans-design](../plans/ship-better-plans-design.md) — the full plan, expanded scope, and open questions
- [ship-better-plans-handoff](../status/ship-better-plans-handoff.md) — the fresh-agent pickup instructions
- [agent-context-initialized](agent-context-initialized.md) — the `docs/agent/` foundation D3 builds on
- [add-user-instructions-to-skill](add-user-instructions-to-skill.md) — Phase 7 emits to the `instructions/` surface defined here
