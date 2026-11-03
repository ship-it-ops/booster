# ship-agent-context reference

The shape of each kind of note, and what makes one worth reading. Consult it when you write a kind of note you have not written before. [`SKILL.md`](SKILL.md) has the rules for when to write and how far to trust what is already there.

## Every note

A note is a Markdown file in the folder for its type, named with a short kebab-case slug. `new` creates it with this frontmatter:

```yaml
---
type: decision
status: active
created: 2026-10-04
updated: 2026-10-04
summary: Every CLI flag goes in src/cli/flags.ts; never parse argv in a command
---
```

| Field | Meaning |
|-------|---------|
| `type` | Matches the folder: `decision`, `investigation`, `scar`, `pattern`, `status`, `instruction`, `open-question`, `plan`. |
| `status` | `active` while it holds. Closed notes are `completed`, `superseded`, `revoked`, `expired`, `answered`, `abandoned` or `retired`, and live in `archive/`. |
| `summary` | One line, shown in the index and by `find`. Say what the reader should do or know, not just the topic. State durable facts ("shipped in PR 7"), never passing ones ("PR open"). |
| `paths` | Optional. Globs for the code the note is about, for example `[src/export/*, src/cli/flags.ts]`. `find` uses them, and `check` warns when one matches nothing any more. |
| `verified` | Optional. The date someone last checked the note against the code. `find` shows it. |
| `supersedes` | Optional. The slug of the note this one replaces. |
| `updated` | Change it when you edit what the note says. |

Older notes may carry `importance`, `tags`, `author` and similar fields. They are ignored; leave them or remove them. Nothing is read because a note calls itself important.

Keep a note short. If it needs supporting material (logs, a long transcript, an evaluation script), that belongs elsewhere in the repository with a link from the note.

## Decision

For a choice a later agent would otherwise reopen.

- **Context**: what prompted it.
- **Decision**: what was chosen, and who chose: quote the user when it was their call, and say when it was an agent's own judgement that nobody confirmed.
- **Alternatives considered**: each rejected option with the reason. This is the part nothing else records.
- **What would change this**: the conditions that should reopen it.

A decision is not edited into its opposite. When it is reversed, write the new decision with `supersedes:` and archive the old one as `superseded`. When one clause of a long decision changes, edit the clause and add a line under the title: `> Revised 2026-10-04: <what no longer holds>, see [other-note](other-note.md).`

## Investigation

For a root cause that took real work to find.

- **Symptoms**: what was observed.
- **Root cause**: file, line, mechanism, and how it was confirmed (a command, a test, a reproduction). If it was not confirmed, say "hypothesis" in the summary and the heading.
- **Ruled out**: what was checked and found not to be the cause. This saves the next person the same dead ends.
- **Fix**: what solved it, or what is proposed.

Check line numbers and behaviour against the code before you write them down; a root cause that does not match the code misleads more than none.

## Scar

For a lesson from something that actually went wrong.

- **What happened**: briefly.
- **Tripwire**: one sentence, "if you are about to X, stop and check Y". Put the same sentence in the summary.
- **Do not**: the specific action to avoid.

A scar stays as history. When the thing it warns about is verifiably gone (the tool was fixed, the code path removed), archive it as `retired` with the evidence, so nobody steers around a hazard that no longer exists.

## Pattern

For a convention you found by reading the code that is not written down anywhere else: when it applies, how it is done here with the key files, and the common mistake.

## Status: work left unfinished

A hand-off for whoever continues. Frontmatter adds `branch:` and `done_when:` (`pr:123`, `branch:<name>`, `commit:<sha>`, `pending` or `manual`). With `pending`, `reconcile` looks for a pull request from the note's branch and tells you its number, but it never closes the note on that alone, because a branch can carry several pull requests: put the number in `done_when` when that pull request is the whole of the work. `manual` notes are closed by hand.

- **What is done**, **what is left, in order**, **what the next person needs to know**, including what the user said not to do.

Write facts that can go stale as something to check, not as an assertion: "the branch had not been pushed when this was written" is better than "not pushed". No standing rules here: link to the instruction note.

## Instruction

A standing rule the user gave. Frontmatter adds `source: user`, and `until: YYYY-MM-DD` when the rule has an end.

- The **title** is the complete rule in one sentence, because the session-start digest shows only titles.
- **Instruction**: the user's sentence, quoted, with the date, and the reason if they gave one: it is what lets a later agent judge an edge case.
- **How to apply**: when it applies and what to do differently, including the edge the user mentioned.
- **To revoke**: what the user can say to turn it off.

## Open question

Something blocking that this session could not settle: what is known, what was tried, who or what can answer it. Close it as `answered` with the answer, or `abandoned`.

## Plan

Written by `ship-better-plans` in its own format when that skill is installed; this skill only indexes it. Without that skill, save a plan only when the user asks: goal, approach, status, and a line saying it is a free-form plan, not one an executor can run.

## The index and merges

`MANIFEST.md` is generated: one line per note, grouped by type, sorted by name, with nothing that changes unless a note does. Two branches that each add a note produce two different lines, and if they still conflict, the resolution is to run `index` again. A team that sees such conflicts often can add `docs/agent/MANIFEST.md merge=union` to `.gitattributes` and run `index` after merging.

Archiving is the same on every branch: the archived file depends only on the note and the evidence, not on the day, so two branches that archive the same finished hand-off merge cleanly.

## A folder written by an older version

Nothing needs converting by hand. Notes without a `summary` show their title in the index; a `## Done when` section in prose is still read; `importance`, `tags` and `scope: until:…` are tolerated. Run `index` once to regenerate `MANIFEST.md` in the current form, add summaries when you touch a note, and commit that as its own change.

## Checking a folder in CI

```yaml
- name: Check docs/agent
  run: python3 path/to/ship-agent-context/scripts/agent_context.py check
```

In CI the script reads and never writes. For other unattended runners, set `AGENT_CONTEXT_READONLY=1`.

It exits non-zero on a broken index, a note without frontmatter or title, a superseded note still marked active, or anything shaped like a common credential (a net for accidents, not a guarantee). It warns, without failing, about notes that name files which no longer exist, leftover template text, standing rules written into a hand-off, and text that tries to direct agents.
