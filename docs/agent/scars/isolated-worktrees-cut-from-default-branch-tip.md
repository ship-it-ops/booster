---
type: scar
status: active
created: 2026-10-22
updated: 2026-10-22
summary: A worktree subagent (Workflow or Agent tool) starts at the tip of the branch origin/HEAD points at, or at HEAD with no remote; move its throwaway branch to the commit you need or the task cannot start
paths: [skills/ship-execute/workflows/*, skills/ship-execute/reference.md]
---

# Isolated worktrees are cut from the default branch tip, not the current checkout

## What happened

In the executor's first live run (2026-10-22) the orchestrator created `ship/<plan>` from `be2ee2b`, committed the plan (`4c407ea`) and dispatched a three-task wave through `execute.workflow.js`. All three agents reported a worktree at `be2ee2b`: the tip of the clone's default branch, which was also the commit checked out when the session began. In the second run the execution branch was based on a side commit (`5cfea8b` off `be2ee2b`) while the default branch had moved to `c2ebbcb`, and every worktree, whether the Workflow tool's or the Agent tool's, started at `c2ebbcb`: the default branch tip, not the checked-out commit and not the session's first commit. A fast-forward could not reach `5cfea8b` from there, so the agents stopped and the orchestrator cut worktrees from `5cfea8b` by hand, after which the wave ran in parallel. In a throwaway repository with no remote, an Agent-tool worktree started at the current HEAD of a fresh branch. The rule that fits all three: the harness cuts from the branch `origin/HEAD` points at when there is a remote, otherwise from HEAD.

## Tripwire

If a worktree agent reports a start commit that is not the one you dispatched from, the cause is the harness, not git. The executor's task-agent prompt now moves the throwaway branch (`git reset --hard <sha>`, only in a clean worktree whose branch name starts with `worktree-`) and blocks only if that fails. Never move anything in the main checkout to compensate.

## Why it hurt

The parallel path, the executor's main reason to exist, silently became sequential in the first run, and the second run needed the orchestrator to improvise worktrees. Both runs completed correctly because every agent refused to work from the wrong commit; that refusal is what to keep.

## Don't do this

Do not assume an isolated worktree starts at HEAD, in any workflow that dispatches isolated agents: check `git rev-parse --short HEAD` in the worktree before relying on committed state, and do not write a hand-off that says worktrees start at the checked-out commit.
