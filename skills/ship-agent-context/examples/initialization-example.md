# Example: Initializing `docs/agent/` in a Repo

This walkthrough shows the first-run scaffold flow.

---

## Scenario

A developer opens Claude Code in `~/Repos/payments-api/`. The agent activates `ship-agent-context` and checks for prior context.

---

## Agent Behavior

### Step 1 — Probe for existing folder

```
> Glob: docs/agent/MANIFEST.md
> Result: no matches
```

The folder hasn't been initialized. The agent does NOT auto-create. It notes the absence and continues with the user's request.

### Step 2 — A decision is made

```
User: I'm switching this service from REST to gRPC. We picked gRPC because the
internal traffic is service-to-service and we want strict schemas. Cap it there
— no public-facing gRPC.
```

The agent now has a real decision to capture. *This* is when scaffolding pays off. The agent asks:

```
Agent: This is a decision worth keeping. I'd like to set up `docs/agent/` —
a committed folder where agents leave plans, decisions, and in-flight status
for future agents on this repo. Sound good?
```

```
User: yes
```

### Step 3 — Scaffold

```
> Bash: mkdir -p docs/agent/{decisions,plans,investigations,patterns,status,open-questions,scars,archive}
```

**Created: `docs/agent/MANIFEST.md`**

```markdown
# Agent Context
Last updated: 2026-05-19 | Total notes: 2

<!--
  This file is the index for `docs/agent/`. Agents read it at session start.
  Format: - [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
-->

## Status (in-flight)

## Decisions
- [agent-context-initialized](decisions/agent-context-initialized.md) | decision | active | core | 2026-05-19 | docs/agent set up for agent handoff context
- [grpc-for-internal-services](decisions/grpc-for-internal-services.md) | decision | active | standard | 2026-05-19 | Switched internal RPCs from REST to gRPC

## Plans

## Investigations

## Patterns

## Open Questions

## Scars
```

**Created: `docs/agent/decisions/agent-context-initialized.md`**

```markdown
---
type: decision
status: active
created: 2026-05-19
updated: 2026-05-19
author: claude-session-20260519-1430
tags: [meta, agent-handoff]
importance: core
---

# docs/agent/ Initialized

## Context
This repo now has `docs/agent/` — a committed folder where agents leave
context for future agents.

## Decision
Use the `ship-agent-context` skill (booster repo) to manage in-repo agent
memory. Standard subfolders: decisions/, plans/, investigations/, patterns/,
status/, open-questions/, scars/, archive/. MANIFEST.md is the index.

## Alternatives Considered
- **Inline notes in AGENTS.md**: rejected — AGENTS.md is for static rules,
  not dynamic state. Mixing them would bloat AGENTS.md and lose the rule/state
  distinction.
- **External knowledge vault (Obsidian)**: works for cross-repo memory but
  doesn't travel with branches. Use that skill in parallel if cross-repo
  memory is also wanted.

## Consequences
- Every branch sees the same agent context (committed to git).
- New agents must read MANIFEST.md + status/ at session start.
- AGENTS.md remains the source of truth for static rules.

## Related
- [grpc-for-internal-services](grpc-for-internal-services.md) — first real
  decision captured after init
```

**Created: `docs/agent/decisions/grpc-for-internal-services.md`**

```markdown
---
type: decision
status: active
created: 2026-05-19
updated: 2026-05-19
author: claude-session-20260519-1430
tags: [rpc, grpc, service-to-service]
---

# Use gRPC for Internal Service-to-Service RPC

## Context
The payments-api needs to call several other internal services. REST endpoints
have caused contract drift — schema changes ship without coordinated client
updates.

## Decision
Use gRPC for all internal service-to-service calls. Keep REST for any
public-facing or partner-facing endpoint.

## Alternatives Considered
- **Stay on REST + OpenAPI**: rejected — OpenAPI is opt-in, gRPC's protobuf
  schemas are enforced by the codegen pipeline.
- **GraphQL**: rejected — overkill for fixed service-to-service contracts;
  query flexibility isn't needed.

## Consequences
- New protobuf build step in CI.
- Existing REST endpoints stay (cap on the gRPC migration scope).
- Service mesh config needs gRPC-aware load balancing.

## Revisit Triggers
- If a public partner needs to call these endpoints (gRPC over the open
  internet has its own headaches).
- If protobuf schema review becomes a bottleneck.

## Related
- [agent-context-initialized](agent-context-initialized.md) — folder set up
```

### Step 4 — Confirm with the user

```
Agent: Done. Set up `docs/agent/` with two notes:

  1. agent-context-initialized — records why we set this up (importance: core)
  2. grpc-for-internal-services — your gRPC decision with the rationale

Future agents on this repo will read these at session start. I did not touch
AGENTS.md or CLAUDE.md — those are for static rules, this folder is for
dynamic state. If gRPC becomes the team-wide standard for new services,
that rule belongs in AGENTS.md and I can suggest the addition.
```

---

## Result

The repo now has:

```
payments-api/
  docs/
    agent/
      MANIFEST.md
      decisions/
        agent-context-initialized.md
        grpc-for-internal-services.md
      plans/
      investigations/
      patterns/
      status/
      open-questions/
      scars/
      archive/
```

The folder is staged for the next commit. From this point on, any agent — Claude, Cursor, Codex, a human reviewer — opening this repo will see the gRPC decision and the rationale behind it without needing to re-derive anything from `git log`.

---

## Auto-activation — already covered if installed via the plugin

If the skill was installed via the booster plugin marketplace (`/plugin install ship-agent-context@booster`), the bundled `hooks/hooks.json` already provides guaranteed session-start activation. You can skip the rest of this section.

### Manual-install workaround: `CLAUDE.md` / `AGENTS.md` anchor

Users who installed the skill manually (npx / cp / symlink) don't get the bundled hook. For reliable activation in those cases, add a one-liner to the repo's `CLAUDE.md` or `AGENTS.md`. These files are auto-loaded into the model's context every session, so the anchor is near-guaranteed activation.

```markdown
## Agent Context
This repo uses the `ship-agent-context` skill. At session start, read
`docs/agent/MANIFEST.md` and every file under `docs/agent/status/`. Capture
new decisions, plans, root causes, and scars as you go.
```

This is a one-time, manual addition. The skill itself never modifies `CLAUDE.md` / `AGENTS.md` — that boundary is intentional (those files hold static rules; `docs/agent/` holds dynamic state).

---

## What this demonstrates

- The skill does **not** auto-scaffold. It asks first, and only when there's a real reason.
- The seed `agent-context-initialized` note is `importance: core` — it will be read by default on every future session, ensuring the system's existence is always visible.
- The first real decision (`grpc-for-internal-services`) shows the full template, including `Alternatives Considered` and `Revisit Triggers`.
- `AGENTS.md` is untouched. The skill respects the rule/state boundary.
