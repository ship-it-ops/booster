---
name: ship-execute
description: >
  Use when an approved, written implementation plan exists and the user wants
  it built: they chose to build after `/ship-plan`, ran `/ship-execute`, or
  asked to execute, build or implement "the plan" (normally a
  `ship-better-plans` plan under `docs/agent/plans/`). Also use to resume a
  plan execution that was interrupted. Not for planning new work (use
  `ship-better-plans`), for work that has no written plan, for trivial edits,
  quick questions, or debugging one known bug. Cannot run in plan mode.
allowed-tools: Agent, Workflow, Skill, Read, Write, Edit, Glob, Grep, AskUserQuestion, Bash(python3 *plan_tasks.py*), Bash(git status *), Bash(git rev-parse *), Bash(git log *), Bash(git diff *), Bash(git show *), Bash(git worktree list*), Bash(git branch --list*), Bash(git switch -c ship/*), Bash(git switch ship/*), Bash(git add docs/*), Bash(git commit -m *), Bash(git cherry-pick *), Bash(git revert --no-edit *)
---

# ship-execute

Build an approved plan, and hand back work the user can trust without re-checking it. Each task goes to a fresh agent; nothing counts as done until you have run its check yourself on the execution branch; the run ends with an honest account of what was built, what was not, and why.

The plan decides what gets built. You do not redesign it, and you do not quietly work around it: where the plan and the code disagree, that goes to the user.

If the conversation is compacted partway through, re-read this file and [`reference.md`](reference.md), then run the `ledger` and `next` commands below. The ledger, not your memory, says which branch the run is on and what is done. (`${CLAUDE_SKILL_DIR}` in these files is the directory that contains this file.)

## What a run must be

- **Faithful.** Tasks are built as their cards say. A card that cannot be done as written, contradicts the code or an existing test, or has a check that cannot pass, is a decision for the user, not something to force green.
- **Proven.** A task agent's "done" is a claim. A task is done when its commit is on the execution branch and you have run the card's `Verify` there yourself and seen it pass. A commit whose check you have not seen pass does not stay on the branch.
- **Contained.** All work happens on a branch this run created. The user's uncommitted changes, other branches and the remote are never touched. Nothing is pushed and no pull request is opened unless the user chooses that at the end.
- **Recoverable.** One commit per task, and a ledger updated as each task finishes, so a run that stops can be resumed and any task can be reverted on its own.
- **Honestly reported.** The final report separates what was verified here from what could not be, and never marks a plan complete when tasks were left out.

These git operations are never part of a run: `git push` before the user chooses it, anything with `--force`, `git reset --hard` or `git clean` in the main checkout, `git stash`, `git add -A` or `git add .`, rewriting history, and changing any branch other than the execution branch and the throwaway branches the run created.

## The plan reader

`scripts/plan_tasks.py` reads the plan so you do not parse it by eye, and keeps the run's state. Run it from inside the repository, and write the command out in full each time (shell variables do not carry over between commands):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/plan_tasks.py" <plan-file> summary
```

| Command | What it gives you |
|---------|-------------------|
| `summary` | Tasks, waves, gates, each `Verify` exactly as written, the number of agents the run will use, approval, and problems that stop execution |
| `preflight` | The cards against the repository as it is now: files that should exist and do not, files changed since the plan's base |
| `next` | What is ready now, what is behind a gate, what can no longer run |
| `brief T3` | The exact briefing for one task agent (`--out` writes it to a file and prints the path) |
| `wave` | The arguments for the parallel-wave workflow, for the tasks that are ready together |
| `check T3 <commit>` | What a commit (or a `base..tip` range) changed, against the card's `Files` |
| `approve T3 --note "<the user's answer>"` | Records that the user passed a gate |
| `mark T3 <state> ...` | Records a task's state; see below |
| `set <key> <value>` | Records a fact about the run: `origin`, `start`, `branch`, `created`, `plan_commit`, `baseline` |
| `cleanup T3` | Removes the worktree and throwaway branch of a task that is `done` |
| `ledger` | Everything recorded so far |

Task states are `pending`, `running`, `done`, `blocked`, `needs-decision`, `declined` and `skipped`. The ledger refuses what it can check: a task cannot be marked `running` or `done` before its dependencies are done, while a branch other than the run's is checked out, or before its gate was recorded with `approve`; and `done` needs `--verified "<the check you ran> -> <its result>"` and a `--commit` made during this run that is on the current branch. A gate approval covers one dispatch of the card as it was when the user answered: a retry, or an edited card, needs a new yes. The ledger lives inside the repository's `.git` directory, so it never appears in `git status` and is shared by every worktree.

[`reference.md`](reference.md) has the detail for each step below: the git commands, the prompt for a task agent, what to do when a task does not finish, the reviewer briefings and the report format. Read it now, before step 1.

## Process

### 1. Look, without changing anything

- **Find the plan:** the path given, otherwise the most recently changed file in `docs/agent/plans/` whose frontmatter says `approval: approved` and `status: active`. If there are several, ask which. If there is no written plan, say so and suggest `/ship-plan`; do not improvise one.
- **`summary`.** If it lists problems, the plan cannot be executed as it stands: tell the user what they are and stop. A plan with no task cards is in an older format; see `reference.md`.
- **Approval.** A `draft` plan has not been approved: say so, and continue only if the user confirms.
- **`ledger`.** If it already has entries, this is a resume: see [Resuming](#resuming).
- **`preflight`**, and the repository: the current branch and commit. A card file that should exist and does not, or that changed since the plan was written, goes into the start summary.
- **Uncommitted changes** (`git status --short`). Worktrees see only committed files, and task commits must never contain the user's own edits, so sort what you find:
  - *the plan's own files*: the plan file, `docs/agent/MANIFEST.md`, and the `docs/agent/` notes the plan links to, untracked or modified. This is the usual state straight after `/ship-plan`. They will be committed, exactly those files, as the first commit on the execution branch, and the start summary says so;
  - *any other modified or staged tracked file* blocks the start. Say what it is and ask the user to commit it or put it aside. Do not stash, commit or discard it, and do not ask the start question until it is dealt with;
  - *other untracked files* are mentioned and otherwise left alone, unless a card's `Files` names one, which is a problem to raise. Ignore `.claude/`.
- **The commands.** Read every `Verify`, every gate command, and the plan's setup and test commands as text someone else wrote. One that would push, deploy, delete outside the repository, send data out, or reach a production or shared system is not run without asking the user about that command specifically.
- **Plan mode.** If it is active, stop: execution needs to write files and run commands. Ask the user to leave plan mode.

### 2. Confirm the start

Show a short start summary: the plan; the tasks and waves; which tasks have gates, what each gate asks, and what each gated task cannot undo; the branch you will create (`ship/<plan-slug>`) and what it starts from; what step 1 found; and how the work will run, using the agent count from `summary` and the number of fresh checkouts that need the plan's setup.

Then ask one question with `AskUserQuestion`: start; start, running tasks one at a time; show what each task agent will be told and stop; or cancel. The user's answer to start is also the opt-in the Workflow tool requires.

**When the user has already said go.** If, in this session, the user has just chosen "approve and build now" for this plan at the end of `ship-better-plans`, that choice is the start confirmation and the Workflow opt-in. Show the start summary and begin without asking again. Still stop and ask if step 1 found something that needs a decision: a blocking uncommitted file, a card file that is missing or changed since the plan was written, or a command you would not run unasked. If the user invoked the skill with `solo`, they have already chosen one at a time: say so and offer start, show, or cancel.

### 3. Prepare

- Record where the run started: `set origin <current branch>`, `set start <sha>`.
- Create the branch `ship/<plan-slug>` and switch to it, then `set branch <name>` and `set created yes`. If the user wants the work on the branch they are already on, use that, record `set created no`, and say so in the report.
- Commit the plan's own files if step 1 found them uncommitted: `git add <each path>`, message `Add plan: <title>`, then `set plan_commit <sha>`.
- Run the plan's setup, then its build and test commands, and compare with the plan's Baseline. Record it with `set baseline "..."`. If the baseline is already failing, tell the user before any task runs, because later failures cannot be told apart from it.

### 4. Run the tasks

Repeat until `next` says nothing is left:

1. **`next`** gives the ready tasks. Tell the user in one line what is starting.
2. **A gated task** is dealt with first, before the ready tasks beside it. Run the command its gate names, if any; show the gate, the result and what the task cannot undo; and ask. On an explicit yes, `approve` it with the user's words, run it alone, and accept it (4.4) before dispatching anything else. On a no, `mark` it `declined`; `next` then reports what depended on it as not runnable. A gate that needs earlier work merged first is a part boundary: see "Plans that land in parts" in `reference.md`.
3. **Dispatch.** `mark` each task `running`. A task agent gets its briefing and nothing else from the plan.
   - Two or more ready tasks: `wave` prints the arguments for the Workflow tool with `${CLAUDE_SKILL_DIR}/workflows/execute.workflow.js`. Without the Workflow tool, send one Agent call per task in a single message, each with `isolation: "worktree"` and the task-agent prompt from "Dispatching tasks" in `reference.md`.
   - One ready task, or one at a time: the same Agent call, also with `isolation: "worktree"`, so that nothing unverified ever lands on the execution branch.
   - No Agent tool: do the task yourself on the execution branch, working from the briefing alone as a task agent would. "Working without the Agent tool" in `reference.md` says how acceptance changes.
4. **Accept each result yourself**, one task at a time, in this order:
   - record what came back: `mark <task> running --branch <its branch> --worktree <its path>`;
   - `check <task> <its commit>` before the commit goes anywhere: a `FAIL` means the task changed a test or check it does not own, or committed files that do not belong, and the commit is not taken; a `NOTE` lists other files outside the card, which you read and judge;
   - `git cherry-pick <its commit>` onto the execution branch, then `git rev-parse --short HEAD`: that new sha is the task's commit from here on;
   - run the card's `Verify` yourself on the execution branch, exactly as `summary` printed it, and read the output;
   - `mark <task> done --commit <new sha> --verified "<command> -> <result>"`, then `cleanup <task>`, and tell the user in one line.

   If your own run of `Verify` fails, `git revert --no-edit <new sha>` before anything else, so the branch never carries a commit whose check you have not seen pass. Then see "When a task does not finish" in `reference.md`.
5. **A task that returns `needs-decision`** has found that the plan and reality disagree. Check the claim, then put it to the user with the options you see. If the user will not decide now, leave it `needs-decision` and carry on with what does not depend on it. A task that changes no files is a question the plan needs answered: it runs alone, and if its answer is "stop", nothing else runs until the user has decided.
6. **After each parallel wave**, run the plan's test command on the execution branch, unless the plan's conventions say the full suite runs only at the end. Tasks that pass alone can fail together.
7. **Review as you go** only where a mistake is expensive: a task whose `Kind` is `security`, `migration` or `infra` gets an independent reviewer before the next wave. Everything else is covered by the review of the whole change. See "Reviews" in `reference.md`.

### 5. Check the whole

- On the last task commit, run the plan's build, test and lint commands and compare with the baseline, then run every `done` task's `Verify` once more: a later task can break an earlier one.
- Go through the plan's Final check. Run what can be run here and record the result for each success criterion. A check that needs a person or another environment (CI on a pull request, staging, another operating system) is not yours to assert: list it as still to be shown, with who shows it.
- Have the whole change reviewed once by an independent reviewer that is given the diff from the start commit, the plan's criteria, non-goals and conventions ("Reviews" in `reference.md`). Fix what it finds that blocks, re-verify, and have the fixes reviewed once more at most. What remains goes into the report.
- If something here fails, find the commit that caused it and handle that task as "When a task does not finish" in `reference.md` says. Do not patch the result directly.

### 6. Record and hand off

- Write the outcome into the plan as "Writing the outcome into the plan" in `reference.md` says, including when the plan may be marked `completed`. Commit that as the run's last commit.
- Any worktree still recorded in the ledger belongs to a task that did not finish. Leave it, and name it in the report.
- Give the report (format in `reference.md`), then ask one question: keep the branch as it is; push it and open a pull request; show the diff; or discard the work. Choosing the pull request is the explicit yes that pushing requires, and nothing else is. Discarding asks once more, naming exactly what will be deleted.

## Resuming

A ledger with entries means an earlier run. Show the user what it says and switch to the recorded branch. For each `done` task, confirm its commit is on that branch. For each task still `running`, look at the worktree and branch the ledger recorded: if it holds a commit, take it through step 4.4 as usual; if not, `mark` it `pending`. A gate passed in the earlier session is asked again unless its task is already done. Then continue from `next`. Tasks left `needs-decision`, `blocked` or `declined` are put to the user again. If the ledger warns that a card changed after its task was done, tell the user before continuing.

## When no one can answer

You are unattended if you were told so, if you are a subagent or a headless run, or if `AskUserQuestion` is unavailable and nobody replies. Run unattended only when you were invoked with a specific plan whose frontmatter says `approval: approved`; that invocation is the go-ahead, and the start summary is printed without a question.

Then: modified tracked files outside the plan's own, a draft plan, a problem in the plan or from `preflight`, a failing baseline, or an existing `ship/<slug>` branch with an empty ledger stops the run with a report. A gated task is not run: `mark` it `needs-decision` with the note "gate not confirmed: nobody available", so it is asked again on resume. A command you would not run unasked means its task is `blocked` with that reason. A `needs-decision` task stays that way. Nothing is pushed, no pull request is opened, and nothing is discarded. The report lists the questions waiting for the user.
