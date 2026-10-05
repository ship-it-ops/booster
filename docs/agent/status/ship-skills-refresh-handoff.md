---
type: status
status: active
created: 2026-10-04
updated: 2026-10-04
author: claude-opus-5-5
branch: ship-better-plans-v2
agent: claude-code-session-2026-10-01
tags: [handoff, skills-refresh, ship-family, evaluation]
importance: core
---

# Hand-off: refreshing the `ship-*` skills, one at a time (3 of 12 done)

## Scope

The user is refreshing every skill in this repository for current models and the current Claude Code harness, one skill at a time, all on the branch `ship-better-plans-v2`. Each refresh is a full audit and rewrite judged by several independent agent personas.

**Done on this branch** (the first two are pushed; `ship-reviewed-prs` is committed locally and not pushed):

| Skill | Version | Decision note | Evidence |
|-------|---------|---------------|----------|
| `ship-better-plans` | 2.0.0 | [ship-better-plans-v2-refresh](../decisions/ship-better-plans-v2-refresh.md) | [ship-better-plans-refresh-audit](../investigations/ship-better-plans-refresh-audit.md) |
| `ship-execute` | 2.0.0 | [ship-execute-v2-refresh](../decisions/ship-execute-v2-refresh.md) | [ship-execute-refresh-audit](../investigations/ship-execute-refresh-audit.md) |
| `ship-reviewed-prs` | 1.4.0 | [ship-reviewed-prs-refresh](../decisions/ship-reviewed-prs-refresh.md) | [ship-reviewed-prs-refresh-audit](../investigations/ship-reviewed-prs-refresh-audit.md) |

**Not started** (suggested order, most connected first):

1. `ship-agent-context` — owns the `docs/agent/` conventions both rewritten skills write into. Its plan template (Goal / Approach / Files to Touch) is older than the `plan_format: 2` plans; reconcile them.
2. The review rubrics that `ship-execute`'s reviewers and `ship-reviewed-prs` load for depth: `ship-clean-code`, `ship-tested-code`, `ship-secure-code`, `ship-devops`, then `ship-debugged-code`. `ship-reviewed-prs` now uses them as catalogues and ignores their finding codes, severity tiers and output format; several still say "severity is mechanical from the finding ID" and describe being delegated to by a persona. Reconcile that.
3. `ship-vuln-scan`, `ship-vuln-fix`.
4. `obsidian-knowledge-graph`.

**No pull request has been opened.** The user said to wait. Do not open one without being asked.

## Why

The user's request, in their words: "A lot of improvements have been made to AI LLMs in general and we need to give these skills a full refresh ... do a full audit with what you know now and all the advanced approaches that are tested and proven to work well ... evaluate this via multiple agent personas to ensure that we are always putting together the optimal execution plan." Then: "we will tackle them one skill at a time", continuing on the same branch.

## The method that worked (repeat it per skill)

1. **Read the skill and its decision notes** under `docs/agent/decisions/`. Record which earlier user decisions you keep and which you revise, and tell the user about every revision.
2. **Snapshot the current skill** somewhere outside the repo, then **audit it with six independent reviewers**, one lens each, who do not see each other's conclusions. Lenses used so far: prompt engineering for current models; a cold-start walkthrough as the agent following the skill (interactive, plan mode, headless); the downstream consumer of the skill's output; a staff engineer on the method; a red team (audit harness, or agent safety); daily developer experience. Give reviewers the facts about the environment they cannot know (see "Facts" below). Ask for evidence with file and line, a severity, and a "keep" list so they do not invent problems.
3. **Run the current skill on real work as a baseline**, judged by agents that did not do the work. For a planner: have it plan two real scenarios in this repo, then score each plan with a cold-read executor and a grounding checker. For an executor: have it execute a real plan and a deliberately flawed one in scratch clones, then have a judge inspect the repository against the agent's report. For a reviewer skill, the equivalent is diffs with known, seeded defects.
4. **Rewrite**, then re-run the same reviewers and the same scenarios. Fix. Run a smaller third round (three reviewers plus the scenarios) on the final text. Fix what is cheap and clearly right; record what you did not fix.
5. **Test live whatever the evaluation agents could not exercise** (see the tool limits below).
6. **Put mechanical checks in a script with unit tests and a CI job**, not in a prose self-check. Both rewritten skills ship one: `skills/ship-better-plans/scripts/lint_plan.py` and `skills/ship-execute/scripts/plan_tasks.py`.
7. **Write a decision note and an investigation note**, index them in `MANIFEST.md`, update `CHANGELOG.md`, bump versions in the plugin's `plugin.json` and in `.claude-plugin/marketplace.json` (the validator requires them to match), and run all checks.

For a skill that drives an external tool, build a stand-in for that tool that validates what it is sent the way the real service does and logs every call; judges then score against the log, not the agent's account. `ship-reviewed-prs` ships one for `gh` (`skills/ship-reviewed-prs/tests/fake_gh.py`) with three fixture pull requests (`tests/build_fixtures.py`).

The evaluation harness from the refreshes is saved in [`../references/refresh-eval/`](../references/refresh-eval/): the three workflow scripts (reviewer prompts, scenario prompts, judge prompts and schemas), the fixture setup script, and the toy repository with its deliberately flawed plan. The scripts contain absolute paths to the previous session's scratch directory; replace `SCRATCH` and the fixture paths before running them.

## Facts the next agent needs

- **Checks that must pass before committing:**

  ```bash
  python3 scripts/validate-skills.py
  python3 scripts/check-skill-links.py
  npx --yes markdownlint-cli2
  python3 -m unittest discover -s skills/ship-better-plans/tests
  python3 -m unittest discover -s skills/ship-execute/tests
  python3 -m unittest discover -s skills/ship-reviewed-prs/tests
  ```

- **Layout:** the source of truth is `skills/<name>/`. `plugins/<name>/skills/<name>/` holds one symlink per top-level entry of the skill directory; adding or removing a file or directory in a skill means adding or removing its symlink, or the validator fails. Commands live in `plugins/<name>/commands/`.
- **Tool names today:** `Agent` (not `Task`), no `TodoWrite`, `AskUserQuestion` takes up to four questions per call, `Skill` loads another skill, `Workflow` runs multi-agent scripts and is not available in headless runs. `allowed-tools` pre-approves; it does not restrict.
- **Evaluation agents spawned by a workflow had no `Agent`, `Workflow` or `AskUserQuestion` tool.** They did every task themselves and answered questions from text supplied in the prompt. So an evaluation of this kind cannot exercise parallel dispatch, independent review or interactive questions. Say so in the write-up and test those paths live.
- **Worktree isolation**, as probed: an isolated agent gets a worktree under `.claude/worktrees/` on a throwaway branch cut from the commit checked out in the main checkout, with tracked files only. If it commits, the worktree and branch persist and must be removed. While they exist, `.claude/` shows as untracked.
- **Do not edit a file while a running reviewer is reading it.** Draft in a scratch directory until the reviewers finish. This nearly contaminated the first audit.
- **zsh does not word-split unquoted variables**, and shell variables do not persist between Bash tool calls. Write commands out in full in skill text.
- **A full reviewer-plus-scenario round costs roughly 0.9 to 1.6 million subagent tokens (1.5, 1.3 and 1.0 million for the three `ship-reviewed-prs` rounds).** Three rounds per skill was the pattern.

## Open items on the finished skills

- Neither skill has been run end to end in a live interactive session: the checkpoint and approval questions in `ship-better-plans`, and the start, gate and hand-off questions, real subagent dispatch and resume in `ship-execute`. A good first act for the next session is to plan and execute one small real change with both skills and fix what that shows.
- `ship-better-plans`: grounding did not improve without a review; the last reviewer round's remaining majors are listed in its investigation note.
- `ship-execute`: three red-team requests were not done (listing and pattern-flagging every command a plan will run, an `--allow` override for `check`, rebuilding a lost ledger from the plan's Status section); see its investigation note.
- `ship-reviewed-prs`: nothing has run against GitHub itself. The first real pull request through this repository's `pr-review.yml` is the test of the result file reaching the check step, thread resolving and review dismissal with the workflow token, and the bot login match. The user chose a minor version (1.4.0), not 2.0.0: do not bump a skill to a new major version in this refresh without asking first. They confirmed that the bot's approvals should count as approvals (unattended approval stays the default). They have not yet commented on the other revisions to their earlier decisions (listed in its decision note). The red team's remaining requests are listed in its investigation note.
- A session's permission check can block an evaluation agent's write even to a simulated service; say in the agent's prompt that the service is a simulation and the write is expected.
- The marketplace `metadata.version` is 1.5.0 after the three refreshes.

## Standing instructions from the user

- Commit messages carry no Claude attribution of any kind: no `Co-Authored-By`, no `Claude-Session` link. See [no-claude-attribution-in-commits](../instructions/no-claude-attribution-in-commits.md). Ask before adding attribution to a pull request description.
- Do not push or open a pull request without being asked. Pushes of this branch have been approved one at a time.
- One skill at a time, all on `ship-better-plans-v2`.
- In `ship-execute`, the user's "approve and build now" at the end of `ship-better-plans` counts as the start confirmation (decided 2026-10-04).

## Done when

`docs/agent/decisions/` on the default branch contains a `<skill>-v2-refresh.md` note (or an explicit decision not to refresh) for every skill listed under "Not started". Check with `git ls-tree -r --name-only origin/main docs/agent/decisions/ | grep refresh`. Until then this entry is current; update the table above as each skill lands.
