# Obsidian Knowledge Graph — Reference

Extended reference for advanced patterns, team workflows, and scaling strategies. The core skill (SKILL.md) covers everyday usage. This file covers everything beyond the defaults.

---

## Detailed Note Templates

### Decision — Extended Fields

For complex decisions that affect multiple systems:

```yaml
---
type: decision
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: auth, security, api
project: backend-api
supersedes: auth-basic-auth-choice
---
```

Optional extended sections:

```markdown
## Alternatives Considered
- **Option A**: Description. Rejected because...
- **Option B**: Description. Rejected because...

## Validation
How we confirmed this was the right choice. Benchmarks, prototypes, team feedback.

## Revisit Triggers
Conditions that should prompt revisiting this decision:
- If request volume exceeds 10k/min
- If we add a mobile client
- If the security audit flags token handling
```

### Investigation — Extended Fields

For complex multi-day investigations:

```yaml
---
type: investigation
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: performance, database, memory
time-to-resolution: 6 hours
severity: critical
---
```

Optional extended sections:

```markdown
## Timeline
- 10:00 — First symptom observed (OOM in staging)
- 10:30 — Reproduced locally with load test
- 11:15 — Isolated to connection pool exhaustion
- 12:00 — Root cause confirmed: leaked connections in error path
- 14:00 — Fix deployed and verified

## Environment
- OS: Ubuntu 22.04
- Runtime: Node.js 20.11
- Database: PostgreSQL 16.1
- Relevant config: `max_connections=100`, pool size 20
```

---

## Team Mode

The central vault model naturally supports teams. Since the vault lives outside any single repo, multiple developers can point their agents at the same vault (e.g., via a shared network drive, Obsidian Sync, or a git-synced vault).

### Shared vs. Personal Knowledge

For teams that want separation:

```
{vault}/_ai/
  MANIFEST.md                  — shared index
  notes/                       — shared knowledge
  personal/                    — per-developer context
    alice/
      MANIFEST.md
      notes/
    bob/
      MANIFEST.md
      notes/
```

- **Shared notes** in `_ai/{folders}/` — team-agreed decisions, documented patterns, resolved investigations
- **Personal notes** in `_ai/personal/{username}/notes/` — individual context, draft investigations, scratch knowledge
- The agent should check `whoami` or `git config user.name` to determine the personal folder

### Team Review Workflow

Periodically (weekly or at sprint boundaries):
1. Review notes with `status: active` and `updated` older than 30 days — still accurate?
2. Check for near-duplicate notes (similar slugs or overlapping tags)
3. Deprecate notes that no longer reflect current architecture
4. Promote valuable personal notes to shared

---

## Cross-Project Knowledge Discovery

One of the key benefits of a central vault is that knowledge flows between projects. Here's how to leverage it:

### Proactive Surfacing

When reading MANIFEST at session start, scan ALL entries — not just the current project. If you see a note from another project that's relevant to the current task, mention it:

> "I found a related pattern from your `chat-service` project — they solved a similar WebSocket connection management issue. Want me to pull that up?"

### Cross-Project Patterns

When you notice the same pattern appearing in multiple projects, consider creating a project-agnostic pattern note:

```
general--websocket-connection-management.md
```

Use `general` as the project prefix for patterns that transcend a single codebase. Link the project-specific notes to the general pattern.

### Cross-Project Linking

Always link across projects when there's a genuine relationship:

```markdown
## Related
- [[my-api--websocket-memory-leak]] — original bug that inspired this pattern
- [[chat-service--connection-manager]] — implementation in a different project
```

These cross-project links are especially valuable in Obsidian's graph view — they show how knowledge flows between codebases.

---

## Maps of Content (MOCs)

MOCs are hub notes that link to all notes in a domain. They provide a narrative overview rather than the flat index of MANIFEST.

### When to Use MOCs

- When a domain has 10+ notes and the MANIFEST section feels crowded
- When you want to tell a story about how a system evolved (not just list facts)
- When onboarding someone to a complex area of the codebase

### MOC Template

```markdown
---
type: pattern
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: moc, authentication
---

# Authentication System — Map of Content

## Overview
Our auth system uses JWT tokens with refresh rotation. This MOC links to all
related decisions, investigations, and patterns.

## How It Evolved
1. Started with session-based auth — [[auth-session-based-original]]
2. Migrated to JWT — [[auth-jwt-choice]] (decision)
3. Added refresh token rotation — [[auth-refresh-rotation]] (decision)
4. Fixed token expiry bug — [[auth-token-expiry-race-condition]] (investigation)

## Key Patterns
- [[auth-middleware-pattern]] — how auth is enforced in route handlers
- [[auth-testing-pattern]] — how to mock auth in tests

## Known Issues
- [[auth-token-size-growing]] — JWT payload is getting large, monitor this

## Related Domains
- [[moc-api-gateway]] — auth happens at the gateway level
- [[moc-database]] — user sessions stored in PostgreSQL
```

### MOC Placement

Store MOCs in `_ai/Projects/` alongside project notes. Prefix the slug with `moc-`:
- `moc-authentication.md`
- `moc-deployment-pipeline.md`
- `moc-database-layer.md`

Add MOCs to MANIFEST under a `## Maps of Content` section.

---

## Scaling Beyond 100 Notes

### Split MANIFEST

When MANIFEST.md exceeds ~100 entries:

1. Create category manifest files:
   - `{vault}/_ai/MANIFEST-decisions.md` — full decision index
   - `{vault}/_ai/MANIFEST-investigations.md` — full investigation index
   - `{vault}/_ai/MANIFEST-patterns.md` — full pattern index

2. Keep `_ai/MANIFEST.md` as the overview with:
   - The 10 most recent entries per category
   - Links to the full category manifests
   - Total counts per category

3. Update the read protocol: read main MANIFEST first, then the relevant category manifest if needed.

### Archiving Old Notes

When notes accumulate:

1. Notes with `status: deprecated` for 90+ days: move to `_ai/archive/` folder
2. Remove archived entries from MANIFEST (they're still searchable via Grep)
3. Keep the `_ai/archive/` folder for historical reference but never read it at session start

### Archive MANIFEST Entry

When archiving, add a comment to MANIFEST:
```markdown
## Archived
<!-- N notes archived. Search _ai/archive/ if needed. Last archive: YYYY-MM-DD -->
```

---

## Search Strategies

The read protocol uses a cascading search strategy. Here's the full cascade with examples:

### Level 1: MANIFEST Scan (cheapest)
Read MANIFEST.md and match entries by slug, project, or summary keywords. This is the default path.

### Level 2: Tag-Based Grep (targeted)
When MANIFEST doesn't surface enough results, search note frontmatter by tags:
```
Grep: pattern "^tags:.*authentication" path "{vault}/_ai/"
```
This finds notes tagged with `authentication` regardless of their slug or summary text. Tags are curated semantic labels — they bridge the vocabulary gap between how knowledge was stored and how it's being searched for.

### Level 3: Synonym Expansion (creative)
Generate 2-3 alternate terms and Grep MANIFEST for each:
- Searching for "auth"? Also try: `authentication`, `login`, `token`, `session`
- Searching for "perf"? Also try: `performance`, `latency`, `throughput`, `slow`
- Searching for "deploy"? Also try: `deployment`, `release`, `ci-cd`, `pipeline`

### Level 4: Full-Text Grep (expensive)
Search all note content — use only when Levels 1-3 fail:
```
Grep: pattern "connection pool" path "{vault}/_ai/"
```

### Level 5: Related-Section Crawl (discovery)
When you find one relevant note, read its `## Related` section. Follow links to discover the topic cluster. This is especially powerful for cross-project knowledge.

### Search Cost Rule
Always start at Level 1 and escalate only as needed. Most searches should resolve at Level 1 or 2. If you're frequently reaching Level 4, that's a signal that notes need better tags.

---

## MCP-Enhanced Workflows

If MCP tools are available (e.g., from obsidian-mcp-server), the agent can use them opportunistically:

### Search Enhancement
Instead of Grep fallback, use the MCP server's search endpoint for better relevance ranking:
```
obsidian_global_search("authentication token expiry")
```

### Metadata Operations
Use MCP tools for frontmatter operations instead of parsing YAML manually:
```
obsidian_manage_frontmatter(file, "set", { status: "deprecated", updated: "2026-03-24" })
```

### Tag Management
Use MCP tag tools for bulk operations:
```
obsidian_manage_tags(file, "add", ["auth", "security"])
```

### Important
MCP tools are an **optimization**, not a requirement. The skill works fully with filesystem tools alone. If MCP tools are available, prefer them for search and metadata operations. If not, fall back to Read/Write/Grep.

---

## Dataview-Compatible Extensions

For users who view their `_ai/` folder in Obsidian with the Dataview plugin:

### Frontmatter Adjustments

To make notes fully Dataview-queryable, use YAML arrays for tags instead of comma strings:

```yaml
tags:
  - auth
  - security
  - jwt
```

This allows Dataview queries like:
```dataview
TABLE status, updated
FROM "_ai"
WHERE contains(tags, "auth") AND status = "active"
SORT updated DESC
```

### Useful Dataview Queries

**Active decisions by recency:**
```dataview
TABLE status, updated, tags
FROM "_ai"
WHERE type = "decision" AND status = "active"
SORT updated DESC
```

**Unresolved investigations:**
```dataview
LIST
FROM "_ai"
WHERE type = "investigation" AND status = "active"
SORT created DESC
```

**Knowledge graph statistics:**
```dataview
TABLE length(rows) as "Count"
FROM "_ai"
GROUP BY type
```

### Note
The AI agent does not execute Dataview queries — these are for human users browsing the vault in Obsidian. The agent uses MANIFEST and Grep for its own retrieval.

---

## Pruning Stale Notes

### Indicators of Staleness

- `updated` date is more than 90 days old and the related code has changed significantly
- A `decision` note refers to a library or approach that's been replaced
- An `investigation` note describes a bug in code that's been rewritten
- A `pattern` note describes a convention that's no longer followed

### Pruning Protocol

1. Read the note and check if it's still accurate against the current codebase
2. If still accurate: bump `updated` to today
3. If partially outdated: update the content, bump `updated`
4. If fully outdated: set `status: deprecated`, add a note at the top: `> Deprecated: {reason}. See [[replacement-note]] if applicable.`
5. Update MANIFEST to reflect the new status

### Staleness Heuristics

The read protocol's Step 4.5 performs opportunistic staleness checks on notes you're already reading. Here are the heuristics in detail:

| Heuristic | Trigger | Action |
|-----------|---------|--------|
| **Age check** | `updated` > 90 days AND `status: active` | Flag to user — may need refresh |
| **File reference** | Note names a file/function that no longer exists or has been heavily refactored | Flag to user — likely outdated |
| **Contradiction** | Note's claims conflict with current codebase state | Flag to user — needs update or deprecation |
| **Confidence** | Note has `confidence: low` | Apply extra scrutiny; verify before acting on it |
| **Revisit triggers** | A condition listed in `## Revisit Triggers` has been met | Flag to user — the note itself predicted this |

These checks are **opportunistic** — only applied to notes you're already reading, never as a full vault scan.

### When to Prune

- When you encounter a stale note during the read protocol (Step 4.5 flags it)
- When the user asks about a topic and you find conflicting information
- At the user's request (e.g., "clean up the knowledge graph")
- Do NOT proactively scan for stale notes every session — that wastes tokens

---

## Filename Slugification Rules

Deterministic slugs ensure the same concept always produces the same filename:

1. Lowercase everything
2. Replace spaces and underscores with hyphens
3. Remove all characters except `a-z`, `0-9`, `-`
4. Collapse consecutive hyphens into one
5. Trim leading/trailing hyphens
6. Max length: 60 characters (truncate at last complete word)

### Examples

| Input | Slug |
|-------|------|
| "We chose JWT for authentication" | `chose-jwt-for-authentication` |
| "BUG: Memory leak in WebSocket handler" | `memory-leak-in-websocket-handler` |
| "React useMemo() pitfall with objects" | `react-usememo-pitfall-with-objects` |
| "PostgreSQL connection pool sizing (prod)" | `postgresql-connection-pool-sizing-prod` |
