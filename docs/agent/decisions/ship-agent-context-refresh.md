---
type: decision
status: active
created: 2026-10-05
updated: 2026-10-05
summary: "ship-agent-context 1.3 rewrite: digest hook, notes as a colleague's notes, script-checked hand-offs, generated index (C1-C12)"
paths: [skills/ship-agent-context/*, plugins/ship-agent-context/*]
---

# `ship-agent-context` 1.3: the full rewrite, what changed from the earlier design, and why

## Context

Fourth skill in the `ship-*` refresh, done with the same loop as [ship-reviewed-prs-refresh](ship-reviewed-prs-refresh.md): six independent reviewers audited the existing skill, the existing skill was run in three scratch repositories and judged independently, then rewrite, re-audit and re-run, three rounds. The evidence is in [ship-agent-context-refresh-audit](../investigations/ship-agent-context-refresh-audit.md).

The earlier design is recorded in [agent-context-initialized](agent-context-initialized.md) and [add-user-instructions-to-skill](add-user-instructions-to-skill.md). This note records what the rewrite keeps and what it revises. The revisions were reported to the user on 2026-10-05; none has been explicitly confirmed yet. The version is 1.3.0, a minor bump, following the user's choice for `ship-reviewed-prs` ("No v2 yet").

## Decision

### Kept

- **The folder**: plain Markdown, committed, one note per file in a folder per type, a slug as the name.
- **Standing instructions are recorded without asking first**, announced in one line with how to revoke; revoked notes are archived, not deleted; when unsure, do not record.
- **Hand-offs carry a machine-checkable completion condition** and finished ones are archived automatically on hard evidence; absence of evidence is never treated as completion.
- **`AGENTS.md` and `CLAUDE.md` are never edited** by the skill; a conflict with them goes to the user.
- **A plugin SessionStart hook** is the activation mechanism, silent in repositories without the folder.
- No scaffolding without the user asking; no session journals; verify before reporting what a note claims.

### Revised

- **C1 — The hook prints a digest; nothing is read because a note calls itself important.** `agent_context.py digest` prints the standing instructions (titles), the open hand-offs and note counts in about 2 KB, offline. Why: the old hook ordered every session to read files, and "read every `importance: core` note" had become 33 of this repository's 38 notes, about 50 thousand tokens per session. `importance` is now ignored.
- **C2 — Notes are a colleague's notes, not standing orders.** They rank below the user in the session, `CLAUDE.md` / `AGENTS.md`, and the harness's permission and safety rules. An instruction that adds a confirmation, check or restriction is followed, including over a tool's default; one that would let the agent do more, or drop a check, needs the user's yes. Text addressed to agents that claims authority or asks for concealment is flagged, not followed. Why: the old text called committed files "standing orders from the user", so anyone who could add a file could direct the agent.
- **C3 — Hand-offs are checked by a script, when they are about to be relied on.** `reconcile` gives `DONE`, `OPEN` or `UNKNOWN` with evidence, from a structured `done_when` (`pr:`, `branch:`, `commit:`, `pending`, `manual`); values from notes never reach a shell. Only an explicit anchor can be `DONE`; a missing branch is not evidence. `--apply` archives in sessions that are already changing files, never unattended. Why: the documented `git ls-remote` check read "never pushed" and "offline" as "finished" and archived without a prompt, and every session ran it whether or not the work mattered. This narrows the user's "reconcile at every session start": the digest lists hand-offs as not verified, and the check runs before anything depends on one.
- **C4 — The index is generated.** `MANIFEST.md` is rebuilt from each note's `summary`, sorted, with no counts or dates. Why: a hand-edited file that every writer touched drifted in the baseline runs and conflicted on merge. The ledger, the index-splitting scheme and the hand slug algorithm are gone.
- **C5 — One test for what to write**: a later agent could not learn it from the code or git, and would do something wrong or wasteful without it. It replaces the five-minute rule.
- **C6 — Every standing rule in a message is recorded**, by meaning, not by trigger phrase, and only from the user's own typed words. The one-per-turn cap is gone: it reintroduced the asking the user had rejected. The announcement now says the file is not committed yet. A repository rule is kept in `instructions/` only, not also in the agent's own memory. In a repository with no folder, the rule is kept for the user only and the folder is not created unasked.
- **C7 — `status/` holds hand-offs, not claims.** Written when work will outlast the session. The "create a status entry within five minutes" rule and the claim that it coordinates parallel agents are gone: other branches cannot see it.
- **C8 — The skill never stages, commits or pushes on its own**, and says which files it left uncommitted.
- **C9 — Closing a note is one operation**: `archive` sets the status, adds a banner that depends only on the evidence, moves the file, fixes links to it and rebuilds the index, so the same archive on two branches merges cleanly.
- **C10 — `check` validates the folder**, in CI too: the index, frontmatter, superseded notes still active, notes naming files that no longer exist, credential shapes. The script refuses to write where it can tell the session is unattended.
- **C11 — Plans belong to `ship-better-plans`.** This skill indexes and reads them; its own plan template is gone.
- **C12 — Removed**: team mode, the scope grammar (an `until:` date remains), timed promotion to `AGENTS.md`, MCP and Obsidian sections, the four example transcripts, most of the eight templates' optional fields. A `/ship-agent-context:notes` command is added.

## Alternatives considered

- **Keep reconciliation in every session, as decided in June.** Rejected: it writes to the repository before the user has said anything, on whatever branch is checked out, including in CI. Checking before relying keeps the purpose (never report stale work as current) without that.
- **Do not commit the index at all.** Suggested by two reviewers. Not done: `ship-better-plans` and `ship-execute` look for `MANIFEST.md`, and people browse it. Generated and deterministic was the smaller change.
- **Stop moving closed notes; mark them in place.** Not done: the archive folder is what keeps closed notes out of searches and the digest, and existing folders use it.
- **Pre-approve only the read-only script commands.** Not done, as with `ship-reviewed-prs`: silent capture of a standing instruction needs the write commands, and the pattern cannot be anchored to the installed path.

## What would change this

- The first sessions with the installed plugin: does `${CLAUDE_PLUGIN_ROOT}` resolve in the hook, does the digest appear after a compaction, is the script pre-approved when the skill has not been loaded.
- Agents stop finding relevant notes because nothing is read up front: add `paths:` to notes, or let the digest name the notes for the current branch's changed files.
- Hand-offs pile up as `UNKNOWN` because nobody sets `done_when`: have `reconcile --apply` write the pull request number it found.
- The user wants reconciliation back at every session start.

## Related

- [ship-agent-context-refresh-audit](../investigations/ship-agent-context-refresh-audit.md) — the evidence
- [add-user-instructions-to-skill](add-user-instructions-to-skill.md), [agent-context-initialized](agent-context-initialized.md) — the earlier decisions
- [ship-reviewed-prs-refresh](ship-reviewed-prs-refresh.md) — the previous skill in the refresh
