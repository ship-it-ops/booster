---
type: investigation
status: active
created: 2026-06-09
updated: 2026-06-09
author: claude-opus-4-8
tags: [ship-better-plans, audit, plugin, workflow, plan-mode, review]
importance: core
---

# Audit of the `ship-better-plans` design plan

## Symptoms

The user asked for a full audit of the handed-off `ship-better-plans` design ([plan](../plans/ship-better-plans-design.md), [decisions](../decisions/ship-better-plans-architecture.md)) before resuming the brainstorm. Audited against both scars, the live plugin layout, the CI validator (`scripts/validate-skills.py`), `CONTRIBUTING.md`, the Workflow tool opt-in contract, and Claude Code plan-mode semantics. The design intent is strong but is **not buildable as written**.

## Root Cause (the findings)

**Blockers — would fail CI / contradict scars:**
- **A1 — plugin layout is wrong.** Plan puts skill files inside the plugin tree with `plugin.json` at plugin root. Reality (enforced by validator + both scars): source of truth is repo-root `skills/ship-better-plans/`; the plugin holds `.claude-plugin/plugin.json` (no `skills` field) + **per-file symlinks** back to the root skill. New subdirs (`templates/`, `workflows/`) each need their own symlink — the existing plugin only symlinks `SKILL.md`, `reference.md`, `examples`.
- **A2 — `marketplace.json` entry omitted.** Validator requires every `skills/<name>/` to have a matching `plugins/<name>/` AND a marketplace entry (`name`/`source`/`description`/`version`/`category`), `source` inlined as `./plugins/ship-better-plans`. Not in the plan's artifact list.
- **A3 — incremental commits go CI-red.** "Commit per layer" breaks the validator's all-or-nothing consistency check. First commit must be a complete CI-green vertical slice.

**Architectural conflicts the 7 open questions never surface (decide control flow):**
- **B1 — plan-mode vs. writes.** Phase 7 writes to `docs/agent/`, but plan mode forbids all writes except the scratchpad. Must choose: skill runs in normal mode (no ExitPlanMode), OR cooperates with plan mode and defers all `docs/agent/` writes to *after* approval. Unresolved; reshapes everything. Add as Open Question #0.
- **B2 — auto-trigger + Workflow violates opt-in.** Workflow requires explicit user opt-in; an auto-fired skill isn't that. Auto-trigger path must gate the audit behind confirmation; only the slash-command path may auto-run it. Makes Q7 (cost surfacing) a correctness requirement.
- **B3 — `disable-model-invocation` vs. auto-trigger.** CONTRIBUTING says side-effecting skills set `disable-model-invocation: true`, which disables the auto-trigger D4 wants. Resolve via documented exception, or split into a read-only auto-advisor + side-effecting slash-command planner.

**Technical bugs:** the audit Workflow snippet would fail — missing `export const meta`, missing `.filter(Boolean)` before `findings.flatMap`, unpinned finding schema (`id`/`title`). It's illustrative pseudocode, not runnable. Also: the `.js` file isn't auto-run — SKILL.md must Read it and pass contents as `script`/`scriptPath`.

**Gaps:** MANIFEST "ledger pattern" referenced but no `ledger/` dir exists (repo edits MANIFEST directly); slash-command source-of-truth/symlink question open (commands aren't validated → test install manually); SKILL.md frontmatter key allowlist + line/char caps; done-criteria omits the three CI gates.

## Fix

Full corrected layout and severity-ordered findings live in the approved audit at `~/.claude/plans/cryptic-napping-hearth.md`. Recommended sequencing: resolve B1/B2/B3 with the user → re-walk Q1–Q7 → build the CI-green vertical slice mirroring `plugins/ship-agent-context/` exactly.

**B1/B2/B3 RESOLVED 2026-06-10** (user, captured as D5–D7 in [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md)):
- **B1 → D5 mode-aware hybrid:** detect plan mode; if active, run read-only + defer all `docs/agent/` writes until after `ExitPlanMode`; else write inline.
- **B2 → D6 always confirm:** always surface "run N-persona audit? ~X tokens" and wait for yes before launching Workflow, on both entry paths.
- **B3 → D7 single skill, auto-trigger kept:** one skill, `disable-model-invocation` unset/false; SKILL.md documents why it's exempt from the side-effect rule (writes are git-tracked markdown, audit is gated).

**Q1–Q7 RESOLVED 2026-06-10** — see the "Resolved Design Decisions" table in [ship-better-plans-design](../plans/ship-better-plans-design.md). Highlights: two modes (standard/ultra); core+context-adaptive personas; `/ship-plan`; skill-only (no hook); Mermaid DAG; audit-gate cost only; execution ships as a **separate future skill**, ship-better-plans ends by offering the execution choice.

Nothing remains open — the design is closed. Remaining work is build-only: the A-blockers are mechanical and folded into the corrected layout in the plan file.

## Prevention

Before building any new plugin in this repo: mirror `plugins/ship-agent-context/` structurally (`.claude-plugin/plugin.json` + symlinks + marketplace entry), and run all three CI gates plus an actual `/plugin install` before calling it done — a green validator does not prove a working install.

## Related
- [ship-better-plans-design](../plans/ship-better-plans-design.md) — the audited plan
- [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md) — D1–D4 (sound) + the D3 plan-mode consequence that B1 expands
- [marketplace-pluginroot-silently-ignored](../scars/marketplace-pluginroot-silently-ignored.md) — A1/A2 root
- [plugin-manifest-rejects-skills-field](../scars/plugin-manifest-rejects-skills-field.md) — A1 root
