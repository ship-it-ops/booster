# ship-execute — reference

Detail for the steps of `SKILL.md`. Read it before step 1, and again after a compaction.

Commands written as `plan_tasks.py <command>` stand for `python3 "${CLAUDE_SKILL_DIR}/scripts/plan_tasks.py" <plan-file> <command>`.

## Contents

- [Git protocol](#git-protocol)
- [Dispatching tasks](#dispatching-tasks)
- [Accepting a result](#accepting-a-result)
- [When a task does not finish](#when-a-task-does-not-finish)
- [Correcting the plan during a run](#correcting-the-plan-during-a-run)
- [Plans that land in parts](#plans-that-land-in-parts)
- [Reviews](#reviews)
- [The final check](#the-final-check)
- [Writing the outcome into the plan](#writing-the-outcome-into-the-plan)
- [The report](#the-report)
- [After the report](#after-the-report)
- [Plans in other formats](#plans-in-other-formats)
- [How runs go wrong](#how-runs-go-wrong)

---

## Git protocol

The whole run rests on one rule: the execution branch only ever holds commits whose check you have seen pass there.

**The execution branch.** `git switch -c ship/<plan-slug>` from the current commit. If that branch already exists and the ledger is empty, someone else's work may be on it: ask before using it.

**Where task agents work.** Every task agent runs in its own worktree, alone or in a wave. An isolated agent (the Workflow tool's `isolation: 'worktree'`, or the Agent tool's `isolation: "worktree"`) starts in a fresh worktree under `.claude/worktrees/`, on its own throwaway branch, cut from the commit that is checked out in the main checkout. So:

- Everything a task depends on must be committed on the execution branch, and that branch must be checked out, before the task is dispatched. Uncommitted changes are not in the worktree.
- A worktree contains tracked files only. Installed dependencies, build output and environment files from the main checkout are not there, which is why the briefing carries the plan's setup. Say in the start summary how many fresh checkouts will need that setup, since it is where the time goes.
- The agent's commit lands on the throwaway branch. It reaches the execution branch only when you bring it over.
- While worktrees exist, `.claude/` shows as untracked in the main checkout. Ignore it, and never stage it.

**Bringing a commit over.**

```bash
git cherry-pick <agent's sha>      # one task at a time, in the order `next` listed them
git rev-parse --short HEAD         # the new sha: this is the task's commit from now on
```

The cherry-pick creates a new commit with a new sha. The new one goes to `mark`, into the report, and into any later `git revert`.

If the agent made more than one commit, check and take all of them: `plan_tasks.py check <task> <start>..<agent tip>`, then `git cherry-pick <start>..<agent tip>`. Record the last new sha.

A conflict during cherry-pick means two tasks changed the same lines, which the plan's linter is meant to prevent. Do not resolve it by guessing: `git cherry-pick --abort`, and re-run that task alone from the updated branch tip (its briefing unchanged). If it conflicts again, mark it `blocked` and tell the user.

**Taking a commit back off.** `git revert --no-edit <sha>`. Revert keeps the record and destroys nothing. Use it when your `Verify` fails after the cherry-pick, when the suite fails after a wave, and when a review finds the commit should not stand.

**Staging.** Stage files by path, always. If the repository has no ignore rule for the caches a test run leaves behind, say so in the report; adding an ignore file is outside every card.

**Cleaning up.** `plan_tasks.py cleanup <task>` removes the worktree and throwaway branch the ledger recorded for a task, and only when that task is `done`, the path is one of this repository's worktrees under `.claude/worktrees/`, and the branch is not the run's own. Do not remove worktrees or delete branches by hand: the directory is shared with other sessions, and a worktree whose task is not `done` holds the only copy of that work. Leave those, and say where they are in the report. When a task is retried, the first attempt's worktree is replaced in the ledger by the second's; remove the first with `git worktree remove` only after confirming with `git worktree list` that it is the path that attempt reported.

**Working without the Agent tool.** Then you do each task yourself on the execution branch, and acceptance changes shape: note `git status --short` before the task; do the work from the briefing; run the card's `Verify` on the working tree; if it passes, stage the task's files by path and commit; run `plan_tasks.py check <task> HEAD`; if `check` fails, `git revert --no-edit HEAD`; otherwise `mark` it `done` with that commit. If the task does not finish, undo only what it changed: restore the tracked files it modified (`git restore --staged --worktree -- <those paths>`, which will ask for permission) and delete only untracked files that were not there before the task. Never delete an untracked file you did not create.

---

## Dispatching tasks

A task agent gets its briefing and nothing else from the plan. The briefing (`plan_tasks.py brief <task>`) already contains the card, the text of the ids it covers, the files it owns, the verification, the conventions, the setup, and the rules a task agent works under. Do not summarise it, add to it from other sections, or paste the plan.

**A wave, with the Workflow tool.** `plan_tasks.py wave` prints the arguments: the start commit and, for each ready task, the path of a briefing file it has just written. Pass that JSON as the `args` object, with `scriptPath` set to `workflows/execute.workflow.js` in this skill's directory. Each agent reads its own briefing file. The script returns, for each task, `status`, `commit`, `branch`, `worktree`, the verification it ran, `filesChanged`, `deviations`, `question` and, for a task that changes no files, `answer`. It reports as `blocked` an agent that crashed, one that started from the wrong commit, and a "done" without a commit.

**The task-agent prompt.** Without the Workflow tool, and for every single task, dispatch with the Agent tool, `isolation: "worktree"`, and this prompt. For a wave, send one such call per task in a single message.

```text
You are implementing one task of an implementation plan, in your own git worktree.
Your worktree should start at commit <sha of the execution branch tip>; if
`git rev-parse --short HEAD` shows something else, do nothing and say so.
Read your briefing at <path printed by `brief <task> --out`> in full before doing
anything. It is everything you need and everything you are allowed to rely on.
In your result, include the output of `pwd` as well as what the briefing asks for.
```

`next` never lists a gated task as part of a wave, never puts two tasks that name the same file in one wave, and holds a wave to four tasks; the rest become ready on the following round.

**A task that changes no files** (a spike, an investigation) is briefed to commit nothing and return an `answer`. `next` lists it alone and holds everything else until it is done, because the plan put the question there to be answered first. Show the answer to the user, or act on it as the card says, and record it in the ledger note. If later cards need it, say so to the user: the cards were written before the answer existed, and may need a correction.

**When the fresh checkout is the problem.** If a task agent fails because its worktree lacks something the plan's setup does not provide (an environment file, a running service, credentials), retrying will not help. Ask the user once: supply the missing setup step, or run the tasks one at a time on the execution branch without isolation, as in "Working without the Agent tool".

---

## Accepting a result

A task agent's report is where you start, not what you record. For each task that reports `done`, one at a time:

1. **Record it:** `mark <task> running --branch <branch> --worktree <path>`, so a resume can find the work.
2. **Check what changed**, on the agent's commit, before it goes anywhere: `plan_tasks.py check <task> <sha>`.
   - `FAIL`: the commit changes or deletes a test the card does not own, changes a check or its configuration, or commits caches, build output, or environment or credential files. Do not cherry-pick it. Treat the task as not finished.
   - `NOTE`: a file outside the card's `Files` was touched, or an owned file was not. Read the change. A small, explained, necessary edit is a deviation to record; anything else goes back.
3. **Cherry-pick it**, and take the new sha.
4. **Run the card's `Verify` yourself**, on the execution branch, exactly as `summary` prints it. If it has several commands, run them all. If a part of it is something to observe and not a command, observe it and say what you saw.
5. **Mark it:** `mark <task> done --commit <new sha> --verified "<command> -> <result>" --note "<deviations, if any>"`, then `cleanup <task>`.

If step 4 fails, revert the new commit first, then go to the table below. The agent's own verification output helps you tell a flaky or environment-dependent check from a real failure. It never replaces yours.

---

## When a task does not finish

A commit that failed `check`, your `Verify`, the suite after a wave, or a blocking review is not on the execution branch when you retry or move on. A `blocked` task has no commit there.

| What happened | What to do |
|---------------|------------|
| The agent returns `needs-decision` | The plan and reality disagree: a card contradicts an existing test, the code is not what the card describes, or its `Verify` cannot pass as written. Check the claim yourself, then put it to the user with the options you see (correct the card, widen its files, drop the task). Do not retry it unchanged. |
| Your `Verify` fails, or the agent returns `blocked` | First decide whether the work or the check is at fault. A check that cannot pass as written is `needs-decision`, as above. Otherwise dispatch one fresh agent from the current branch tip, with the same briefing plus the failing output and what was tried. If that also fails, `mark` it `blocked` with the output and carry on with what does not depend on it. Do not try a third time, and do not fix it yourself by loosening the check. |
| `check` fails | The commit is not taken. If the file it flagged is one the task genuinely had to change, the card is incomplete: that is `needs-decision`, for the user. Otherwise dispatch once more with the briefing plus the reason it was rejected. A second rejection is `blocked`. |
| The commit to take back has `done` tasks built on it | Do not revert it: later commits depend on it. Dispatch a fix agent with the task's briefing and the failing output, to fix it in one new commit, accepted the usual way. If that fails, stop and put it to the user, naming the tasks that depend on it. |
| A gated task is retried | Its approval was used up. Ask the user again. |
| A task that changes no files answers "stop" | Mark it `needs-decision`. Everything after it waits for the user, because the plan said its continuation depends on the answer. |
| The user declines a gate | `mark` it `declined`. Its dependents are not runnable; `next` reports them. |
| The suite fails after a wave although each task passed alone | Find which commit introduced the failure by running the suite at each commit of the wave. Revert that commit and treat its task as failing `Verify`. |
| The agent crashed, or started from the wrong commit | Its worktree holds nothing you want. Remove the worktree and branch, and dispatch again. |
| The agent finished but left its worktree with uncommitted changes | The commit is what counts. Uncommitted leftovers are discarded with the worktree. |

A task that is `blocked`, `needs-decision` or `declined` stops only the tasks that depend on it (a task that changes no files is the exception: see "Dispatching tasks"). The run continues with everything else, and the report lists what was left. Tasks that can no longer run stay `pending` in the ledger, so a resume picks them up once the user has decided. `skipped` is for a task the user chose to drop.

---

## Correcting the plan during a run

When the user decides a card should change (after a `needs-decision`, or because a spike's answer changes later work):

1. Edit the card in the plan file. Change only what the user decided.
2. Run `summary` again. If `ship-better-plans` is installed, also run its linter with `--revising`.
3. Commit the plan file alone: `Plan correction: <task> <what changed>`, and add a dated line to the plan's Status section saying what changed and why.
4. `mark <task> pending`, then continue from `next`.

`next` and `ledger` warn when the card of a `done` or `running` task was edited after the ledger recorded it. A warning on a `done` task means its commit was built from a card that no longer exists: tell the user and ask whether to redo it.

Never change a card to make a failing task pass without the user's decision. That is working around the plan.

---

## Plans that land in parts

Some plans must land as more than one pull request: the first task of a later part carries a gate such as "the user confirms PR 1 is merged and CI on main is green". That gate cannot be passed during the same run.

When the user's answer to a gate is "not yet, the earlier work has to merge first" (any other no is `declined`):

1. Leave the gated task `pending`. Do not mark it `declined`.
2. Finish this part: steps 5 and 6 for what was built, with the report saying which tasks belong to the next part. The plan's `status` stays `active`.
3. When the user comes back after the earlier part has merged, this is a resume. The earlier tasks' commits now exist on the base branch under new shas, so confirm with the user that they are merged, create a new branch from the updated base (`ship/<plan-slug>-part-2`), record it with `set branch` and `set start`, pass the gate with `approve`, and continue from `next`.

---

## Reviews

Reviews are done by an agent that did not write the code and is shown only what a reviewer needs. If there is no Agent tool, you review the diff yourself against the same instructions, and the report says the review was not independent.

**Sibling review skills.** Before dispatching a reviewer, look at the skills available in this session. If the skill that fits is listed, put its name in the reviewer's prompt exactly as listed (plugin skills are listed as `plugin:skill`, for example `ship-clean-code:ship-clean-code`). If it is not listed, leave that line out. A skill that is not installed is not an error.

| Kind of change | Skill |
|----------------|-------|
| `code` | `ship-clean-code` |
| `test` | `ship-tested-code` |
| `security`, or anything touching authentication, input handling, secrets or personal data | `ship-secure-code` |
| `infra`, `config` (CI, containers, deployment) | `ship-devops` |
| `migration` | `ship-secure-code` and `ship-devops` |

### During the run

A task whose `Kind` is `security`, `migration` or `infra` is reviewed before the next wave, because a mistake there is expensive to find later. Dispatch one reviewer agent with:

```text
Review one commit in the repository at <path>. Do not change anything.

Commit: <sha> on branch <execution branch>. See it with `git show <sha>`.

It was meant to do this:
<the task's briefing, from WHAT TO DO through HOW IT IS VERIFIED>

Look for: behaviour that does not match what the task was meant to do; mistakes in the
code (wrong logic, unhandled failure, unsafe handling of input, secrets or data); tests
that would still pass if the behaviour were wrong; and anything changed that the task did
not call for.
<if a sibling skill is available: "Load the skill `<exact name>` with the Skill tool and
apply it to this commit. Start your answer by saying whether you were able to load it.">

Report each problem with the file and line, what goes wrong, and how sure you are. Mark
each as blocking (the commit should not stand as it is) or not. An empty list is a fine
answer.
```

A blocking finding goes to a fresh fix agent in its own worktree: the original briefing, the finding, and the instruction to fix it in one new commit and run `Verify`. Accept that commit like any other, and add its sha to the task's ledger note. One round; what is still open after it goes to the user.

### The whole change

Once, in step 5, after the commands are green:

```text
Review a completed change in the repository at <path>. Do not change anything.

The change is `git diff <start sha>..HEAD` on branch <execution branch>.

It was built from a plan. The plan's success criteria, requirements and acceptance criteria:
<those sections of the plan>
What the plan ruled out:
<the Non-goals section>
Conventions the work had to follow:
<the Conventions for every task block>
Tasks that were left out, and why:
<from the ledger>

Check that the change does what the criteria say and nothing else of note; that the pieces
fit together (each task was checked alone); that nothing was weakened to pass (tests,
checks, error handling); that new tests would fail if the behaviour were wrong; and that
it is safe to merge. Run the tests if that helps you.
<if a sibling skill is available: the same line as above>

Report each problem with the file and line, what goes wrong, and whether it blocks.
An empty list is a fine answer.
```

Which sibling skills: take the `Kind` of each `done` task, look each up in the table above, and give the reviewer every skill in that set that is available, telling it which commits each applies to. With more than two, use one reviewer per skill, three at most. For a change that touches authentication, input handling, secrets or personal data, one of them is `ship-secure-code` when it is available.

Fix blocking findings with a fix agent, one commit per fix, accepted by you in the usual way. Then have the fixes reviewed once more. After that second round, anything still open is reported to the user as open; do not loop.

`ship-reviewed-prs` reviews a pull request on GitHub, so it cannot run before one exists. Offer it after the user chooses to open a pull request.

---

## The final check

Run on the last task commit, each part recorded with the command and its result:

1. **The plan's commands**: setup, build, test, lint, compared with the baseline from step 3. A failure that was already in the baseline is reported as pre-existing, not as yours and not as fixed.
2. **Every `done` task's `Verify`, again.** `summary` lists them. A later task can break an earlier one, and the suite does not always cover what a card's own check does.
3. **The plan's Final check line.** For each success criterion it names:
   - a check you can run here: run it, record the result;
   - a check that needs a person, a pull request, CI, staging, production data or another machine: record it as "still to be shown" with who or what shows it. Do not run a check against a shared or production system on your own initiative, and do not mark such a criterion met.
4. **Acceptance criteria that no task owned** (those listed only on the Final check line): the same rule.

A criterion belonging to a task that was `blocked`, `needs-decision` or `declined` is not met. Say so.

If a command or a re-run `Verify` fails here, find the commit that introduced the failure, revert it, and handle that task as in "When a task does not finish". One round of that; if the final check is still red, report it as red.

---

## Writing the outcome into the plan

Edit the plan file on the execution branch:

- **Status section**: add a dated entry. The branch and its first and last commit; each task with its state and commit; deviations from the cards and why; corrections to the plan that the run revealed; criteria still to be shown and by whom.
- **Frontmatter `status`**: this is the one rule for it. `completed` when every task is `done`, the plan's commands pass, and nothing in the Final check failed here. A criterion that can only be shown elsewhere (CI on the pull request, staging, a person) does not block `completed`, because the executor's work is finished; but the Status entry opens with the list of criteria still to be shown and by whom, and the report never calls them met. In every other case the plan stays `active`.
- **`updated`**: today's date.
- If the repository has `docs/agent/MANIFEST.md` and it lists this plan, update that entry to match: when the file says it is generated, rebuild it with the `ship-agent-context` skill's `index` command (or leave it and say so, if that skill is not installed) instead of editing it. If it does not list the plan, leave the index alone and mention it in the report.
- A decision made during the run that a later agent would otherwise reopen, or a trap worth warning about, can be recorded under `docs/agent/decisions/` or `docs/agent/scars/` when the repository uses them.

Commit these edits as one commit, `Record execution of <plan title>`, after the reviews and before the report. Write nothing else into `docs/agent/` during the run: the ledger holds the in-flight state, and it lives in `.git`.

---

## The report

Lead with the outcome in one or two sentences, then the detail. Keep it to what the user needs in order to decide what to do with the branch.

```text
<Built N of M tasks of "<plan>" on branch ship/<slug> (<first sha>..<last sha>). One sentence on the state: complete and verified / complete with items still to be shown / incomplete, and why.>

Tasks
- T1 <title>: done (<sha>). Verify: `<command>` → <result>
- T2 <title>: needs your decision. <the contradiction, in a sentence>
- T3 <title>: not run. You declined its gate.
- T4 <title>: not run. Depends on T3.

Checks on the last task commit (<sha>)
- <command> → <result> (baseline: <result>)

Success criteria
- SC-1: met. <the check and its result>
- SC-2: still to be shown by <who or what>: <the check>
- SC-3: not met. <why>

Review
- <what was reviewed and by whom: an independent reviewer, with or without which sibling skill, or yourself; findings fixed; findings still open>

Deviations and corrections to the plan
- <anything done differently from a card, and anything the plan had wrong>

Left behind
- <worktrees or branches not removed, and why; missing ignore rules; anything the user should know about their repository>
```

Leave out a section that has nothing in it. Do not describe work as verified unless you ran the check, and do not describe the plan as complete if any task was left out.

---

## After the report

Ask one question:

- **Keep the branch as it is.** Nothing more happens. The ledger stays, so the run can be resumed or inspected later.
- **Push and open a pull request.** This choice is the permission. First look at `git log --name-only <start>..HEAD` for anything that should never be pushed (environment or credential files); if there is any, stop and tell the user. Then push the execution branch and `gh pr create`, with a title from the plan and a body that summarises what was built, the checks and their results, and what is still to be shown. Follow the repository's and the user's conventions for commit and pull request text, and add no attribution lines they have not asked for. If `ship-reviewed-prs` is installed, offer to run it on the new pull request.
- **Show the diff.** Walk the change task by task, then ask again.
- **Discard the work.** Ask once more, listing exactly what will be deleted. What can be deleted is only what the run created: the execution branch if the ledger says `created: yes`, the worktrees recorded in the ledger, and the ledger itself (`plan_tasks.py clear`). First compare `git log <start>..<branch>` with the commits in the ledger: if the branch holds a commit the run did not make, do not delete it; tell the user. If the run worked on a branch it did not create, discarding means `git revert` of the run's commits, never deleting the branch. If the plan's own files were first committed by this run (`plan_commit` in the ledger), put every file of that commit back into the working tree of the starting branch before deleting anything, so the plan and its notes are not lost; the plan stays `active`. Deleting a branch will ask for the user's permission; that is intended.

---

## Plans in other formats

`summary` reports "no task cards found" for a plan that is not in the card format. Such a plan gives no per-task files, checks or gates, so the protections above do not apply. Tell the user, and offer two routes: have `ship-better-plans` revise the plan into the card format, or, on their explicit yes, execute it one step at a time in the order written, treating each step as a task with no parallelism, asking before any step that deletes or migrates something, and verifying each step with the plan's test command.

A plan that has cards but also problems (`summary` exits 1) is not executed until the plan is fixed.

---

## How runs go wrong

- Parallel task agents finish, and their work is never brought onto the execution branch, because nobody was told to commit or which commit to take.
- A task is recorded as done on the agent's word. The check was never run on the branch that will be merged.
- A commit whose check failed is left on the branch, the task is called blocked, and later tasks are built on it.
- A red check goes green because a test was edited, skipped or deleted, or a check's configuration was loosened. `check` exists to catch this; read its output.
- `git add -A` commits caches, or the worktrees directory.
- The plan is marked completed although a task was declined, or a criterion that can only be shown in CI is reported as met.
- A reviewer that needs a pull request is invoked before one exists, and its verdict is invented.
- The run is interrupted and restarted from the top, redoing or duplicating finished tasks, because nothing recorded what was done.
- A gated task runs inside a parallel wave before anyone answered the gate.
- A merge conflict between two tasks is resolved by an agent that understood neither.
- The user's uncommitted work is stashed "temporarily" and forgotten.
- A card is quietly rewritten so that a failing task passes.
