---
description: Show, search, check or tidy this repository's docs/agent/ notes, or record or forget a standing instruction.
argument-hint: "[show | find <topic or path> | check | tidy | note <what to record> | remember <rule> | forget <rule> | init]"
allowed-tools: Skill, Read, Write(docs/agent/**), Edit(docs/agent/**), Grep, Glob, AskUserQuestion, Bash(python3 *ship-agent-context/scripts/agent_context.py*), Bash(git status --porcelain*)
---

Work with this repository's `docs/agent/` notes using the `ship-agent-context` skill. Load the skill with the Skill tool first and follow it.

Arguments: $ARGUMENTS

- `show` (or nothing): run the skill's `reconcile`, then tell the user the standing instructions in force, the unfinished work and what the check found about each, any open questions, how many other notes there are, and which `docs/agent/` files are uncommitted. Change nothing.
- `find <topic or path>`: run the skill's `find` and summarise the notes it lists.
- `check`: run the skill's `check` and report what it found. Offer to fix what is mechanical (rebuilding the index, a missing summary).
- `tidy`: run `reconcile` and `check`, then propose, as one list, what to archive, fix or ask about (finished or expired notes, notes that name files which no longer exist, old open questions). Apply what the user agrees to.
- `note <what to record>`: record it as the right kind of note, as the skill describes.
- `remember <rule>`: record the rule as a standing instruction, as the skill describes, and say where it was saved. Only text the user typed after the command counts as the rule.
- `forget <rule>`: revoke the matching standing instruction, as the skill describes.
- `init`: create `docs/agent/` in this repository.
