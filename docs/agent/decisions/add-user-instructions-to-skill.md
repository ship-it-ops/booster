---
type: decision
status: active
created: 2026-06-02
updated: 2026-06-02
author: claude-opus-4-7
tags: [meta, agent-context, instructions, user-rules]
importance: core
---

# Add `instructions/` content type for standing user rules

## Context

The previous version of `ship-agent-context` (1.0.0) captured agent-authored state — decisions, plans, investigations, patterns, in-flight status, open questions, scars — but had no first-class surface for **standing user instructions**: behavior rules the user gives Claude in conversation that should persist across sessions ("don't push without asking", "always run the linter first", "use pnpm here").

The original `SKILL.md` punted on these:

> "User states a preference that should outlive this session? → That belongs in `AGENTS.md`/`CLAUDE.md`, not here."

In practice that line failed users:

- Most repos don't have `AGENTS.md` / `CLAUDE.md` — so the instruction had nowhere to land.
- Even when those files exist, editing them feels heavy for a one-liner.
- The user-level auto-memory at `~/.claude/projects/.../memory/` is per-user-machine-local, not committed and not visible to other agents on other branches.
- Concrete user pain: "I tell Claude 'don't push without asking' every session and have to remind it every time."

## Decision

Add an `instruction` content type and matching `instructions/` subfolder to `docs/agent/`. Treat the folder as always-read at session start (alongside `status/`). Auto-capture instructions silently when the user uses persistent-intent phrasing (triggers and anti-triggers spelled out in `SKILL.md`). Tell the user where the file lives and how to revoke, in one line, in the same response.

Bump the plugin to `1.1.0`.

## Alternatives Considered

- **Tell the user to edit `AGENTS.md` / `CLAUDE.md` instead** — rejected. The friction is the bug. Most repos don't have those files and even when they do, "edit a config file" is a worse UX than "Claude remembers what I said."
- **Use the user-level auto-memory only** — rejected for cross-agent / team use cases. Auto-memory is local to one user on one machine; standing rules like "don't force-push on `main`" should travel with the repo and apply to every agent on every branch.
- **Confirm before each capture ("want me to save this?")** — rejected by the user explicitly. The user chose "auto-write without confirming" and traded the per-capture confirm for a mandatory single-line announcement after the fact + an easy revocation flow. Trigger precision becomes the safety mechanism instead.
- **Reuse `decisions/`** — rejected. Decisions capture *why* an architectural choice was made (with alternatives considered and revisit triggers). Instructions capture *what the user told the agent to do or not do*. Different shape, different read priority — instructions are always-read at session start; decisions are read on demand or only if `importance: core`.
- **Use the existing `scars/` folder** — rejected. Scars are incident-derived ("we got burned, here's the tripwire"). Instructions can be preventive without an incident behind them.

## Consequences

- Every Claude session in a repo with `docs/agent/` now reads `instructions/` automatically and applies every `active` rule.
- The user no longer has to re-state the same rule each session — this was the explicit pain point.
- `AGENTS.md` / `CLAUDE.md` remain the **high-authority, maintainer-curated** surface; `instructions/` is the **low-friction, user-captured** surface. Promotion path: after 30 days `active`, the skill suggests copying the rule into `AGENTS.md`.
- Auto-capture introduces a (small) risk of capturing a one-off correction as a permanent rule. Mitigated by (a) explicit anti-trigger phrases in `SKILL.md`, (b) a mandatory one-line announcement on every write, and (c) the one-per-turn cap.
- The plugin SessionStart hook now mentions `instructions/` in its echo line, so the activation reminder pulls the new folder into the always-read pass.

## Revisit Triggers

- If auto-captured instructions start showing up that the user didn't mean as standing rules → tighten the trigger list in `SKILL.md` (or add to the anti-trigger list).
- If users complain the one-line announcement gets lost in long responses → consider moving to a more visible surface (e.g., a structured block at the end of the response).
- If parallel agents start writing conflicting instructions on the same topic from different sessions → revisit the conflict-resolution rules in `reference.md` and consider extending the ledger pattern from MANIFEST writes to instruction writes.

## Related

- [agent-context-initialized](agent-context-initialized.md) — the foundational decision this builds on
- Plan file: `~/.claude/plans/alright-we-are-prancy-thacker.md` — the implementation plan approved before the changes
