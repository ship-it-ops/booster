---
name: obsidian-knowledge-graph
description: >
  Manage an AI-powered knowledge graph in an Obsidian vault. Captures architecture
  decisions, bug investigations, and codebase patterns as persistent memory across
  coding sessions. Use when recalling past decisions, documenting learnings, building
  project memory, or working with an Obsidian-based knowledge base. Activates
  when the agent knows the user's Obsidian vault path.
allowed-tools: Read, Write, Glob, Grep, Bash(mkdir -p *)
---

## Purpose

You are an AI agent with a persistent knowledge graph stored in the user's Obsidian vault. Instead of losing context between sessions, you read from and write to an `_ai/` namespace inside a **central Obsidian vault** that serves as your long-term memory across all projects.

You capture architecture decisions, bug investigations, and codebase patterns as linked markdown notes. Each session, you consult your knowledge graph first and contribute back to it — making every future session smarter.

The vault is a single, central location (e.g., `~/Obsidian/my-vault/`), not a per-repo folder. All projects share the same knowledge graph, with notes tagged by project name. This lets you discover cross-project patterns and reuse knowledge across codebases.

---

## Vault Discovery

Before you can read or write knowledge, you need the path to the user's Obsidian vault.

### Step 1: Check if You Already Know the Vault Path

Check your memory or conversation context for a previously saved vault path. If you have one, verify it still exists:

```
Glob: {vault_path}/.obsidian
```

If the path exists and contains `.obsidian/`, you're good — proceed to the Read Protocol.

### Step 2: Ask the User

If you don't have a vault path, ask:

> "I'd like to use an Obsidian vault as a persistent knowledge graph across your coding sessions. Which vault should I use?
>
> - Give me the path to an existing vault (e.g., `~/Obsidian/my-vault`)
> - Or say **'create new'** and I'll help you set one up"

### Step 3: Handle the Response

**If the user provides a path:**
1. Expand `~` to the home directory
2. Verify `.obsidian/` exists inside it (confirms it's a real Obsidian vault)
3. If valid: save the vault path to your memory for future sessions
4. Create the `_ai/` scaffold if it doesn't exist (see Scaffold Creation below)

**If the user says "create new":**
1. Check if Obsidian is installed (look for `/Applications/Obsidian.app` on macOS, or ask the user)
2. If not installed: tell the user to install Obsidian from https://obsidian.md, then come back
3. If installed: guide them — "Open Obsidian, create a new vault (e.g., `ai-knowledge`), then tell me the path"
4. Once they provide the path, validate and scaffold as above

**If the user doesn't want to use Obsidian:**
- This skill does not activate. Stop here. Do not ask again in this session.

### Step 4: Save to Memory

Save the vault path so future sessions don't need to ask again. Use whatever memory/persistence mechanism is available (Claude Code memory, config file, etc.). The key information to persist:

- **Vault path**: The absolute path to the Obsidian vault
- **Date configured**: When this was set up

---

## Scaffold Creation

When setting up `_ai/` in the vault for the first time:

```
{vault}/_ai/
  MANIFEST.md       — the index you read first, every session
  notes/            — flat folder for all knowledge notes (across all projects)
```

Create `{vault}/_ai/MANIFEST.md` with this starter content:

```markdown
# Knowledge Graph
Last updated: {TODAY} | Total notes: 0

<!--
  This file is your AI agent's memory index.
  The agent reads this at the start of every session to recall past knowledge.
  Notes are stored in _ai/notes/ and prefixed with the project name.
  Format: - [[project--slug]] | status | importance | project | date | brief summary
-->

## Decisions
<!-- Architecture, library, and configuration choices -->

## Investigations
<!-- Bug hunts, debugging sessions, root cause analyses -->

## Patterns
<!-- Codebase conventions, idioms, recurring approaches -->

## Conventions
<!-- Workflow preferences, user expectations, cross-session rules -->
```

Create a seed note at `{vault}/_ai/notes/{project}--knowledge-graph-initialized.md` (where `{project}` is derived from the current working directory basename):

```markdown
---
type: decision
status: active
created: {TODAY}
updated: {TODAY}
project: {project}
tags: meta, knowledge-graph
---

# Initialized Knowledge Graph

## Context
This Obsidian vault now has an AI-managed knowledge graph in `_ai/`. The agent
uses this as persistent memory across all projects and coding sessions.

## Decision
Using a central Obsidian vault with a flat `_ai/notes/` folder and MANIFEST.md
index. Notes are prefixed with the project name (e.g., `booster--auth-choice.md`)
and use YAML frontmatter for metadata and wikilinks for connections.

## Consequences
- The agent reads MANIFEST.md at session start for context
- New knowledge is captured as individual notes, tagged by project
- Notes link to each other via `[[wikilinks]]` in a `## Related` section
- Cross-project knowledge is discoverable through the shared MANIFEST

## Related
```

Add the seed note to MANIFEST.md under Decisions:
```
- [[{project}--knowledge-graph-initialized]] | active | standard | {project} | {TODAY} | AI knowledge graph set up in this vault
```

---

## Project Identification

Derive the current project name from the working directory:
- Use the basename of the current working directory (e.g., `/Users/me/Repos/booster` → `booster`)
- Use this as the project prefix for note filenames and the `project` frontmatter field
- If the working directory is the vault itself, use `general` as the project name

### Project Aliases

When a project directory is renamed, existing notes with the old prefix become disconnected. Instead of migrating note filenames (which would break wikilinks), use a lightweight alias registry.

**File**: `{vault}/_ai/PROJECT-ALIASES.md` (created on-demand, not at scaffold time)

```markdown
# Project Aliases
<!-- Maps current directory basenames to canonical project names used in notes -->
| Current Directory | Canonical Project Name | Since |
|---|---|---|
| booster-v2 | booster | 2026-04-01 |
| my-app-rewrite | my-app | 2026-03-15 |
```

**Resolution order**:
1. Get the current working directory basename
2. Check `PROJECT-ALIASES.md` — if an alias exists, use the canonical name
3. If no alias, use the basename directly

**When to create an alias**: At session start, if the derived project name has **zero** MANIFEST entries BUT similar-prefixed notes exist (e.g., working in `booster-v2` but MANIFEST has `booster--*` entries), ask the user:

> "I see notes for 'booster' but you're in 'booster-v2'. Is this the same project? Should I treat them as the same?"

If yes, create `PROJECT-ALIASES.md` (or append to it) with the mapping. Notes keep their original prefix — **no migration needed**.

---

## Read Protocol

When you need context from past sessions, follow this order:

### Step 1: Resolve Vault Path
Get the vault path from memory. Verify it exists.

### Step 1.5: Resolve Project Name
Get the working directory basename, then check `{vault}/_ai/PROJECT-ALIASES.md` (if it exists) for an alias mapping. Use the resolved canonical project name for all subsequent filtering.

### Step 2: Read MANIFEST
Read `{vault}/_ai/MANIFEST.md`. Scan for entries relevant to your current task. Each entry has a slug, status, importance, project, date, and summary.

**Filtering**: Use the resolved project name (after alias lookup). Prioritize `core` importance entries for the current project — always read these for context. Then scan `standard` entries for task-specific matches. Skip `minor` entries unless you're searching for a niche topic. Also scan other projects — a pattern discovered in project A might be exactly what project B needs.

### Step 2.5: Conceptual Search
If MANIFEST scanning yields fewer than 2 relevant matches for a task that likely has prior knowledge, expand your search before falling back to brute-force Grep:

1. **Tag scan**: Grep `{vault}/_ai/notes/` for frontmatter tags related to your concept. Use `Grep` with pattern `^tags:.*{concept-keyword}` on path `{vault}/_ai/notes/`. Tags are curated concept labels — they catch what slugs miss.
2. **Synonym expansion**: Think of 2-3 alternate terms for the concept (e.g., "auth" / "authentication" / "login" / "token"), then Grep the MANIFEST for each. LLMs are good at synonyms — use that strength.
3. **Related-section crawl**: If you found at least one relevant note, read its `## Related` section and follow those links. Related notes cluster around topics — one hit often leads to the full cluster.

### Step 3: Read Targeted Notes
Open only the 1-3 notes most relevant to the current task. Read them fully — they contain the detailed context, rationale, and links to related notes.

### Step 4: Follow Links (if needed)
If a note's `## Related` section points to other relevant notes, read those too. Stay focused — follow at most one hop of links.

### Step 4.5: Staleness Spot-Check
After reading relevant notes, quickly check for staleness on the notes you just read (NOT a full vault scan):

1. Is the `updated` date older than **90 days** AND the note is `status: active`?
2. Does the note reference specific **files, functions, or libraries** that you know have changed?
3. Does the note **contradict** what you observe in the current codebase?

If any note fails these checks, flag it to the user:

> "Note [[project--slug]] was last updated N months ago and references X which has changed. Want me to update or deprecate it?"

This is **opportunistic**, not exhaustive. Only check notes you're already reading — never scan the full vault for staleness. Also treat notes with `confidence: low` with extra scrutiny.

### Step 5: Search Fallback
If MANIFEST doesn't surface what you need, use Grep to search `{vault}/_ai/notes/` for keywords. This is the expensive path — use it only when the index fails.

### Rules
- **NEVER** glob-read all notes in `_ai/notes/`. That wastes tokens and context.
- **ALWAYS** check `status` before trusting a note. Skip `deprecated` notes. Flag `superseded` notes and check what replaced them.
- **PREFER** the MANIFEST path (Steps 2-3) over search (Step 5). The MANIFEST is curated; search is brute-force.
- **CROSS-PROJECT**: When you find a note from another project that's relevant, mention it to the user — they may not know that knowledge exists.

---

## Write Protocol

**Write incrementally, not just at the end.** After each significant milestone during a session — not just when all work is done — evaluate whether something was learned that's worth persisting. Apply the **re-discovery threshold**: only write knowledge that would take more than 5 minutes to re-derive from scratch. If you wait until the session ends, you risk losing knowledge if the session is interrupted or context is compressed.

### What to Write
- Architecture or configuration decisions and their rationale
- Bug root causes, especially non-obvious ones
- Codebase patterns and conventions you discovered
- Gotchas, edge cases, or API quirks that surprised you
- Environment setup steps that weren't documented
- User workflow preferences and rules that affect how agents should behave (e.g., commit style, tool preferences, review expectations)

### What NOT to Write
- Routine code changes (the git log captures those)
- Obvious facts derivable from reading the code
- Temporary state or in-progress work
- Task lists or to-do items (use a task tracker)

### 5-Step Write Flow

**Step 1 — Search MANIFEST**: Before creating a note, scan MANIFEST.md for existing notes on this topic. Check if there's already a note with a similar slug or summary, in this project or any project.

**Step 2 — Decide Update vs. Create**:
- **Same topic, same project, exists and is `active`**: Update the existing note. Edit its content, bump `updated` date.
- **Same topic, same project, exists but is `deprecated`**: Create a new note. Set the old note's status to `superseded`. Add a link between them.
- **Same topic, different project**: Create a new project-specific note, but link to the existing one in `## Related`. Consider whether the existing note should be generalized.
- **No match found**: Create a new note.

**Step 3 — Write/Update the Note**: Use the appropriate template (see Note Types below). Use a deterministic project-prefixed slug:

```
{project}--{topic-slug}.md
```

- `{project}` — current project name (from working directory basename)
- `--` — double-hyphen separator between project and topic
- `{topic-slug}` — lowercase, hyphens for spaces, no special characters

Examples:
- `booster--auth-jwt-choice.md`
- `ship-code--postgres-connection-pool.md`
- `my-api--react-memo-pitfall.md`

Write the file to `{vault}/_ai/notes/{project}--{topic-slug}.md`.

**Revisit Triggers (recommended for `decision` and `pattern` types)**: Add a `## Revisit Triggers` section listing concrete conditions under which the note should be re-evaluated. This helps the staleness spot-check (Step 4.5) by making expiry conditions explicit rather than relying on date heuristics alone. Example: "If we upgrade from Node 20 to 22", "If connection count exceeds 1000 concurrent".

**Tag Quality Rule**: Tags are your semantic search index. Choose tags that a future searcher would use as query terms, not just descriptive labels. Include:
- The **primary concept** (e.g., `authentication`, `caching`, `deployment`)
- The **technology** involved (e.g., `jwt`, `postgres`, `docker`)
- A **cross-cutting concern** if applicable (e.g., `performance`, `security`, `reliability`)
- Aim for **3-5 tags** per note. Too few = invisible to search; too many = noise. Reuse existing tags from other notes when applicable — check recent MANIFEST entries for consistency.

**Step 4 — Update MANIFEST**: Add or update the entry in the appropriate section of `{vault}/_ai/MANIFEST.md`. Use the format:
```
- [[{project}--{topic-slug}]] | status | importance | project | YYYY-MM-DD | 8-word summary
```
Bump the "Last updated" date and "Total notes" count.

**Step 5 — Add Links**: In the new note's `## Related` section, add 3-5 wikilinks to related notes (if any exist). Use short links: `[[project--slug]]`. Cross-project links are encouraged — they're one of the main benefits of a central vault.

---

## Note Types & Templates

### Decision
For architecture, library, configuration, or process choices.

```markdown
---
type: decision
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
project: {project}
tags: relevant, topic, tags
---

# {Descriptive Title}

## Context
What situation or problem prompted this decision?

## Decision
What was decided and why?

## Consequences
What are the trade-offs? What does this enable or prevent?

## Related
- [[project--related-note]] — why it's related
```

### Investigation
For bug hunts, debugging sessions, and root cause analyses.

```markdown
---
type: investigation
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
project: {project}
tags: relevant, topic, tags
---

# {Bug or Issue Title}

## Symptoms
What was observed? Error messages, unexpected behavior, failing tests?

## Root Cause
What was actually wrong? Be specific — file, line, mechanism.

## Fix
What was the solution? Include key code changes or config adjustments.

## Prevention
How to avoid this in the future? What to watch for?

## Related
- [[project--related-note]] — why it's related
```

### Pattern
For codebase conventions, recurring approaches, and idioms.

```markdown
---
type: pattern
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
project: {project}
tags: relevant, topic, tags
---

# {Pattern Name}

## When to Use
What situations call for this pattern?

## Implementation
How is it implemented in this codebase? Key files, functions, conventions.

## Examples
Brief code snippets or references showing the pattern in action.

## Gotchas
Common mistakes or edge cases when applying this pattern.

## Related
- [[project--related-note]] — why it's related
```

### Convention
For workflow preferences, user expectations, and cross-session rules that aren't architecture decisions but need to persist across all agent instances.

```markdown
---
type: convention
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
project: {project}
tags: relevant, topic, tags
---

# {Convention Name}

## Rule
What must always (or never) be done?

## Why
What prompted this convention? What goes wrong without it?

## Scope
Does this apply to one project, all projects, or a specific context?

## Related
- [[project--related-note]] — why it's related
```

### Onboarding & Runbook (team mode)

Two additional types for teams. Use the same frontmatter as above with `type: onboarding` or `type: runbook`.

- **Onboarding**: Sections — Overview, Key Components, Getting Started, Related
- **Runbook**: Sections — When to Use, Steps, Rollback, Related

See reference.md for full templates.

---

## MANIFEST.md Format

The MANIFEST is a compact index — one line per note, organized by category. It is the **only** file you read at session start.

### Entry Format
```
- [[project--slug]] | status | importance | project | YYYY-MM-DD | 8-word-max summary
```

**Backwards compatibility**: Older entries with 4 pipe-separated fields (no importance) are treated as `standard` importance.

### Category Sections
Group entries under `## Decisions`, `## Investigations`, `## Patterns`, `## Conventions`. Add `## Onboarding` and `## Runbooks` sections when those note types are used.

### Header
```markdown
# Knowledge Graph
Last updated: YYYY-MM-DD | Total notes: N
```

### Scaling
When the MANIFEST exceeds ~100 entries, split into:
- `MANIFEST.md` — overview with all `core` entries plus the 10 most recent `standard` entries per category, plus links to category manifests. `minor` entries only appear in category manifests.
- `{vault}/_ai/MANIFEST-decisions.md` — full decision index
- `{vault}/_ai/MANIFEST-investigations.md` — full investigation index
- `{vault}/_ai/MANIFEST-patterns.md` — full pattern index

The main MANIFEST always remains the entry point.

---

## Frontmatter Schema

### Required Fields (all note types)
```yaml
type: decision | investigation | pattern | convention | onboarding | runbook
status: active | deprecated | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
project: project-name
tags: comma, separated, values
```

### Optional Fields
```yaml
importance: core | standard | minor   # defaults to standard if omitted
confidence: high | medium | low       # defaults to medium if omitted
```

- **`importance`** — How critical this knowledge is:
  - `core` (~10-15% of notes): Foundational decisions, critical patterns, severe bug root causes. Things that would cause real damage if forgotten.
  - `standard`: Default. Normal knowledge worth persisting. Most notes are this.
  - `minor`: Small gotchas, environment quirks, one-off fixes. Worth recording but low priority for session-start context loading.
- **`confidence`** — How reliable the knowledge is:
  - `high`: Well-verified, stable knowledge confirmed by testing or production use.
  - `medium`: Default. Reasonably confident but not battle-tested.
  - `low`: Speculative, based on incomplete investigation, or likely to become stale quickly. Treat with extra scrutiny during reads.

### Rules
- Keep frontmatter **flat** — no nested YAML objects or arrays of objects
- `tags` is a comma-separated string, not a YAML array (saves tokens)
- `project` is the working directory basename where the knowledge was captured
- `status` must always be set. When deprecating, change status and add a note explaining why
- Dates use ISO 8601 format: `YYYY-MM-DD`
- Relationship links go in the `## Related` body section as wikilinks, not in frontmatter

---

## Linking Strategy

### When to Link
Create a wikilink when there is a **causal, dependency, or "you'll need this too"** relationship. Do not link just because two notes mention the same word.

### Cross-Project Links
One of the key benefits of a central vault. If you discover that `booster--auth-middleware.md` is relevant to `ship-code--api-security.md`, link them. This surfaces connections the user might not see otherwise.

### Where to Put Links
Every note has a `## Related` section at the bottom. Place 3-5 wikilinks there, each with a brief reason:
```markdown
## Related
- [[booster--auth-jwt-choice]] — same auth system, related token handling
- [[ship-code--error-handling]] — similar error handling pattern used here
```

### Link Format
Use short links: `[[project--slug]]`. Never use full filesystem paths.

### Tag Conventions
Tags serve as a lightweight categorization layer that complements the type-based MANIFEST sections. They are also the primary input for conceptual search (Step 2.5). Follow these conventions:

- Use **domain tags** for the problem area: `authentication`, `database`, `deployment`, `testing`
- Use **technology tags** for specific tools: `jwt`, `postgres`, `docker`, `react`
- Use **cross-cutting tags** for concerns: `performance`, `security`, `dx`, `reliability`
- Keep tags **lowercase**, single-word or hyphenated
- **Reuse** existing tags from other notes when applicable — consistency makes search work

---

## Naming Convention

Note filenames are deterministic project-prefixed slugs:

```
{project}--{topic-slug}.md
```

Topic slug rules: lowercase, hyphens for spaces, no special characters, max 60 characters for the topic portion.

| Project | Topic | Filename |
|---------|-------|----------|
| booster | "We chose JWT for auth" | `booster--auth-jwt-choice.md` |
| my-api | "Memory leak in WebSocket handler" | `my-api--websocket-memory-leak.md` |
| ship-code | "How we handle errors" | `ship-code--error-handling-convention.md` |

The project-prefixed slug is a pseudo-primary key. If you want to write about JWT auth in the booster project and `booster--auth-jwt-choice.md` already exists, **update it** instead of creating a second note.

---

## Multi-Instance Mode

When multiple Claude instances may write to the vault simultaneously (e.g., in different terminal tabs or IDE windows), use ledger-based writes to avoid MANIFEST conflicts. Note files themselves are safe because each has a unique slug-based filename — the only contention point is MANIFEST.md.

### Activation
Use this mode when the user has told you they run multiple Claude instances, or when you detect `{vault}/_ai/ledger/` already exists. Otherwise, direct MANIFEST writes are simpler and preferred.

### Write Path (replaces direct MANIFEST edit in Step 4 of Write Protocol)
1. Generate a session ID: `{project}-{HHMMSS}` (e.g., `booster-143022`)
2. Create the ledger directory if needed: `mkdir -p {vault}/_ai/ledger`
3. Write the MANIFEST entry to `{vault}/_ai/ledger/{session-id}.md` instead of editing MANIFEST.md directly:
   ```markdown
   # Session Ledger: {session-id}
   Created: {YYYY-MM-DD HH:MM}

   ## Entries
   - [[project--slug]] | status | importance | project | YYYY-MM-DD | summary
   ```
4. Write the note file to `_ai/notes/` as normal (unique filenames = no conflict)

### Merge Path (at session start, after reading MANIFEST)
1. `Glob: {vault}/_ai/ledger/*.md`
2. If ledger files exist, read each one
3. For each entry in a ledger: add it to the appropriate section of MANIFEST.md if not already present
4. Delete the ledger files after successful merge
5. Bump the MANIFEST "Last updated" date and "Total notes" count

### Conflict Resolution
- If two ledgers have entries for the **same note slug**: keep the one with the later date
- If MANIFEST already has the entry: skip (merge is idempotent)

---

## What This Is NOT

This knowledge graph is:

- **Not a database.** You cannot query, filter, sort, or aggregate programmatically. If you need that, use SQLite or a proper database.
- **Not a task tracker.** Do not store to-do items, sprint backlogs, or issue tickets here.
- **Not a replacement for documentation.** Public-facing docs, READMEs, and API references belong in their proper locations.
- **Not a replacement for code comments.** If knowledge is specific to a single file, put it in that file.
- **Limited concurrency.** Multi-instance mode uses per-session ledger files to avoid write conflicts on MANIFEST. Note files are safe because they have unique names. For full concurrent safety with locking, use an MCP server.
- **Not unlimited.** Designed for ~200-500 AI-managed notes. Beyond that, split MANIFEST into category files.

The agent writes **ONLY** to `{vault}/_ai/`. Never modify files outside the `_ai/` namespace. The rest of the vault is the user's personal space.

---

## Companion Tools

This skill teaches **strategy** — what to remember and how to organize it. It pairs well with:

- **[kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)** — Teaches Obsidian-flavored markdown syntax (wikilinks, callouts, properties, Canvas). Recommended companion. Not required.
- **MCP servers** (cyanheads/obsidian-mcp-server, aaronsb/obsidian-mcp-plugin) — Provide structured API access to Obsidian vaults. Optional enhancement for better search and scaling.
- **Obsidian plugins** (Dataview, Templater) — Power user extensions. See reference.md for details.

---

## Session Lifecycle

### Start of Session
1. Resolve vault path (from memory or ask the user)
2. Resolve project name (check aliases if `PROJECT-ALIASES.md` exists)
3. Merge any pending ledger files in `{vault}/_ai/ledger/` (multi-instance mode)
4. Read `{vault}/_ai/MANIFEST.md` to load context
5. Note entries relevant to the current project and likely task

### During Work
6. When you encounter a past decision, bug, or pattern — check if it's already captured
7. Reference captured knowledge in your responses when relevant
8. Surface cross-project knowledge when it helps the current task
9. Flag stale notes opportunistically (Step 4.5) when you read them
10. **Write incrementally**: After each significant milestone (a decision made, a bug root-caused, a preference stated), capture the knowledge immediately — don't defer to end-of-session

### End of Session
11. Review: did you miss anything worth persisting? Check for uncaptured decisions, conventions, or discoveries.
12. If yes, follow the 5-step write protocol (use ledger path if multi-instance mode is active)
13. If no, move on — not every session produces new knowledge
