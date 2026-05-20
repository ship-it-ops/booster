# ship-agent-context — Reference

Extended patterns beyond the everyday workflow in `SKILL.md`. Read this when you need to scale, run multiple agents in parallel, deepen a template, or integrate with other tools.

---

## Extended Templates

### Decision — extended fields

For decisions that affect multiple systems or carry long-term commitment:

```yaml
---
type: decision
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: claude-session-…
tags: [auth, security]
importance: core
supersedes: prior-slug      # optional, when replacing an earlier decision
adr-id: ADR-007             # optional, when mirrored to a formal ADR
---
```

Optional body sections beyond the base template:

```markdown
## Validation
How the decision was confirmed — benchmarks, prototypes, user feedback.

## Stakeholders
Who needs to agree before this changes (names, roles).

## Cost of Reversal
What it would take to back out. Cheap / moderate / expensive.
```

When the team uses ADRs, mirror the decision into `docs/adr/` and reference the ADR ID in frontmatter. Don't duplicate the body — the ADR is canonical for committed architectural choices; this note holds the agent-side context.

### Investigation — extended fields

For complex multi-day investigations:

```yaml
---
type: investigation
status: active
severity: critical | high | medium | low
time-to-resolution: 6h     # optional
---
```

Optional body sections:

```markdown
## Timeline
- 10:00 — first symptom in staging
- 10:30 — reproduced locally
- 11:15 — narrowed to connection pool
- 12:00 — root cause confirmed
- 14:00 — fix deployed

## Environment
OS, runtime, key config values relevant to the bug.

## Hypotheses Ruled Out
- Hypothesis A — falsified by experiment X.
- Hypothesis B — falsified by reading code at path Y.
```

`Hypotheses Ruled Out` is one of the highest-value sections — it stops future agents from chasing dead ends.

### Plan — extended fields

When a plan spans multiple sessions:

```markdown
## Phases
- Phase 1 — schema migration (done)
- Phase 2 — backfill (in progress, branch: backfill-job)
- Phase 3 — cutover (blocked on Phase 2)

## Decisions Made During Planning
- [decision-slug](../decisions/decision-slug.md)

## Open Questions Raised
- [question-slug](../open-questions/question-slug.md)
```

### Scar — extended fields

```yaml
---
type: scar
status: active
incident-date: YYYY-MM-DD
severity: critical | high | medium
tripwire: "if you see X, stop and check Y"
postmortem: https://link-to-postmortem  # optional
---
```

Optional body sections:

```markdown
## Detection
What signal would have caught this earlier.

## Mitigation Now in Place
Guards added to the codebase or CI that should prevent recurrence.
```

---

## Multi-Instance Mode (ledger writes)

When multiple agents may write to MANIFEST simultaneously (multiple terminal tabs, multiple IDE sessions, multiple humans pairing with agents), direct MANIFEST edits will race. Note files themselves are safe — each has a unique slug — but `MANIFEST.md` is a single contended file.

### Activation

Use ledger writes when:
- The user has told you they run multiple agents concurrently.
- `docs/agent/ledger/` already exists (a prior session enabled it).
- You detect more than one `status/` entry from different agent IDs created within the last hour.

Otherwise, direct MANIFEST writes are simpler and preferred.

### Write path (replaces Step 4 of the Write Protocol)

1. Generate a session ID once per session: `{YYYYMMDD-HHMMSS}-{short-hash}`.
2. Create the ledger directory if missing: `mkdir -p docs/agent/ledger`.
3. Append your MANIFEST entry to `docs/agent/ledger/{session-id}.md`:
   ```markdown
   # Session Ledger: {session-id}
   Created: YYYY-MM-DD HH:MM
   
   ## Entries
   - [slug] | type | status | importance | YYYY-MM-DD | summary
   ```
4. Write the note file to `docs/agent/{folder}/{slug}.md` as normal (unique filenames, no contention).

### Merge path (at session start, right after Step 1)

1. `Glob: docs/agent/ledger/*.md`.
2. For each ledger file, read it and merge its entries into the correct sections of `MANIFEST.md` if not already present.
3. Delete each ledger file after a successful merge.
4. Bump `Last updated` and `Total notes`.

### Conflict resolution

- Two ledgers reference the same slug → keep the one with the later `updated` date.
- Entry already exists in MANIFEST → skip (merge is idempotent).
- Two notes wrote to the same slug → the file system enforces last-writer-wins. Inspect manually if both intended to create distinct content.

---

## Scaling Beyond 100 Notes

### Split the MANIFEST

When `MANIFEST.md` exceeds ~100 entries:

1. Create category manifests:
   - `docs/agent/MANIFEST-decisions.md`
   - `docs/agent/MANIFEST-plans.md`
   - `docs/agent/MANIFEST-investigations.md`
   - `docs/agent/MANIFEST-patterns.md`
   - `docs/agent/MANIFEST-scars.md`

2. Keep `MANIFEST.md` as the entrypoint, containing:
   - All `importance: core` entries across all categories.
   - The 10 most recent `standard` entries per category.
   - Links to the full category manifests.
   - Total counts per category.

3. Update Step 1 of the Read Protocol: read `MANIFEST.md` first; only open the relevant category manifest if you need more.

### Archive cold content

Notes with `status: deprecated` for 90+ days:
1. Move the file from its topical folder to `docs/agent/archive/`.
2. Remove its MANIFEST entry.
3. Add a one-line marker in MANIFEST under `## Archived`:
   ```
   ## Archived
   <!-- N notes archived. Search docs/agent/archive/ if needed. Last archive: YYYY-MM-DD -->
   ```

Never read `archive/` at session start. It exists for Grep fallback and human review only.

### Status entries that age out

Stale `status/` entries are the most common rot. Apply this monthly:
- Any `status/` entry untouched for 14 days → ask the user if the work is still live.
- If completed: move to `archive/` (preserves the work-was-done signal), remove from MANIFEST.
- If abandoned: delete entirely.

---

## Staleness Heuristics

The Read Protocol's normal path doesn't do a full vault scan for stale content — that wastes tokens. Instead, apply opportunistic checks to notes you're already reading:

| Heuristic | Trigger | Action |
|---|---|---|
| **Age** | `updated` > 90 days AND `status: active` | Flag to user — may need refresh |
| **File reference** | Note names a file/function that no longer exists | Flag to user — likely outdated |
| **Contradiction** | Note's claim conflicts with current code | Flag — needs update or deprecation |
| **Revisit trigger met** | A `## Revisit Triggers` condition has become true | Flag — the note predicted this |
| **Open question stale** | `open-question` `active` > 30 days | Ask user if still open |
| **Status stale** | `status` entry untouched > 14 days | Ask user if work is still live |

Apply only to notes you opened during the current session. Never scan the full folder for staleness — that's a separate maintenance task the user must invoke explicitly ("clean up docs/agent/").

### Pruning Protocol

When a stale note is confirmed:
1. Still accurate → bump `updated` to today, no other change.
2. Partially outdated → edit the content, bump `updated`.
3. Fully outdated → set `status: deprecated`, add a top-of-file note (`> Deprecated YYYY-MM-DD: reason`). Link to replacement if any.
4. Update MANIFEST to reflect the new status.

---

## Team Mode

`docs/agent/` is team-shared by default (it's in git). For teams that want a separation between shared knowledge and individual scratch space:

```
docs/agent/
  MANIFEST.md
  decisions/                  ← team-shared
  plans/
  investigations/
  patterns/
  status/
  open-questions/
  scars/
  archive/
  personal/                   ← per-developer scratch space
    alice/
      notes/
    bob/
      notes/
```

The agent should check `git config user.name` (or `whoami`) to determine the right `personal/` subfolder when writing personal scratch notes. These are still in git unless the team adds them to `.gitignore`.

### Review cadence

Periodically — weekly, monthly, or per-sprint:
1. Review all `active` notes whose `updated` is older than 30 days.
2. Walk `open-questions/` and resolve, escalate, or close.
3. Promote valuable `personal/` notes to the shared folders.
4. Apply the Pruning Protocol to any stale notes.

A `/agent-context-review` slash command (or equivalent ritual) is a reasonable team practice.

---

## Search Strategy Cascade

The Read Protocol uses a cheapest-first cascade:

### Level 1 — MANIFEST scan
Read `MANIFEST.md`, match by slug, summary, or tag. Most reads should resolve here.

### Level 2 — Tag grep
```
Grep: pattern "^tags:.*authentication" path docs/agent/
```
Finds notes tagged with a concept regardless of slug. Tags bridge vocabulary gaps.

### Level 3 — Synonym expansion
For ambiguous concepts, try 2–3 alternates:
- `auth` → `authentication`, `login`, `token`, `session`
- `perf` → `performance`, `latency`, `slow`, `throughput`
- `deploy` → `deployment`, `release`, `ci-cd`

Grep MANIFEST for each.

### Level 4 — Full-text grep
```
Grep: pattern "connection pool" path docs/agent/
```
Use only when Levels 1–3 fail. Expensive.

### Level 5 — Related-section crawl
When you find one relevant note, read its `## Related` section. Topic clusters propagate quickly.

If you reach Level 4 often, the symptom is bad tagging — go back and add tags to the notes you eventually find.

---

## Frontmatter Schema — Strict Rules

- Frontmatter must be **flat** — no nested objects, no arrays of objects.
- `tags` must be a YAML array: `tags: [auth, security, jwt]`.
- Dates use ISO 8601: `YYYY-MM-DD`. No times unless the field is named `*-at`.
- `status` is always set. Never leave it implicit.
- Relationship links go in the body's `## Related` section, not in frontmatter.
- Unknown keys are allowed but discouraged — prefer adding sections in the body.

### Importance and confidence

- `importance: core` — foundational. ~10% of notes. Read at session start by default. Examples: a primary architecture decision, the most-bitten scar, the canonical convention for a core subsystem.
- `importance: standard` — default. Read on demand.
- `importance: minor` — small gotchas, environment quirks. Worth recording but not session-start material.
- `confidence: high | medium | low` — optional. Notes with `low` should be treated with extra scrutiny. Defaults to `medium` if omitted.

---

## MCP / Tooling Integration

This skill works with plain filesystem tools (`Read`, `Write`, `Glob`, `Grep`). If MCP servers are available, prefer them for these operations:

- **GitHub MCP** — when a decision references a PR/issue, fetch the canonical link via `mcp__github__pull_request_read` or `issue_read` rather than pasting a URL.
- **Jira/Linear MCPs** — link decisions to tickets via the structured fetch tools; never duplicate ticket bodies into the note.
- **Slack MCP** — when a decision originated in a thread, link to the thread; do not paste the conversation.

MCP usage is optional. The skill must work fully with only filesystem tools.

---

## Pairing with `obsidian-knowledge-graph`

The obsidian skill is **cross-repo**: a central vault that surfaces patterns across projects. This skill is **in-repo**: handoff context committed alongside the code.

Use both when:
- A pattern observed in this repo should also be known to agents working in sibling repos. Capture it here first, then mirror to the obsidian vault as `general--{slug}` for cross-project reuse.
- A cross-project pattern from the obsidian vault becomes relevant here. Link from a local `patterns/` note: `## Related — [obsidian-vault-note](path-in-vault)`.

The two skills are independent. Installing one does not require the other.

---

## Filename Slugification

Deterministic slugs ensure the same concept always produces the same filename:

1. Lowercase everything.
2. Replace spaces and underscores with hyphens.
3. Remove all characters except `a-z`, `0-9`, `-`.
4. Collapse consecutive hyphens.
5. Trim leading/trailing hyphens.
6. Truncate to 60 characters at the last complete word.

### Examples

| Input | Slug |
|---|---|
| "We chose JWT for authentication" | `chose-jwt-for-authentication` |
| "BUG: Memory leak in WebSocket handler" | `memory-leak-in-websocket-handler` |
| "PostgreSQL connection pool sizing (prod)" | `postgresql-connection-pool-sizing-prod` |
| "Plan: phase 2 migration" | `plan-phase-2-migration` |

If the slug already exists in the target folder, that's the signal to **update** the existing note, not create a second one. Slugs are pseudo-primary keys.
