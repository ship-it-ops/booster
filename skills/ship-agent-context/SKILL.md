---
name: ship-agent-context
description: >
  ALWAYS activate at session start in any repository to check for `docs/agent/`
  — the in-repo memory of plans, decisions, in-flight status, open questions,
  patterns, and incident scars left by prior agents. Read `MANIFEST.md` and
  every file under `status/` before answering, planning, deciding, implementing,
  debugging, investigating, refactoring, reviewing, or fixing code. Activate
  whenever the user says "what did we decide", "what's in flight", "what's the
  plan for X", "any known issues / scars / blockers", "is anyone working on Y",
  "pick up where the last agent left off", or mentions prior agents, handoffs,
  or past incidents. Also activate to capture new context after a decision is
  made, a plan is finalized, a root cause is identified, a workaround is
  chosen, or a scar is earned — even when `docs/agent/` does not yet exist
  (offer to scaffold). Complements AGENTS.md / CLAUDE.md (static rules) by
  holding dynamic, branch-tracked state. Standalone — no external vault or
  other skill required.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir -p *), Bash(mv docs/agent/*)
---

## Purpose

You are an AI agent walking into a repository. Code, `git log`, and any static `AGENTS.md`/`CLAUDE.md` tell you *what exists* and *what the rules are*. They do not tell you:

- What plans the previous agent left half-finished.
- What decisions were made by other agents and *why* — including which approaches were rejected.
- What other agents are working on right now in parallel branches.
- Which questions are blocking forward progress.
- Which paths have burned the team before (incident scars).

This skill manages `docs/agent/` inside the repo as the **dynamic, team-shared handoff layer** for AI agents. It complements — never replaces — `AGENTS.md`/`CLAUDE.md`, which hold static project rules.

The folder is committed to git. Every agent on every branch sees the same context.

---

## Auto-Activation

When installed via the booster plugin marketplace (`/plugin install ship-agent-context@booster`), this skill ships a bundled SessionStart hook at `hooks/hooks.json`. The hook fires at the start of every Claude Code session and:

- Checks for `docs/agent/MANIFEST.md` in the current working directory.
- If present, injects a system reminder telling the model to read MANIFEST + every file under `docs/agent/status/` before proceeding and to use this skill for new context.
- If absent, the hook is silent — installing the plugin imposes ~no cost in repos that don't use `docs/agent/`.

This guarantees activation in repos that need it, independent of description matching. To disable, disable the plugin via `/plugin`. For users who installed the skill manually (npx / cp / symlink) rather than via the plugin marketplace, the hook is not present — anchor the skill in the repo's `AGENTS.md` or `CLAUDE.md` (see `examples/initialization-example.md`) for similar reliability.

---

## CRITICAL: Always Check `docs/agent/`

**At session start — before doing ANY work:**
1. `Glob: docs/agent/MANIFEST.md` to check if the repo has been initialized.
2. If yes: Read `MANIFEST.md`, then read every file under `docs/agent/status/` (small, ephemeral, always relevant), then read any `importance: core` decisions.
3. If no: do not auto-create. Note the absence; offer to scaffold only if the user's request would benefit (a decision is being made, a plan needs writing, etc.).
4. Only then begin working on the user's request.

**Before making decisions during a session:**
- Choosing a library, pattern, or architecture? → Check `docs/agent/decisions/` and `docs/agent/patterns/`.
- Debugging a bug? → Check `docs/agent/investigations/` and `docs/agent/scars/` for prior root causes and tripwires.
- Starting work in an area? → Check `docs/agent/status/` — a sibling agent may already be in that area.
- Hitting an unknown? → Check `docs/agent/open-questions/` — it may already be tracked.
- User states a preference that should outlive this session? → That belongs in `AGENTS.md`/`CLAUDE.md`, not here.

**If you skip the check, you risk:**
- Repeating work another agent completed last week.
- Contradicting a decision that has explicit rationale.
- Stomping on a sibling agent's in-flight branch.
- Re-stepping on an incident the team has already scarred over.

---

## Setup & Scaffolding

`docs/agent/` lives at a deterministic path inside the repo. No discovery is needed. The skill only needs to create it once.

### When to scaffold

Scaffold only when the user's current task will produce content worth capturing — a decision, a plan, an investigation root cause, a scar. Do not create empty folders just because the skill activated.

Before creating anything, confirm with the user:

> "I'd like to set up `docs/agent/` in this repo — a committed folder where agents leave plans, decisions, and in-flight status for future agents. Sound good?"

If the user declines: do not activate again this session.

### Scaffold layout

```
docs/agent/
  MANIFEST.md              ← the index you read first, every session
  decisions/               ← architecture, library, configuration choices
  plans/                   ← implementation plans, active and historical
  investigations/          ← bug hunts, root cause analyses
  patterns/                ← codebase conventions discovered by agents
  status/                  ← IN-FLIGHT work (cleared on completion)
  open-questions/          ← blockers awaiting human/maintainer answer
  scars/                   ← incidents and tripwires ("don't do X because Y")
  archive/                 ← superseded/deprecated content
```

Create with: `mkdir -p docs/agent/{decisions,plans,investigations,patterns,status,open-questions,scars,archive}`

Then write `docs/agent/MANIFEST.md` with the starter content shown in the [MANIFEST.md Format](#manifestmd-format) section. Also write a seed decision at `docs/agent/decisions/agent-context-initialized.md` documenting that this folder was set up and why (this becomes the first MANIFEST entry, proving the system works).

### Permissions

The folder is inside the repo, so no global permission setup is needed. Standard project file-write permissions apply.

---

## Read Protocol

When you need context, follow this order. Stop as soon as you have enough.

### Step 1 — Read MANIFEST
Read `docs/agent/MANIFEST.md`. It indexes every note: slug, type, status, importance, date, 8-word summary. Scan for entries relevant to your task.

### Step 2 — Read all of `status/`
Always read every file in `docs/agent/status/`. It is bounded in size (typically <5 entries) and is the single most important signal: it tells you what other agents are doing *right now*. Skipping this is how parallel agents collide.

### Step 3 — Read `core` decisions
For any note with `importance: core` in the MANIFEST, read the full file. These are foundational — you should know them by default.

### Step 4 — Read task-relevant notes
Open the 1–3 notes that most directly match your task. Read them fully. Stay focused — follow at most one hop of `## Related` links.

### Step 5 — Scan `open-questions/`
If a question is open in your task area, surface it to the user. Don't silently re-derive an answer; the team may already be waiting on a specific person to answer it.

### Step 6 — Search fallback
If the MANIFEST didn't surface what you need, Grep `docs/agent/` for keywords. Try synonyms (auth/authentication/login/token). This is the expensive path — most reads should resolve at Step 1.

### Rules
- **NEVER** glob-read every file in `docs/agent/`. Use the MANIFEST.
- **ALWAYS** check `status` before trusting a note. Skip `deprecated`. Treat `superseded` as a pointer to its replacement.
- **DO NOT** read `archive/` at session start — it's intentionally cold storage.
- **READ AGENTS.md and CLAUDE.md normally** — they hold static rules, not agent state. This skill does not duplicate them.

---

## Write Protocol

**Write incrementally, not at the end.** After each significant milestone — a decision made, a plan finalized, a root cause confirmed, a scar earned — evaluate whether it's worth persisting. Apply the **5-minute re-discovery threshold**: only write what would take more than 5 minutes for a future agent to reconstruct.

### What to write

- **Decisions** — architecture, library, or process choices with rationale.
- **Plans** — implementation plans you produced (the user's `/plan` output, an ExitPlanMode plan, a multi-step strategy).
- **Investigations** — bug root causes, especially non-obvious ones.
- **Patterns** — codebase conventions you discovered while reading code.
- **Status** — short-lived "I am working on X on branch Y" entries, cleared on completion.
- **Open questions** — blockers you can't resolve and the person/source that could.
- **Scars** — incidents that produced a lesson. Must name the tripwire ("if you see X, stop").

### What NOT to write

- Routine code changes (`git log` captures those).
- Obvious facts derivable from reading the code.
- Ephemeral todos (use the in-conversation task list).
- Anything already documented in `AGENTS.md`, `CLAUDE.md`, or `README.md` — link to those instead.
- Per-session journals — the user has explicitly excluded these.

### 5-Step Write Flow

**Step 1 — Search MANIFEST**: Scan for an existing note on this topic. Look for the same slug or an overlapping summary.

**Step 2 — Decide update vs. create**:
- **Same topic, exists, `active`**: edit the existing file. Bump `updated`.
- **Same topic, exists, `deprecated`**: create a new file. Set the old file's status to `superseded`. Add a pointer between them.
- **No match**: create a new file.

**Step 3 — Write the file** to `docs/agent/{folder}/{slug}.md` using the right template (see Content Types below). Before writing, run `mkdir -p docs/agent/{folder}` defensively — the subfolder may be missing if `docs/agent/` was hand-edited. Folder follows the type:

| Type | Folder |
|---|---|
| `decision` | `decisions/` |
| `plan` | `plans/` |
| `investigation` | `investigations/` |
| `pattern` | `patterns/` |
| `status` | `status/` |
| `open-question` | `open-questions/` |
| `scar` | `scars/` |

Slug rules: lowercase, hyphens for spaces, no special characters, max 60 chars. No project prefix (repo-scoped).

**Step 4 — Update MANIFEST**: Add or update the entry under the right section. Format:
```
- [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
```
Bump `Last updated` and `Total notes`.

**Step 5 — Add `## Related` links** (3–5 max) to other notes that share a causal or dependency relationship. Use relative links: `[slug](../decisions/slug.md)`.

---

## Content Types & Templates

All notes share this base frontmatter:

```yaml
---
type: decision | plan | investigation | pattern | status | open-question | scar
status: active | completed | superseded | deprecated | blocked
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: <agent-id, claude-session-id, or human handle>
tags: [list, of, tags]
importance: core | standard | minor   # optional, defaults to standard
---
```

### Decision

For architecture, library, configuration, or process choices.

```markdown
# {Descriptive Title}

## Context
What situation prompted this decision?

## Decision
What was decided.

## Alternatives Considered
- **Option A**: rejected because…
- **Option B**: rejected because…

## Consequences
What does this enable, prevent, or commit us to?

## Revisit Triggers
Concrete conditions that should reopen this decision (e.g., "if request volume exceeds 10k/min").

## Related
- [other-note](../decisions/other-note.md) — why it's related
```

### Plan

For implementation plans produced by an agent. Captures plans that would otherwise be lost when the session ends.

```markdown
# {Plan Title}

## Goal
What this plan accomplishes.

## Approach
Step-by-step strategy.

## Files to Touch
- `path/to/file` — what changes

## Status
What's done, what's next, what's blocked.

## Related
- [decision-this-followed](../decisions/x.md)
```

`status` in the frontmatter is `active` while in flight, `completed` when shipped, `superseded` if replaced.

### Investigation

For bug hunts and root cause analyses.

```markdown
# {Bug or Issue Title}

## Symptoms
What was observed.

## Root Cause
What was actually wrong. Be specific — file, line, mechanism.

## Fix
What solved it.

## Prevention
How to avoid recurrence.

## Related
- [scar-if-incident-grade](../scars/x.md)
```

### Pattern

For recurring codebase conventions discovered while reading code.

```markdown
# {Pattern Name}

## When to Use
Situations that call for this pattern.

## Implementation
How it's implemented in this codebase. Key files, functions.

## Examples
Brief code references showing the pattern in action.

## Gotchas
Common mistakes when applying it.
```

### Status (in-flight)

Short-lived entry that signals "an agent is working on this right now". Extra required fields:

```yaml
type: status
status: active | blocked | completed
branch: feature/x
agent: claude-session-2026-05-19-1430   # any stable identifier
```

```markdown
# {What you're doing, in one line}

## Scope
Files or areas being touched.

## Why
Link to the decision, plan, or issue driving this.

## Blocked on
(only if status: blocked) — what needs to resolve.
```

**Lifecycle**: when the work merges or is abandoned, change `status` to `completed` and move the file from `status/` to `archive/` (or delete if it added no durable knowledge). `status/` should rarely have more than 3–5 active entries at once.

### Open Question

A blocker awaiting an answer. Extra required fields:

```yaml
type: open-question
status: active | answered | abandoned
opened: YYYY-MM-DD
answer-source: docs | maintainer | experiment | unknown
```

```markdown
# {The question, phrased as a question}

## Context
What we know so far, and why we need an answer.

## Tried
What we attempted to resolve it ourselves.

## Who Can Answer
Name, role, or "needs experiment".
```

Flag any `active` open question older than 30 days for review.

### Scar

A lesson from a real incident. Extra required fields:

```yaml
type: scar
status: active
incident-date: YYYY-MM-DD
tripwire: "if you see X, stop and check Y"
```

```markdown
# {Short title — the lesson, not the bug}

## What Happened
Brief incident summary.

## Tripwire
The one-line condition that should make a future agent stop.

## Why It Hurt
What broke, who paid, how bad.

## Don't Do This
Specific action to avoid.

## Related
- [investigation-of-incident](../investigations/x.md)
```

Scars are immutable. Update them only to refine the tripwire. Never set `status: deprecated` on a scar — once the team has been burned, the lesson stands.

---

## MANIFEST.md Format

```markdown
# Agent Context
Last updated: YYYY-MM-DD | Total notes: N

<!--
  This file is the index for `docs/agent/`. Agents read it at session start.
  Format: - [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
-->

## Status (in-flight)
<!-- always-read at session start -->

## Decisions
## Plans
## Investigations
## Patterns
## Open Questions
## Scars
```

Sections appear only when they have entries. Order is fixed — `Status` always first.

When the file exceeds ~100 entries, split per-section into `MANIFEST-decisions.md`, `MANIFEST-plans.md`, etc. Keep `MANIFEST.md` as the entrypoint with the 10 most recent per section plus all `core` importance entries.

---

## Relationship to AGENTS.md and CLAUDE.md

This skill **does not modify or duplicate** `AGENTS.md` or `CLAUDE.md`.

- `AGENTS.md` / `CLAUDE.md` = **static rules** the project asks agents to follow ("use pnpm", "tests live in `__tests__/`", "never commit without running lint").
- `docs/agent/` = **dynamic state** captured during work (decisions made, plans in flight, scars earned).

If a rule emerges from a captured decision — e.g., a `decisions/` note concludes "we now standardize on pnpm" — that rule belongs in `AGENTS.md`. The skill should suggest the update, not perform it silently. The decision note links to the rule; the rule links back to the decision.

---

## Multi-Agent Coordination

Parallel agents (different terminal sessions, different branches) coordinate through `status/`.

**Before starting work in an area:**
1. Read all `status/` entries.
2. If an entry overlaps your scope and is `active`, surface it: "Another agent is on branch X touching these files. Want me to pause, coordinate, or work elsewhere?"
3. If your work proceeds, create your own `status/` entry within the first 5 minutes — don't wait until done.

**While working:**
- Update your `status/` entry when scope changes or you become blocked.
- Don't create new `decisions/` or `plans/` entries that contradict another agent's `status/` without coordinating first.

**Concurrent writes to MANIFEST.md** can conflict. For repos that frequently run multiple agents in parallel, use the ledger pattern documented in `reference.md` — each agent writes its MANIFEST entries to `docs/agent/ledger/{session-id}.md`, and the next agent to start merges them.

---

## Anti-Bloat Rules

The folder must not become a dumping ground. Apply these filters every time you consider writing:

1. **5-minute rule**: If a future agent could re-derive this in under 5 minutes from code or `git log`, don't write it.
2. **No duplication**: If it's in `AGENTS.md`, `CLAUDE.md`, `README.md`, or a code comment, link to it instead.
3. **No routine logging**: Code changes are in `git log`. Tasks are in your tool's task list. Neither belongs here.
4. **One topic, one note**: Update the existing note instead of creating a near-duplicate.
5. **Status entries expire**: If `status/` has entries older than 14 days that haven't been touched, flag them. Stale `status/` is the #1 failure mode.
6. **Open questions age out**: 30 days `active` → ask the user if it's still open.
7. **Tags are search keys**: 3–5 tags per note. Reuse tags from existing notes — consistency makes search work.

---

## Session Lifecycle

### Start of Session (mandatory, before any work)
1. `Glob: docs/agent/MANIFEST.md`. If missing, note and skip to user's request (do not auto-scaffold).
2. Read `MANIFEST.md`.
3. Read every file in `docs/agent/status/`.
4. Read every `importance: core` note.
5. Scan `open-questions/` for anything matching the user's request.
6. Begin work.

### During Work
7. Before each major decision: check `decisions/` and `patterns/` for prior art.
8. Before debugging: check `investigations/` and `scars/`.
9. Within 5 minutes of starting non-trivial work: create a `status/` entry.
10. On every milestone (decision made, root cause found, plan finalized, scar earned): apply the Write Protocol immediately. Don't defer to end-of-session.
11. Reference captured knowledge in responses — tell the user what you found.

### End of Session
12. Review: any decision, plan, root cause, or scar uncaptured? Write it.
13. Update your `status/` entry: complete it (and archive), or update its current state.
14. If you flagged stale notes during the session, summarize them for the user before finishing.

---

## What This Is NOT

- **Not a task tracker.** Use the in-conversation task list or an issue tracker for todos.
- **Not a replacement for `AGENTS.md` / `CLAUDE.md`.** Those hold static rules; this holds dynamic state.
- **Not a replacement for documentation.** Public-facing docs, READMEs, API references belong in their normal locations.
- **Not a journal.** Per-session chronological logs are excluded by design — `git log` covers that.
- **Not cross-repo.** This is repo-local. For knowledge that crosses repos, pair with `obsidian-knowledge-graph` (separate skill, optional).
- **Not unlimited.** Designed for ~100–300 notes. Beyond that, split MANIFEST per section.

For extended patterns — team mode, multi-instance ledger, scaling, staleness heuristics, MCP integration — see `reference.md`.
