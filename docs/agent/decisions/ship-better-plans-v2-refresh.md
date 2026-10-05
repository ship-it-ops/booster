---
type: decision
status: active
created: 2026-10-01
updated: 2026-10-01
author: claude-fable-5-1
tags: [skill, plugin, planning, audit, workflow, ship-family, ship-execute]
importance: core
summary: 2.0 rewrite: cards, linter, grounded review; revises D6/Q3
---

# `ship-better-plans` 2.0: what changed from the 1.0 architecture, and why

## Context

The user asked for a full refresh of the `ship-*` skills for current models and the current Claude Code harness, starting with `ship-better-plans`, evaluated through multiple agent personas. Six independent reviewers audited 1.0, and 1.0 was run on two real planning scenarios in this repo with the plans judged by a cold-read executor and a grounding checker. The evidence is in [ship-better-plans-refresh-audit](../investigations/ship-better-plans-refresh-audit.md).

The 1.0 architecture is recorded as D1–D7 in [ship-better-plans-architecture](ship-better-plans-architecture.md). This note records which of those decisions 2.0 keeps and which it revises.

## Decision

### Kept

- **D1 (standalone, parallel to superpowers), D2 (Workflow-based audit), D3 (`docs/agent/` artifacts), D4 and D7 (auto-trigger plus `/ship-plan`, one skill), D5 (plan-mode aware).** All stand. D2 gains a fallback to parallel Agent calls, because the Workflow tool is not available in headless runs. D5 gains a self-contained "after approval" block in the plan-mode file, because approval can clear the conversation.

### Revised

- **R1 — Discovery before questions; one checkpoint.** 1.0 ran an eight-field intake, one question at a time, before reading any code. 2.0 drafts the brief from the request, reads the repository, designs, and then stops once: brief, recommended approach, up to four batched questions, review depth. Why: every reviewer flagged the intake as the largest source of friction, and the repository answers most intake questions better than the user can.
- **R2 — Task cards are the plan's primary artifact.** 1.0 tasks were Mermaid node labels. 2.0 tasks are self-contained cards (`Depends on`, `Covers`, `Files`, `Do`, `Verify`, `Kind`, `Size`, `Reversibility`, `Gate`) plus a "Conventions for every task" block; the execution order is derived from the cards by the linter. Why: `ship-execute` hands each task to a fresh agent that never sees the rest of the plan, and baseline plans scored 5–6 out of 10 on cold executability for exactly this reason.
- **R3 — A deterministic linter.** `scripts/lint_plan.py` checks what a model should not be trusted to check by eye: traceability, the dependency graph, a stale execution order, parallel file collisions, gates, and that cited files and evidence lines exist. Why: these are mechanical properties, and "self-check" lists were being ticked without being true (both 1.0 example plans broke the skill's own rules).
- **R4 — D6 revised: consent for the review is collected once, at the checkpoint.** 1.0 always asked a separate cost question before launching the audit. 2.0 asks for the review depth (none, light, full, ultra) as one of the checkpoint questions, stating agent counts, and treats an explicit `/ship-plan ultra` as the choice already made. The user's choice is still what authorizes the Workflow call. Why: the separate gate was an extra round trip that could only show an invented token figure.
- **R5 — Reviewer set revised (was Q3: Adversarial, Pragmatist, Production).** Core reviewers are now `executor` (cold read of each card), `grounding` (plan against repository), `adversary` (premortem) and `scope` (request fidelity and simplification); `security`, `data`, `ops` and `tests` are chosen by the script from the plan's content, not by the plan's author. Reviewers read the plan file and the repository, where 1.0 reviewers saw only pasted plan text. Why: the old personas were attitudes; the failure modes that sink plans are ungrounded claims and cards that cannot be executed cold.
- **R6 — Verification no longer defaults to "refuted".** 1.0 dropped a finding whenever a single verifier was unsure. 2.0 uses confirmed / refuted / uncertain, returns uncertain findings as disputed, gives a refuted blocker a second opinion, and reports dropped findings, failed reviewers and unverified findings. Why: for plans, a silently dropped true blocker costs far more than a false positive the planner can dismiss.
- **R7 — Ultra is bounded and converges on a revised plan.** 1.0's loop re-read an unchanged plan with an exact-title dedup key and no round cap. 2.0 caps rounds at three, tells each round what was already found, merges duplicates across rounds, stops when a round confirms a blocker (revise first), and adds a `recheck` mode that reads the revised plan.
- **R8 — "No quick mode" revised.** Plans are sized to the work (`N/A — reason`, no separate requirements for small plans), and a one-agent light review exists. Why: a single depth for every task produced filler and made mid-sized work not worth the ceremony.
- **R9 — Draft and approval are explicit.** The plan file is written at specification time with `approval: draft` and flipped to `approved` only on the user's yes; an unattended run ends with a draft and named assumptions instead of stalling.
- **R10 — `ship-execute` 1.1.0 reads the new format in the same change.** It parses cards, passes the conventions block and the text of the ids in `Covers`, pauses at a `Gate`, refuses a draft plan without confirmation, and warns on a stale `base`. Why: all six reviewers of the rewrite flagged that a plan format the executor does not honour gives false safety. This was the one edit made outside `ship-better-plans`; the rest of `ship-execute` is unchanged and still due its own refresh.

## Alternatives Considered

- **Patch 1.0 in place** (fix the Workflow script, keep the eight-phase flow). Rejected: the two largest problems, task format and intake order, are structural.
- **Keep numeric 1–5 tradeoff scores and a mandatory two-to-three options.** Rejected: unanchored numbers look rigorous and are not, and forced alternatives produced strawmen ("do nothing").
- **Per-finding majority voting (three verifiers each).** Rejected for cost; one verifier with a three-way verdict, a second opinion on refuted blockers, and a recheck of the revised plan cover the same risk for fewer agents.
- **Leave `ship-execute` untouched until its own refresh.** Rejected: see R10.
- **Have the linter rewrite the execution order in place** (`--write-dag`). Rejected for now: plan mode forbids shell writes; the linter instead rejects a pasted order that no longer matches the cards.

## Consequences

- Plans in the old format still execute (the executor falls back to a linear task list) but do not pass the linter. `plan_format: 2` in the frontmatter marks the new format.
- A full review costs about 11–12 agents and 1.1–1.4 million subagent tokens for a 300–380 line plan (two measured runs). The checkpoint states agent counts so the user chooses knowingly.
- The skill now ships Python (`lint_plan.py`, standard library only) and a CI job that runs its 43 unit tests and lints the three bundled example plans, so the examples cannot drift from the rules.
- `reference.md` became three step-scoped files (`reference-planning.md`, `reference-cards.md`, `reference-review.md`).

## Revisit Triggers

- Plans written without a review keep showing false claims about the repository (grounding was flat without review in the evaluation: 8 → 8 and 8 → 9 out of 10) → make the light review the default instead of an option.
- Users skip the review because of its cost → add a cheaper tier between light and full (for example `executor` plus `grounding` with verification).
- The linter's warnings prove noisy on monorepos or non-JavaScript stacks → relax or scope the path and script heuristics.
- `ship-execute`'s own refresh changes how task agents are briefed → update the contract table in `reference-cards.md` and the `HANDOFF` text in the audit script together.
- The Workflow tool's API changes → re-run the audit script's dry-run scenarios and one live run.

## Related

- [ship-better-plans-refresh-audit](../investigations/ship-better-plans-refresh-audit.md) — the evidence behind every revision above
- [ship-better-plans-architecture](ship-better-plans-architecture.md) — D1–D7, the 1.0 decisions this note keeps or revises
- [ship-execute-architecture](ship-execute-architecture.md) — the executor whose plan contract R10 extends
- [ship-better-plans-design](../plans/ship-better-plans-design.md) — the 1.0 design plan
