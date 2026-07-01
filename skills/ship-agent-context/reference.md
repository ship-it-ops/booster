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

### Instruction — extended fields

The base `Instruction` template in `SKILL.md` covers the common case. These extra fields handle nuance:

```yaml
---
type: instruction
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: claude-session-…
source: user-instruction
scope: always | when-X | branch:feature/y | until:YYYY-MM-DD
tags: [git, safety]
importance: core | standard
confirmed-on: YYYY-MM-DD          # last time the user re-affirmed this rule
supersedes: prior-slug            # when replacing an earlier instruction
adjacent-rule: agents-md          # set when the instruction echoes an AGENTS.md rule (use the adjacent rule's anchor / heading)
---
```

Optional body sections beyond the base template:

```markdown
## Examples
- Triggered: "About to `git push` after a commit — the agent paused and asked."
- Not triggered: "Squashing local commits before pushing — no remote action yet."

## Exceptions
Cases where the rule does NOT apply (e.g., "documentation-only branches on `docs/*` are exempt").

## Promotion History
- 2026-07-04 — suggested promotion to AGENTS.md; user deferred ("not yet, still trialing").
```

#### Scope grammar

`scope:` is parsed as a small DSL:

| Scope | Meaning | Auto-revoke trigger |
|---|---|---|
| `always` | This repo, every branch, every session, indefinitely | Only on explicit user revocation |
| `when-X` | Active only when context X applies (`when-deploying`, `when-touching-migrations`) | Only on explicit user revocation |
| `branch:NAME` | Active only on the named branch | Branch deleted or merged into main |
| `until:YYYY-MM-DD` | Time-bounded | Date passes — move to archive automatically |

Infer the scope from the user's wording: "on the deploy branch, never force-push" → `branch:deploy`. "Until the freeze ends Friday" → `until:<that-friday-as-iso>`. When ambiguous, default to `always` — the user can always say "actually that was just for the migration branch" later.

#### Confirmed-on

When an active instruction comes up during a session (the agent applied it, the user affirmed it implicitly by accepting the behavior, or the user re-stated it), bump `confirmed-on` to today. This is the signal that distinguishes living rules from forgotten ones. Stale `confirmed-on` (>90 days) is a candidate for asking the user "is this still the rule?"

---

## User-Instruction Capture — Edge Cases

The SKILL.md trigger/anti-trigger lists cover the common cases. These are the harder calls.

### Worked examples — capture or skip?

| User said | Capture? | Why |
|---|---|---|
| "Don't push without asking first." | **Yes** | Indefinite verb + push (recurring action). |
| "Don't push this branch." | **No** | Scope is "this branch" + current task. Capture only as `scope: branch:<current-branch>` if the user explicitly says "from now on this branch". |
| "Never use ESM in this repo." | **Yes** | "Never" + "this repo" = persistent, repo-wide. |
| "Don't use ESM here." | **No** | "Here" most likely refers to the current file or current edit. Momentary correction. |
| "Always run the tests before opening a PR." | **Yes** | "Always" + recurring action. |
| "Run the tests." | **No** | Single imperative for now, no temporal marker. |
| "Remember that we use pnpm." | **Yes**, with one caveat | Capture, then suggest promotion to `AGENTS.md` — "we use pnpm" is the canonical kind of static project rule. |
| "For now, skip the linter." | **No** | "For now" is an anti-trigger. |
| "Ask me before deploying to production." | **Yes** | "Ask before" + deploy = clear standing rule. |
| "Don't refactor this function." | **No** | Scoped to the current function. |
| "Don't ever refactor without tests." | **Yes** | "Don't ever" + general rule about refactoring. |

The shared property of the **Yes** rows: an unbounded scope plus an action class the user expects to recur. The shared property of the **No** rows: scope tied to "here / this / now / this {file,branch,function}" without a temporal marker.

### Overlap with existing instructions

When a trigger fires but `instructions/` already has a file on the same topic:

1. Read the existing file.
2. If the new statement **refines** the existing rule (adds a condition, adds an example, narrows the scope), edit the existing file and bump `updated` and `confirmed-on`.
3. If the new statement **contradicts** the existing rule, do not silently overwrite. Ask: "You have a standing instruction that says X. Now you've said Y. Should I replace, narrow, or revoke the old one?"
4. If the new statement is identical, just bump `confirmed-on`.

### Conflict with AGENTS.md / CLAUDE.md

The conflict-resolution rule in SKILL.md (don't overwrite, surface the conflict, ask which wins) needs nuance for two common shapes:

- **Direct contradiction** — AGENTS.md says "always push immediately after commit"; user says "ask before pushing." Surface explicitly: "AGENTS.md says X, you just said Y — which wins for this repo?" Capture the answer in the instruction's `## Why` and `adjacent-rule:` frontmatter.
- **Refinement** — AGENTS.md says "use pnpm"; user says "use pnpm with `--frozen-lockfile` in CI." No conflict — this is a refinement. Capture the instruction with `adjacent-rule: agents-md-pnpm`, link in `## Related`.

### Promotion to AGENTS.md

When an instruction satisfies all of the following, suggest promotion:

1. Status has been `active` for 30+ days without revocation.
2. The repo has an `AGENTS.md` (or `CLAUDE.md`).
3. The rule is *general* — it would apply to any contributor or any agent, not just the user who set it.

Suggested promotion script (model output, not literal):

> "The instruction at `docs/agent/instructions/run-linter-before-pr.md` has been active for 38 days without revocation. It reads as a general project rule — I'd suggest copying it into `AGENTS.md` under a 'Pre-PR checks' section so it carries the same weight for every contributor. Want me to draft the AGENTS.md change for you to review?"

The skill never edits `AGENTS.md` itself. Drafting a proposed change is fine; committing it requires the user.

### One-per-turn cap — rationale

The cap exists because a single user message can contain several persistent-intent phrases (e.g., "always run tests, never force push, and remember to ask before deploys"). Writing three files silently in one turn would:

- Trigger three filesystem writes the user didn't see coming.
- Make the single-line "saved as…" confirmation grow into a paragraph, which dilutes its safety-net value.
- Create three MANIFEST entries that may want different scopes or importances — better surfaced one at a time.

The cap forces the agent to capture the most explicit/important one silently, then surface the others as one-line "want me to save that too?" offers. The user can accept all of them, but with visibility.

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

Stale `status/` entries are the most common rot. The **primary** defense is the session-start Reconciliation pass in `SKILL.md` ("Reconciliation — Self-Healing Status"): every entry's `## Done when` anchor is verified against ground truth and the demonstrably-complete ones auto-archive — no waiting on an age threshold. The age check below is the **backstop** for entries that survive reconciliation (no checkable anchor, or work genuinely still open but idle):
- Any `status/` entry that reconciliation could not resolve and is untouched for 14 days → ask the user if the work is still live.
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
| **Status unreconciled** | `status` entry whose `## Done when` shows hard evidence of completion (PR merged, branch gone, sha on default branch) | Auto-archive silently (see Reconciliation in SKILL.md) |
| **Status stale** | `status` entry reconciliation couldn't resolve, untouched > 14 days | Ask user if work is still live |

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
