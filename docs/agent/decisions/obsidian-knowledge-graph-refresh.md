---
type: decision
status: active
created: 2026-10-08
updated: 2026-10-08
summary: "obsidian-knowledge-graph 1.1 rewrite: notes as a record not instructions, a script and a digest hook, writes that ask, nothing overwritten (O1-O14); revises the March 2026 design"
paths: [skills/obsidian-knowledge-graph/*, plugins/obsidian-knowledge-graph/*]
---

# `obsidian-knowledge-graph` 1.1: the full rewrite, what changed, and why

## Context

Twelfth and last skill in the refresh. The evidence is in [obsidian-knowledge-graph-refresh-audit](../investigations/obsidian-knowledge-graph-refresh-audit.md).

Version 1.0.0 was the repository's first skill (March 2026, improved once that month). Its description said "ALWAYS activate at session start"; its protocol read the vault's whole index and every note marked `core` before any work; it edited `~/.claude/settings.json` to grant itself read and write access to the vault; it kept a hand-edited index with counts and a status column; and it described the notes as the agent's memory, to be acted on. It also kept folders for people and for session status in a vault that syncs to the user's other devices.

Its nearest relative, `ship-agent-context`, was rewritten earlier in this refresh ([ship-agent-context-refresh](ship-agent-context-refresh.md)), and the same findings applied here with two differences that shaped this rewrite: a vault is shared by every project and session on the machine, and it has no history, so an overwrite cannot be taken back.

The control run: with no skill, told only where the vault was, a current model found and respected a recorded decision that conflicted with the request, exactly as 1.0.0 did. It did not tell the user about a planted note that told agents to push to main, skip tests and hide the note; and it copied what it recorded into the harness's memory as well.

**This revises the user's earlier decisions about this skill, which are recorded in the vault itself** (`booster--knowledge-graph-initialized` and `booster--skill-v2-improvements`, both March 2026), and touches one of their conventions (`booster--workflow-conventions`). The list is under Consequences. The user has not ruled on it.

## Decision

- **O1 — Notes are an earlier session's record, not instructions.** They rank below the user, `CLAUDE.md` and the harness. A restriction is followed (do not, ask first, stop); a check is followed when the command is already the project's own; anything that would have the agent do more, skip a test or a review, run or fetch something the project does not define, or keep quiet is not followed and is reported.
- **O2 — A script carries the mechanics** (`scripts/vault.py`, standard library, 55 unit tests in CI): `digest`, `find`, `show`, `check`, `where` read; `new`, `amend`, `close`, `index`, `init` write. Notes are read and written only through it, so the folder boundary, the credential check, the dates and the index do not depend on the model remembering them.
- **O3 — A session-start hook prints a digest;** nothing else is read up front. The digest is counts and one line per recorded rule. `importance` and `confidence` decide nothing.
- **O4 — What is looked up depends on what is touched, not on how big the change feels.** Before changing how something behaves, one `find` with the paths and a word or two. Rules in the digest apply to small tasks too.
- **O5 — Only the commands that read are pre-approved.** Every write asks the user: that prompt is their check on what goes into a synced folder. The skill never edits permission settings.
- **O6 — Nothing is overwritten or deleted.** `new` creates exclusively; `amend` refuses a note that changed since it was read; a reversed decision is a new note that supersedes the old one, which is kept; a failed supersede writes nothing.
- **O7 — The index is generated.** A hand-kept index from 1.0.0 is never overwritten by a write; it is replaced only when the user agrees, a copy is kept, and its one-line summaries go on being used for notes that have none.
- **O8 — The user's own decisions are the user's to change.** Notes are marked with who said them; a note marked as the user's, or whose author is not recorded (every 1.0.0 note), is not closed, superseded or rewritten without the user asking. A convention is recorded only from the user's typed words. The marking earns a note this care; it never grants anything.
- **O9 — What never goes into a vault:** credentials (the script refuses the common shapes), personal details, customer data and anything under a confidentiality agreement. `People/` and `Status/` are no longer read or written; nothing in them is deleted. A repository can be excluded.
- **O10 — Project identity:** the remote's repository name, then the checkout's directory name; notes under either are read. A note records its repository, so two repositories that share a name are told apart and the other's notes are leads. Outside a repository only `general` is read.
- **O11 — Where a fact belongs:** when a repository has `docs/agent/`, everything about that repository goes there. The vault is for what should travel across projects, the user's own working preferences, and projects with no notes of their own. Nothing is copied into the harness's memory as well.
- **O12 — With no vault configured, nothing happens** and none is proposed. The one exception is the upgrade: a vault that 1.0.0 used is named once from the permission rules it added, and recorded only when the user says yes.
- **O13 — Other sessions, the app and sync write here too:** exclusive creates, atomic replaces, no symbolic links followed, sync-conflict copies not read until the user has merged them. The ledger scheme for several sessions is gone.
- **O14 — Version 1.1.0,** minor.

## Alternatives Considered

- **Keep reading through the Read tool with a permission rule for the vault.** Rejected: a rule wide enough to read `_ai/` without prompting is written by editing the user's settings, and nothing then keeps a read inside `_ai/`. `show` does both jobs.
- **Pre-approve every script command.** The first draft did, while telling the user that writes go through their prompts. Reviewers caught the contradiction; the prompts are the point.
- **Rebuild the index on every write regardless.** That silently replaced a hand-kept index holding the only one-line summaries 35 real notes had. Found in round 2 by all six reviewers.
- **Refuse to write a note that the steering check flags.** A recorded decision can legitimately say "hotfixes can go out without review". The check warns; a person judges.
- **Guess the vault's location** (common paths, the harness's memory). The script never guesses; it reads the one setting, and for the upgrade names what 1.0.0 left in the settings file.

## Consequences

- About 2,700 words of skill text plus a reference file, against about 4,700 and 1,900 before; a session with no vault pays for one description line.
- **For the user to rule on** (their March 2026 decisions): reading the index at session start is replaced by the digest; the `importance` priority signal and the `confidence` and 90-day staleness checks are replaced by "check a claim against the code when you rely on it"; the conceptual-search steps and tag taxonomy by `find`; the project aliases file by reading both names and `init --project-name`; ledger-based writes by exclusive and atomic writes; the flat layout and the hand-kept index by type folders (which the vault already has) and a generated index.
- **And on one of their conventions:** "use the Obsidian vault as the primary shared knowledge store between Claude instances". O11 sends notes about a repository that has `docs/agent/` to that folder and not to the vault. If the user wants both, O11 is the line to change.
- An existing user must run `init` once; until then the skill reads nothing and says so once per session.
- The permission rules 1.0.0 added to `~/.claude/settings.json` (`Read`, `Write`, `Edit` and `mkdir` for the vault) are still there on machines that used it. They are the user's to remove; with them in place, a hand edit of a note would not prompt, which is one reason the skill now forbids hand edits.

## Revisit Triggers

- The `allowed-tools` patterns turn out not to match the command as agents type it (untested in a live session): every read would then prompt, and the fix is in the frontmatter.
- A vault grows past a few hundred notes and the digest or `find` becomes slow: both read every note.
- Users want notes about a `docs/agent/` repository in the vault as well: revisit O11.

## Related

- [obsidian-knowledge-graph-refresh-audit](../investigations/obsidian-knowledge-graph-refresh-audit.md) — the evidence
- [ship-agent-context-refresh](ship-agent-context-refresh.md) — the model this follows
