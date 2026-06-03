# Example: Auto-Capturing a Standing User Instruction

This walkthrough shows the full lifecycle of an `instructions/` entry — capture, re-read in a new session, then revocation.

---

## Scenario

A developer is working in `~/Repos/payments-api/`. They've already used `ship-agent-context` for a while, so `docs/agent/` is initialized with `MANIFEST.md`, some decisions, and a status entry. No `instructions/` yet.

---

## Session 1 — Auto-capture

### Step 1 — User states a rule

```
User: Hey one more thing — don't commit or push without asking me first.
We had an incident last month where a half-baked feature went out to prod
because an agent auto-pushed.
```

The agent parses two distinct signals:

- **Trigger**: "don't … without asking" + recurring actions (`commit`, `push`) → this is a standing rule.
- **Why**: an actual incident the user mentioned — capture it, since it tells future agents *why* the rule exists.

### Step 2 — Agent writes the file silently

The agent runs (without asking):

```
> Bash: mkdir -p docs/agent/instructions
```

**Created: `docs/agent/instructions/dont-commit-or-push-without-asking.md`**

```markdown
---
type: instruction
status: active
created: 2026-06-02
updated: 2026-06-02
author: claude-session-20260602-1430
source: user-instruction
scope: always
tags: [git, safety, deploy]
importance: core
---

# Don't commit or push without asking first

## Instruction
"Don't commit or push without asking me first."

## Why
Last month, an agent auto-pushed a half-baked feature to prod. The user wants
an explicit confirmation step before any commit or push to prevent recurrence.

## How to apply
When the natural next step is `git commit`, `git push`, `gh pr merge`, or any
other action that mutates remote state, stop and ask the user before running
the command. Applies to all branches in this repo.

## Source
- Session: claude-session-20260602-1430
- Captured from: "don't commit or push without asking me first"

## To revoke
Say "you can commit/push without asking now" or "forget the no-push rule".
```

### Step 3 — Agent updates MANIFEST

**Edited: `docs/agent/MANIFEST.md`** — added the `## Instructions` section right after `## Status`:

```markdown
# Agent Context
Last updated: 2026-06-02 | Total notes: 5

## Status (in-flight)
- [backfill-job-on-feature-backfill](status/backfill-job-on-feature-backfill.md) | status | active | standard | 2026-06-01 | Backfill job running on feature/backfill branch

## Instructions
- [dont-commit-or-push-without-asking](instructions/dont-commit-or-push-without-asking.md) | instruction | active | core | 2026-06-02 | Ask before any commit or push (incident-driven)

## Decisions
…
```

### Step 4 — Agent acknowledges in one line

In the same response, the agent prints (single line, mandatory):

```
Agent: Saved as a standing instruction: docs/agent/instructions/dont-commit-or-push-without-asking.md.
Say "you can commit/push without asking now" anytime to revoke. I'll ask before any commit or push
for the rest of this session and every future one.
```

That's it. No confirmation prompt, no multi-paragraph summary. The user knows exactly what was written and how to undo it.

---

## Session 2 — Next-session acknowledgement

The user opens a new Claude Code session two days later in the same repo. The SessionStart hook fires:

```
> docs/agent/ is present in this repo. Before proceeding, read docs/agent/MANIFEST.md,
  every file under docs/agent/status/, and every file under docs/agent/instructions/.
  Capture new decisions, plans, root causes, scars, instructions, and open questions
  per the ship-agent-context skill as you go.
```

The agent reads `MANIFEST.md`, `status/`, and `instructions/`. The `dont-commit-or-push-without-asking` instruction is `importance: core`, so the agent acknowledges it in its opening response:

```
User: pick up where we left off on the backfill job
Agent: Got it. I'm picking up the backfill job on the `feature/backfill` branch.

Note: there's a standing instruction here — I won't commit or push without
asking you first (captured 2026-06-02 after an incident). I'll keep that
in place unless you tell me otherwise.
```

The rule has now survived a session boundary with zero re-statement from the user. That's the whole point.

---

## Session 3 — Revocation

A few weeks later the user has built more trust in the workflow:

```
User: ok you can commit and push without asking now, I trust the linting setup
```

The agent recognizes the revocation phrasing matches the rule's `## To revoke` line. It:

1. Edits `docs/agent/instructions/dont-commit-or-push-without-asking.md`:
   - Sets `status: revoked`.
   - Bumps `updated: 2026-06-21`.
   - Adds a top-of-body note: `> Revoked 2026-06-21 — user trusts the linting setup; ok to commit/push autonomously.`
2. Moves the file from `instructions/` to `archive/`.
3. Removes the entry from `## Instructions` in `MANIFEST.md`. If `## Instructions` is now empty, removes the section header too.
4. Confirms in one line:

```
Agent: Revoked. Moved to docs/agent/archive/dont-commit-or-push-without-asking.md.
I'll commit and push autonomously from now on.
```

The history isn't lost — `archive/` preserves the "asked then rescinded" trail, which is itself useful context (a future agent can see that this rule used to exist and what changed the user's mind).

---

## What this demonstrates

- **Capture is silent but visible.** No mid-conversation confirm prompt; one mandatory line of acknowledgement so the user always knows what was written.
- **One file per rule, slug from the rule itself.** Not from the user's verbatim words — `dont-commit-or-push-without-asking` not `hey-one-more-thing-dont-commit-or-push`.
- **Importance `core` instructions get acknowledged at session start.** Lower-importance ones are read silently and applied without ceremony.
- **Revocation is symmetric.** A natural-language sentence ("you can X now") undoes a natural-language rule ("don't X"). No commands or magic words.
- **`archive/` preserves the trail.** Revoked ≠ deleted. The history of what the user asked for and later rescinded is itself a useful signal.
- **AGENTS.md is untouched.** This rule originated from the user during a conversation, so it lives in `instructions/`. If after 30+ days it's still active, the skill will suggest promoting it to `AGENTS.md` as a project rule — but never silently.
