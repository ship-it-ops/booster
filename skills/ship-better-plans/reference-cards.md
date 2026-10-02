# ship-better-plans — task card reference

Detail for steps 5 to 7 of `SKILL.md`: how plans go wrong, how to write task cards, what the executor does with them, and the linter's checks done by hand. Read "How plans go wrong" before writing the specification and again before linting.

## Contents

- [How plans go wrong](#how-plans-go-wrong)
- [Task cards](#task-cards)
- [The plan as a contract with the executor](#the-plan-as-a-contract-with-the-executor)
- [Lint by hand](#lint-by-hand)

---

## How plans go wrong

Read this before you lint. Patterns seen in plans that looked complete and were not:

- A card says "as specified above", "see the interface section" or "the reference implementation". The task agent sees none of them.
- A constraint (commit rules, no new dependencies) sits in the Constraints section and in no card or convention.
- A `Verify` step compares against a commit, branch or pull request that does not exist yet at that point, or needs a file another task owns.
- A check that can only pass: "tests pass" where no test covers the change, a diff of an empty range, a grep for a word the new text will always contain.
- A new check, gate or alarm is never shown firing on a bad case.
- The risk table promises a mitigation that no requirement or task builds.
- An edge case states what existing code does with an input nobody tried.
- The review changed the approach, and the requirements and cards still describe the old one.
- An assumption the whole approach rests on is parked as an open question, and the plan is marked approved.
- The plan refers to notes (decisions, open questions) that were never written.
- A success criterion can only be shown in an environment nobody has (another operating system, production data), and no task, gate or final-check line says who shows it.
- The work needs two pull requests, and nothing says what must be true before the second begins.

---

## Task cards

A task agent receives its card, the plan's "Conventions for every task" block, and the text of each id the card lists under Covers. Nothing else: not the Facts, the Approach, the Interfaces section, or other cards. Anything from those sections that the task needs is written into the card's `Do`.

| Field | Rule |
|-------|------|
| `Depends on` | `none`, or task ids separated by commas, and nothing else. Everything the task needs that another task produces. |
| `Covers` | The `FR`/`AC` ids it delivers (or `SC` ids in a plan without requirements). Groundwork writes `none — enabling: <what it unblocks>`. When a requirement is split across cards, each card's `Do` says which part it delivers. |
| `Files` | Every path it creates, modifies or deletes, in backticks, each marked `(new)`, `(modify)` or `(delete)`. Include files touched as a side effect: lockfiles, index or barrel exports, route or DI registries, snapshots, generated output. Paths marked modify or delete must exist today or be created by a task it depends on. The task agent is told these are the files it owns. |
| `Do` | What to build and the context needed to build it: the interface to implement, the existing pattern to copy and where it lives, decisions already made, the tests to write, and what to leave alone. |
| `Verify` | A command, run from the repository root, and the expected result. In a workspace, include the package filter or directory. |
| `Kind` | `code`, `test`, `docs`, `config`, `infra`, `migration` or `security`; the executor picks its reviewer from this. |
| `Size` | `S` (one focused change) or `M` (several files, one concern). Anything larger is split. |
| `Reversibility` | `safe`, or what makes it hard to undo. |
| `Gate` | Required whenever Reversibility is anything but `safe`, and on the first task of a later pull request: what a person confirms before the task runs, with the command that shows it when there is one. A gate can also guard a precondition, such as a clean working tree. |

A weak card and a card done properly:

```markdown
### T4 — Drop the old column
- **Depends on:** the backfill
- **Covers:** FR-3
- **Files:** migrations
- **Do:** Remove the legacy column as described in the migration section.
- **Verify:** migration runs
```

```markdown
### T4 — Drop users.legacy_plan
- **Depends on:** T2, T3
- **Covers:** FR-3, AC-5
- **Files:** `db/migrations/20260930_drop_legacy_plan.sql` (new), `db/schema.sql` (modify)
- **Do:** Add a migration that drops the column `users.legacy_plan`, following the format of `db/migrations/20260811_add_plan_id.sql`, and regenerate `db/schema.sql` with `make schema`. No code reads the column after T2, and T3 copied every value into `users.plan_id`. Do not touch any other column or add a down migration; the way back is the backup named in the gate.
- **Verify:** `make migrate-test` → applies cleanly on the test database; `grep -c legacy_plan db/schema.sql` → prints 0
- **Kind:** migration · **Size:** S · **Reversibility:** destructive: the column's data cannot be recovered from the database afterwards
- **Gate:** the user confirms that T2 is deployed and that last night's backup restored cleanly (`make verify-backup` → OK)
```

The weak card's dependency is prose, so a tool reads it as no dependency; it says "as described in the migration section", which the agent cannot see; it names no file; and its check cannot fail.

**Verify must hold where the task runs.** Tasks may run in separate fresh checkouts that contain only that task's changes and those of its dependencies. Verify runs on the task's finished working tree, before the executor commits it, so a check must give the same answer whether or not the work is committed. A check that needs another task's file, an open pull request, or a commit that has not been made yet will fail or pass vacuously. A check that needs a running service says how to start it. If a check cannot run until several tasks are merged, or needs an environment task agents do not have, it belongs on the Final check line, with who runs it.

**Tests travel with the code.** A task ships the tests for what it changes. The exception is characterization tests that must exist before a refactor begins; those are their own first task.

**Spikes.** A spike card states the question, how to answer it, and what happens next for each answer. It has two legal shapes. Continue or stop: "If the sandbox can replay partial captures, continue. If not, stop and report; nothing after this task starts." Or a result that later cards need: the spike writes it to a named file that those cards list in `Do`, or the card after it carries a `Gate` saying the plan was revised for the result.

**Conventions for every task.** Setup for a fresh checkout and constraints on how work is done (commit message format, no new dependencies, a style rule from `CLAUDE.md`) go in this block once. A constraint that lives only in the plan's Constraints section never reaches a task agent.

**Not tasks.** The executor commits each task's work; branching, pushing, opening a pull request and marking the plan complete are the executor's job and need the user's say-so. Leave them out. If the work must land as more than one pull request, describe the sequence in the Approach section and put a `Gate` on the first task of each later part ("the user confirms PR 1 is merged and CI on main is green: `gh run list --branch main --limit 1`").

**Execution order.** `lint_plan.py --dag` derives the order from the cards: a graph, parallel waves and the critical path, or a single line when the plan is sequential. Paste its output; do not edit it. The linter rejects a pasted order that no longer matches the cards. If the result surprises you, fix the `Depends on` fields. A plan with no parallel wave is fine; say why in a sentence, as the refactor example does.

---

## The plan as a contract with the executor

`ship-execute` (version 1.1.0 and later) reads the plan, hands each card to a fresh agent, runs independent cards in parallel worktrees, and merges them. What it takes from the plan:

| Plan element | Executor use |
|--------------|--------------|
| Frontmatter `approval` | A `draft` plan is not executed without the user's explicit confirmation |
| Frontmatter `base` | Detecting that the code moved since the plan was written |
| Frontmatter `plan_format: 2` | Telling card-based plans from older ones |
| Card `Depends on` | Ordering and the parallel waves |
| Card `Files` | The files the task agent is told it owns |
| Card `Do`, "Conventions for every task", and the text of the ids in `Covers` | The task agent's whole briefing. The ids are passed exactly as listed; a covered requirement is not expanded into its other criteria |
| Card `Verify` | The command the task agent must run and report |
| Card `Kind` | Which review the task's change gets |
| Card `Gate` | Execution pauses for the user before the task; gated tasks never run in a parallel wave |
| Verification section | Setup for each fresh checkout, and the final check before hand-off |

An executor that does not know this format (an older `ship-execute`, or another tool) will still see the gate and the conventions if it reads the plan, but nothing guarantees it stops. If the plan will be built by anything else, say so to the user at approval.

---

## Lint by hand

When `python3` is not available, check the same things yourself:

1. Every section of the template is present and either filled or `N/A — reason`. No `TBD`, `TODO`, `???`, `…`, template comment or template text is left as content. The frontmatter says `approval: draft` or `approved`.
2. Every `SC` is named by a requirement, an acceptance criterion, a task's `Covers` or the Final check. Every `FR` has at least one `AC` and a task. Every `AC` names what it verifies, says how, and is in a task's `Covers` or on the Final check line. No id is used that is not defined.
3. Every card has `Depends on`, `Covers`, `Files`, `Do`, `Verify` and `Reversibility`. `Depends on` is `none` or task ids only. Every dependency is a real task. Following the dependencies never returns to the task you started from. The Execution order section matches the cards.
4. For every pair of tasks whose files overlap (the same path, a directory and a file inside it, a glob that matches), one depends on the other, directly or through a chain.
5. Every path marked `(modify)` or `(delete)` exists, or is created by a task the card depends on. Every path marked `(new)` does not exist yet. Every `path:line` in the plan points at a real, non-blank line. Paths and scripts named in `Do` and `Verify` exist or are created by this task or one it depends on.
6. Every task whose Reversibility is not `safe` has a `Gate`.
