# Example: Initializing a Knowledge Graph

This example shows the vault discovery flow when an agent first sets up a knowledge graph.

---

## Scenario

A developer opens Claude Code in `~/Repos/my-api/`. The agent has no saved vault path.

---

## Agent Behavior

### Step 1: Check Memory

The agent checks for a previously saved vault path. None found.

### Step 2: Ask the User

```
Agent: I'd like to use an Obsidian vault as a persistent knowledge graph across
your coding sessions. Which vault should I use?

- Give me the path to an existing vault (e.g., ~/Obsidian/my-vault)
- Or say "create new" and I'll help you set one up
```

```
User: ~/Obsidian/claude-vault
```

### Step 3: Validate

```
> Glob: /Users/me/Obsidian/claude-vault/.obsidian
> Result: Found — this is a valid Obsidian vault
```

### Step 4: Create Scaffold

The agent checks for `_ai/` inside the vault:

```
> Glob: /Users/me/Obsidian/claude-vault/_ai/MANIFEST.md
> Result: No matches found — need to create scaffold
```

```
mkdir -p /Users/me/Obsidian/claude-vault/_ai/notes
```

**Created: `/Users/me/Obsidian/claude-vault/_ai/MANIFEST.md`**

```markdown
# Knowledge Graph
Last updated: 2026-03-24 | Total notes: 1

<!--
  This file is your AI agent's memory index.
  The agent reads this at the start of every session to recall past knowledge.
  Notes are stored in _ai/notes/ and prefixed with the project name.
  Format: - [[project--slug]] | status | project | date | brief summary
-->

## Decisions
- [[my-api--knowledge-graph-initialized]] | active | my-api | 2026-03-24 | AI knowledge graph set up in this vault

## Investigations

## Patterns
```

**Created: `/Users/me/Obsidian/claude-vault/_ai/notes/my-api--knowledge-graph-initialized.md`**

```markdown
---
type: decision
status: active
created: 2026-03-24
updated: 2026-03-24
project: my-api
tags: meta, knowledge-graph
---

# Initialized Knowledge Graph

## Context
This Obsidian vault now has an AI-managed knowledge graph in `_ai/`. The agent
uses this as persistent memory across all projects and coding sessions.

## Decision
Using a central Obsidian vault with a flat `_ai/notes/` folder and MANIFEST.md
index. Notes are prefixed with the project name (e.g., `my-api--auth-choice.md`)
and use YAML frontmatter for metadata and wikilinks for connections.

## Consequences
- The agent reads MANIFEST.md at session start for context
- New knowledge is captured as individual notes, tagged by project
- Notes link to each other via wikilinks in a Related section
- Cross-project knowledge is discoverable through the shared MANIFEST

## Related
```

### Step 5: Save and Confirm

The agent saves the vault path to memory:
```
Vault path: ~/Obsidian/claude-vault
Configured: 2026-03-24
```

```
Agent: Knowledge graph initialized in your Obsidian vault at ~/Obsidian/claude-vault.

I created `_ai/MANIFEST.md` (the index I'll read every session) and `_ai/notes/`
(where knowledge notes live). Your existing vault notes are untouched — I only
write inside `_ai/`.

From now on, when I learn something worth remembering — architecture decisions,
bug root causes, codebase patterns — I'll capture it here. This works across
all your projects.
```

---

## What If the User Doesn't Have Obsidian?

```
User: create new
```

```
Agent: Let me check if Obsidian is installed...
```

```
> Bash: ls /Applications/Obsidian.app 2>/dev/null
> Result: No such file or directory
```

```
Agent: Obsidian isn't installed yet. Here's how to get started:

1. Download Obsidian from https://obsidian.md (it's free)
2. Install and open it
3. Create a new vault — give it a name like "ai-knowledge" or "dev-brain"
4. Come back and tell me the vault path

Obsidian stores your vault as a regular folder of markdown files — I'll be
able to read and write to it directly.
```

---

## Result

After initialization, the vault looks like:

```
~/Obsidian/claude-vault/
  .obsidian/                             ← Obsidian's config (untouched)
  Decisions/                             ← User's existing folders (untouched)
  Projects/
  Research/
  _ai/                                   ← Agent's namespace
    MANIFEST.md
    notes/
      my-api--knowledge-graph-initialized.md
```

The agent's files appear in Obsidian's file explorer, graph view, and search — fully integrated with the vault but cleanly separated in their own folder.
