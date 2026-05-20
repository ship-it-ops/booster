# Example: Full Read → Work → Write Session

This walkthrough shows a complete session cycle in a repo with an established `docs/agent/`. The agent reads existing context, consults it during work, and writes new context at milestones.

---

## Setup

The repo is `~/Repos/payments-api/`. It was scaffolded in [initialization-example.md](initialization-example.md). One week of work has happened since — there are now 6 notes.

---

## Session Start

### Step 1 — Read MANIFEST

```
> Read: docs/agent/MANIFEST.md
```

```markdown
# Agent Context
Last updated: 2026-05-25 | Total notes: 6

## Status (in-flight)
- [refactor-billing-module](status/refactor-billing-module.md) | status | active | standard | 2026-05-24 | Splitting billing into invoicing + dunning

## Decisions
- [agent-context-initialized](decisions/agent-context-initialized.md) | decision | active | core | 2026-05-19 | docs/agent set up for agent handoff
- [grpc-for-internal-services](decisions/grpc-for-internal-services.md) | decision | active | standard | 2026-05-19 | Switched internal RPCs from REST to gRPC

## Investigations
- [duplicate-charge-on-retry](investigations/duplicate-charge-on-retry.md) | investigation | active | standard | 2026-05-22 | Retry storm created duplicate Stripe charges

## Scars
- [stripe-idempotency-key-required](scars/stripe-idempotency-key-required.md) | scar | active | core | 2026-05-22 | NEVER call Stripe charge API without idempotency key
```

### Step 2 — Read `status/`

```
> Read: docs/agent/status/refactor-billing-module.md
```

```markdown
---
type: status
status: active
created: 2026-05-24
updated: 2026-05-24
author: claude-session-20260524-0915
branch: refactor/billing-split
tags: [billing, refactor]
---

# Refactoring billing module into invoicing + dunning

## Scope
- src/billing/ — splitting into src/invoicing/ and src/dunning/
- Tests in tests/billing/ moving to mirror new structure

## Why
Driven by [grpc-for-internal-services](../decisions/grpc-for-internal-services.md) —
the billing module is becoming two separate gRPC services and needs the code
split first.

## Blocked on
nothing currently
```

### Step 3 — Read `core` notes

```
> Read: docs/agent/decisions/agent-context-initialized.md
> Read: docs/agent/scars/stripe-idempotency-key-required.md
```

The `stripe-idempotency-key-required` scar is core importance — the agent commits its tripwire to memory:

> **Tripwire**: "if you see a Stripe charge call without `idempotency_key`, STOP."

### Step 4 — Begin work

```
User: I'm getting reports of duplicate emails to customers when the dunning
flow fails partway through. Can you investigate?
```

---

## During Work

### The agent consults existing context

```
> Grep: pattern "dunning" path docs/agent/
```

Returns the `refactor-billing-module` status entry. The agent notes that a sibling agent is in the middle of restructuring the dunning code — anything it changes could conflict.

```
Agent: Before I dig in: another session is mid-refactor of the billing module
on branch `refactor/billing-split`, splitting it into invoicing + dunning. I'll
investigate the duplicate-email bug against the current main, capture the root
cause, but coordinate with that session before making any code changes in
src/billing/dunning/.
```

The agent investigates, finds the bug: the dunning retry loop doesn't track which emails it has already sent within a single retry cycle.

### Milestone reached — capture investigation

This is a clear milestone. The agent applies the Write Protocol immediately.

**Step 1 — Search MANIFEST**: no existing investigation of dunning duplicate emails.

**Step 2 — Decide**: create new note.

**Step 3 — Write the file**:

**Created: `docs/agent/investigations/duplicate-emails-in-dunning-retry.md`**

```markdown
---
type: investigation
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-20260525-1100
tags: [dunning, retries, email, idempotency]
importance: standard
---

# Duplicate Emails in Dunning Retry Loop

## Symptoms
Customers receive 2–4 copies of the same dunning email within minutes during
retry storms. Reported by support 3x in the past week.

## Root Cause
`src/billing/dunning/retry.ts:retryFailedNotifications()` retries the whole
batch when ANY notification in the batch fails. It does not track per-notification
success, so successfully-sent emails get re-sent on the next retry.

## Fix
Track per-notification success/failure within a retry cycle. Only retry the
failed subset. Emit a metric `dunning.notifications.partial_failure_count`
so we can detect this class of bug earlier.

## Prevention
- Any retry loop over a batch must track per-item state.
- Add a lint or code-review checklist item: "retry loops over batches must
  track per-item outcome."

## Related
- [stripe-idempotency-key-required](../scars/stripe-idempotency-key-required.md) —
  same family of bug (retry without idempotency tracking)
- [refactor-billing-module](../status/refactor-billing-module.md) — sibling
  agent is restructuring this code; coordinate before patching
```

**Step 4 — Update MANIFEST**:

```diff
 ## Investigations
 - [duplicate-charge-on-retry](investigations/duplicate-charge-on-retry.md) | investigation | active | standard | 2026-05-22 | Retry storm created duplicate Stripe charges
+- [duplicate-emails-in-dunning-retry](investigations/duplicate-emails-in-dunning-retry.md) | investigation | active | standard | 2026-05-25 | Dunning retry resent already-delivered emails
```

```diff
-Last updated: 2026-05-25 | Total notes: 6
+Last updated: 2026-05-25 | Total notes: 7
```

**Step 5 — Links already added** in `## Related`.

### Pattern emerges — capture it too

The agent notices this is the second "retry without per-item tracking" bug in two weeks (the Stripe one + this one). That recurrence is itself a pattern worth recording.

**Created: `docs/agent/patterns/retry-loops-must-track-per-item-state.md`**

```markdown
---
type: pattern
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-20260525-1100
tags: [retries, idempotency, reliability]
importance: core
---

# Retry Loops Must Track Per-Item State

## When to Use
Any time code retries a batch of operations (notifications, charges, API
calls, message-queue sends).

## Implementation
- Maintain a per-item status map within the retry cycle.
- On retry, only resubmit items in `failed` or `pending` state.
- Emit a `partial_failure_count` metric when not all items in a batch succeed
  on the first try.

## Examples
- `src/billing/dunning/retry.ts` — after the 2026-05-25 fix.
- `src/payments/stripe-client.ts` — uses `idempotency_key` (the upstream
  service does the per-item tracking for us in that case).

## Gotchas
- "All-or-nothing" batch retries are the default mental model; resist this
  for any operation with user-visible side effects.
- Idempotency keys only protect you when the upstream service supports them.
  For our own code, we must track state ourselves.

## Related
- [stripe-idempotency-key-required](../scars/stripe-idempotency-key-required.md)
- [duplicate-emails-in-dunning-retry](../investigations/duplicate-emails-in-dunning-retry.md)
```

MANIFEST updated under `## Patterns`. Total notes: 8.

---

## End of Session

The agent has not modified code yet — the sibling agent is mid-refactor on the same module. Instead, it leaves a status entry for itself:

**Created: `docs/agent/status/dunning-duplicate-email-fix.md`**

```markdown
---
type: status
status: blocked
created: 2026-05-25
updated: 2026-05-25
author: claude-session-20260525-1100
branch: (not yet started)
tags: [dunning, bug-fix]
---

# Fix for dunning duplicate-email bug

## Scope
src/billing/dunning/retry.ts

## Why
Driven by [duplicate-emails-in-dunning-retry](../investigations/duplicate-emails-in-dunning-retry.md).

## Blocked on
[refactor-billing-module](refactor-billing-module.md) — wait for the
billing-split refactor to land before applying this fix on top.
```

The agent reports to the user:

```
Agent: Root cause is in src/billing/dunning/retry.ts — the retry loop resends
the whole batch instead of just failures. I wrote up the investigation and a
matching pattern (this is the second retry-without-per-item-tracking bug in
two weeks).

I did not apply the fix because another session is mid-refactor on the same
file. I left a blocked status entry — when the refactor lands, the next agent
will see it and pick up the fix on top of the new structure.

Three new notes added under docs/agent/. The pattern is core-importance, so
future agents on this repo will read it by default.
```

---

## What this demonstrates

- **MANIFEST + status first**: total reads at session start ≈ 4 files, under 5KB.
- **Sibling agent awareness**: the in-flight status entry prevented stomping.
- **Milestone-driven writes**: investigation captured immediately after root cause, not deferred.
- **Pattern emerges from repeated incidents**: writing the pattern as `core` means future agents see it without having to ask.
- **No code change committed** when blocked, but the *intent* to fix is preserved as a status entry for the next agent to pick up.
