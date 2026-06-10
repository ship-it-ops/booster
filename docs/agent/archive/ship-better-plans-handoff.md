---
type: status
status: completed
created: 2026-06-09
updated: 2026-06-10
author: claude-opus-4-7
tags: [handoff, ship-better-plans, in-flight]
importance: core
---

# Handoff: continue `ship-better-plans` skill design + implementation

> **For the next agent picking this up:** Read this first, then the plan and decisions linked at the bottom. The user will pick up where the prior session left off — they expect you to resume the brainstorm with Open Question #1 (scope boundary), not to start coding.
>
> ✅ **Update 2026-06-10 — DESIGN CLOSED. The brainstorm below is historical; do not re-ask Q1–Q7.** A full audit was run ([ship-better-plans-design-audit](../investigations/ship-better-plans-design-audit.md)): control-flow conflicts resolved as D5–D7 in the [architecture decision](../decisions/ship-better-plans-architecture.md); all 7 open questions resolved (see the "Resolved Design Decisions" table in the [plan](../plans/ship-better-plans-design.md)); the plan now carries the **corrected** plugin layout. **Next agent: skip straight to build** — implement the CI-green vertical slice mirroring `plugins/ship-agent-context/` per the corrected layout. Execution is a *separate* future skill, not part of this one.

## State at handoff

- Skill name: `ship-better-plans` — joins the `ship-*` family in this repo.
- Plugin destination: `plugins/ship-better-plans/` (mirror `plugins/ship-agent-context/` structure).
- **4 architectural decisions locked.** See [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md).
- **7 open questions remain.** See the full list in [ship-better-plans-design](../plans/ship-better-plans-design.md).
- No code written yet. No plugin scaffold yet. Brainstorm paused mid-question.

## Where the prior session paused

The prior agent was asking the user about **Open Question #1 — scope boundary at end of planning** when the user interrupted to commit everything into repo memory before handing off.

The three options for Q#1, ready to re-present via `AskUserQuestion`:

- **(a) Stop at "plan approved"** — skill ends after the audited plan is written, committed, and user-approved. Names the next step (e.g., `/execute-plan`, `superpowers:executing-plans`). Clean separation. Users re-enter execution in a fresh session.
- **(b) Plan + auto-kickoff execution** — once approved, the skill immediately spawns the executor (Workflow over the task DAG, or `executing-plans`). One trigger, full pipeline. Risk: long-running, mixes planning + execution context.
- **(c) Plan + offer execution choice** — after approval, present `start execution now / stop here / pick executor`. Most flexible, slight UX overhead.

## Your first move

1. **Activate `ship-agent-context`** (auto-activates at session start) to load standing user instructions and the full `docs/agent/` context.
2. **Read these three files in order**, top-to-bottom:
   - This status file.
   - [ship-better-plans-design](../plans/ship-better-plans-design.md) — full plan with expanded scope and open questions.
   - [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md) — locked decisions + alternatives + revisit triggers.
3. **Skim** `plugins/ship-agent-context/` and `skills/ship-agent-context/SKILL.md` to confirm the plugin/skill layout you'll mirror.
4. **Resume the brainstorm.** Use `AskUserQuestion` to re-present Q#1 (three options above). Then walk Q#2 through Q#7 from the plan file, one question per message, multiple-choice when possible.
5. **Only after all 7 open questions are resolved**, draft a v1 `SKILL.md` and persona prompts. Get user approval on the `SKILL.md` draft before writing supporting files.
6. **Commit incrementally** — one commit per layer (plugin shell → SKILL.md → templates → workflow script → slash command → optional hooks).
7. **Update `docs/agent/MANIFEST.md`** when each artifact lands. Update this status file (status → completed) and the plan file (status → completed) when the skill ships.

## Hard constraints — do not violate

- **Do not start coding the plugin yet.** Q#1–Q#7 must be resolved first. The user explicitly wants to finish the brainstorm before implementation.
- **No `Co-Authored-By` lines** in commits. Standing user instruction; see `~/.claude/projects/-Users-mohamede-Repos-Ship-It-Ops-booster/memory/feedback_no_coauthor.md`.
- **Do not push without asking.** General ship-* norm.
- **Do not invoke the `Workflow` tool during this brainstorm.** Workflow is for the audit phase of plans the *finished skill* produces, not for designing the skill itself.
- **One question per `AskUserQuestion` call.** Do not combine.
- **`docs/agent/MANIFEST.md` is append-friendly but conflict-prone** if multiple agents update concurrently. Use the ledger pattern from `ship-agent-context/reference.md` if you need to.

## Where things live

| Artifact | Path |
|----------|------|
| Plan (this work item) | `docs/agent/plans/ship-better-plans-design.md` |
| Architecture decisions | `docs/agent/decisions/ship-better-plans-architecture.md` |
| This handoff | `docs/agent/status/ship-better-plans-handoff.md` |
| Repo MANIFEST | `docs/agent/MANIFEST.md` |
| Pattern to copy | `plugins/ship-agent-context/`, `skills/ship-agent-context/` |
| Plan-mode scratchpad (historical, can be ignored) | `~/.claude/plans/alright-we-have-staged-whisper.md` |

## Done criteria for this handoff

The status entry flips from `active` to `completed` once:
- All 7 open questions resolved with the user.
- `SKILL.md` written and user-approved.
- Plugin scaffold (plugin.json, SKILL.md, reference.md, at least one template, the audit workflow script, the slash command) committed.
- `MANIFEST.md` updated to reflect the new plugin.
- The plan file ([ship-better-plans-design](../plans/ship-better-plans-design.md)) status flipped to `completed`.

## Related

- [ship-better-plans-design](../plans/ship-better-plans-design.md)
- [ship-better-plans-architecture](../decisions/ship-better-plans-architecture.md)
- [agent-context-initialized](../decisions/agent-context-initialized.md)
- [add-user-instructions-to-skill](../decisions/add-user-instructions-to-skill.md)
