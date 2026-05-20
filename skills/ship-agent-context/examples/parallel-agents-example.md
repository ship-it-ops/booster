# Example: Parallel Agents Coordinating via `status/`

This walkthrough shows two agents running concurrently on the same repo, using `docs/agent/status/` as the coordination signal that prevents collision.

---

## Scenario

Two developers are working on `payments-api` simultaneously, each with their own Claude Code session.

- **Agent A** — opened at 09:15, working on splitting the billing module.
- **Agent B** — opened at 10:30, asked to investigate a dunning bug.

Both sessions see the same `docs/agent/` because it's committed to git and they're each on a fresh branch from main.

---

## 09:15 — Agent A starts work

### Read

```
> Read: docs/agent/MANIFEST.md
> Read: docs/agent/status/   (empty)
```

Nothing in flight. Agent A is free to start.

### User request to Agent A

```
User A: Split src/billing/ into src/invoicing/ and src/dunning/. We discussed
this in standup — it's a prerequisite for the gRPC migration.
```

### Within 5 minutes — Agent A creates a status entry

**Created: `docs/agent/status/refactor-billing-module.md`**

```markdown
---
type: status
status: active
created: 2026-05-24
updated: 2026-05-24
author: claude-session-A-20260524-0915
branch: refactor/billing-split
tags: [billing, refactor]
---

# Refactoring billing module into invoicing + dunning

## Scope
- src/billing/ — splitting into src/invoicing/ and src/dunning/
- Tests in tests/billing/ moving to mirror new structure

## Why
Prerequisite for the gRPC migration ([grpc-for-internal-services](../decisions/grpc-for-internal-services.md)).

## Blocked on
nothing
```

MANIFEST updated. Agent A continues splitting files on branch `refactor/billing-split`.

---

## 10:30 — Agent B starts

### Read

```
> Read: docs/agent/MANIFEST.md
> Read: docs/agent/status/refactor-billing-module.md
```

Agent B immediately sees Agent A's status entry.

### User request to Agent B

```
User B: We're seeing duplicate dunning emails when retries kick in. Can you
fix it?
```

### Agent B surfaces the conflict

```
Agent B: Before I start: another session is mid-refactor on src/billing/,
splitting it into invoicing + dunning on branch `refactor/billing-split`.
Their status entry was created at 09:15 today, untouched since — likely
still active.

I'll investigate the bug against main and capture the root cause, but I
won't apply the fix in src/billing/dunning/ until the refactor lands.
Otherwise our changes will conflict. Sound good?
```

```
User B: yeah, do the investigation and leave the fix for later.
```

### Agent B does its work and writes

Agent B traces the bug, writes `docs/agent/investigations/duplicate-emails-in-dunning-retry.md`, and creates its own status entry — **blocked** on Agent A:

**Created: `docs/agent/status/dunning-duplicate-email-fix.md`**

```markdown
---
type: status
status: blocked
created: 2026-05-24
updated: 2026-05-24
author: claude-session-B-20260524-1030
branch: (not yet started)
tags: [dunning, bug-fix]
---

# Fix for dunning duplicate-email bug

## Scope
src/billing/dunning/retry.ts (current path)

## Why
[duplicate-emails-in-dunning-retry](../investigations/duplicate-emails-in-dunning-retry.md)

## Blocked on
[refactor-billing-module](refactor-billing-module.md) — wait for billing
split to merge so the fix lands on top of the new structure.
```

---

## 14:00 — Agent A finishes and merges

Agent A's refactor PR merges into main. Agent A updates its status entry:

```diff
---
-status: active
+status: completed
-updated: 2026-05-24
+updated: 2026-05-24
+merged-pr: 1247
```

Then archives it:

```
> Bash: mv docs/agent/status/refactor-billing-module.md docs/agent/archive/
```

MANIFEST updated — entry removed from `## Status (in-flight)`. Agent A also captures a pattern note about how the refactor was structured.

---

## 14:30 — A new session (Agent C) picks up Agent B's blocked work

A developer opens a new session and asks:

```
User C: Anything blocked that's now ready to ship?
```

### Agent C reads

```
> Read: docs/agent/MANIFEST.md
> Read: docs/agent/status/dunning-duplicate-email-fix.md
```

Agent C sees the `blocked` status entry. It checks the dependency:

```
> Read: docs/agent/archive/refactor-billing-module.md
```

The blocker is `completed`. Agent C unblocks the work:

```
Agent C: There's one blocked task: a dunning duplicate-email fix that was
waiting on the billing split. The split landed today (PR #1247), so the fix
is unblocked.

The investigation is already written up. New file path is
src/dunning/retry.ts (the file moved during the refactor). Want me to take
the fix?
```

Agent C updates the status entry:

```diff
---
-status: blocked
+status: active
-branch: (not yet started)
+branch: fix/dunning-duplicate-emails
-author: claude-session-B-20260524-1030
+author: claude-session-C-20260524-1430
-## Blocked on
-[refactor-billing-module](refactor-billing-module.md) — wait for billing
-split to merge so the fix lands on top of the new structure.
+## Unblocked
+refactor-billing-module merged at 14:00 today. Picking this up.
```

---

## What This Demonstrates

1. **Status entries are the lock signal.** Agent B didn't need any messaging system to know Agent A was mid-refactor — the in-repo status file was sufficient.

2. **Blocked work is preserved.** Agent B's investigation and intent-to-fix didn't evaporate when its session ended. The next agent — even a different session, even a different developer — picked up exactly where it left off.

3. **Status files have a lifecycle.** Active → blocked → active → completed → archived. Each transition is explicit, dated, and visible in MANIFEST.

4. **Multi-instance writes are safe enough for small teams.** Each status note has a unique slug, so file creation never collides. The only shared file is MANIFEST.md — for higher concurrency (3+ simultaneous agents), use the [ledger pattern in `reference.md`](../reference.md#multi-instance-mode-ledger-writes).

5. **No external system was used.** No Linear, no Slack thread, no project board. The coordination signal lives in the repo, travels with branches, and survives session boundaries.

---

## Anti-patterns to avoid

- **Don't skip the status entry "because the work is quick."** Five-minute tasks turn into hour-long tasks when someone else starts on the same file in parallel.
- **Don't delete completed status entries** — archive them. The fact that work was done is itself useful context for the next agent.
- **Don't write a status entry as a wish list.** It's only for work the agent is actively pursuing right now (or is genuinely blocked on). Future-intent belongs in `plans/`.
