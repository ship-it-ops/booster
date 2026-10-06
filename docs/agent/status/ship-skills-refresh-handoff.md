---
type: status
status: active
created: 2026-10-04
updated: 2026-10-05
author: claude-opus-5-5
branch: ship-better-plans-v2
agent: claude-code-session-2026-10-01
tags: [handoff, skills-refresh, ship-family, evaluation]
importance: core
summary: "Skills refresh: 7 of 12 done, ship-devops stopped after round 2; the method, what the user asked for, and what is next"
done_when: manual
---

# Hand-off: refreshing the `ship-*` skills, one at a time (7 of 12 done, `ship-devops` in progress)

## Scope

The user is refreshing every skill in this repository for current models and the current Claude Code harness, one skill at a time, all on the branch `ship-better-plans-v2`. Each refresh is a full audit and rewrite judged by several independent agent personas.

**Done on this branch** (check `git status -sb` for what is pushed):

| Skill | Version | Decision note | Evidence |
|-------|---------|---------------|----------|
| `ship-better-plans` | 2.0.0 | [ship-better-plans-v2-refresh](../decisions/ship-better-plans-v2-refresh.md) | [ship-better-plans-refresh-audit](../investigations/ship-better-plans-refresh-audit.md) |
| `ship-execute` | 2.0.0 | [ship-execute-v2-refresh](../decisions/ship-execute-v2-refresh.md) | [ship-execute-refresh-audit](../investigations/ship-execute-refresh-audit.md) |
| `ship-reviewed-prs` | 1.4.0 | [ship-reviewed-prs-refresh](../decisions/ship-reviewed-prs-refresh.md) | [ship-reviewed-prs-refresh-audit](../investigations/ship-reviewed-prs-refresh-audit.md) |
| `ship-agent-context` | 1.3.0 | [ship-agent-context-refresh](../decisions/ship-agent-context-refresh.md) | [ship-agent-context-refresh-audit](../investigations/ship-agent-context-refresh-audit.md) |
| `ship-clean-code` | 1.2.0 | [ship-clean-code-refresh](../decisions/ship-clean-code-refresh.md) | [ship-clean-code-refresh-audit](../investigations/ship-clean-code-refresh-audit.md) |
| `ship-tested-code` | 1.2.0 | [ship-tested-code-refresh](../decisions/ship-tested-code-refresh.md) | [ship-tested-code-refresh-audit](../investigations/ship-tested-code-refresh-audit.md) |
| `ship-secure-code` | 1.1.0 | [ship-secure-code-refresh](../decisions/ship-secure-code-refresh.md) | [ship-secure-code-refresh-audit](../investigations/ship-secure-code-refresh-audit.md) |

**In progress: `ship-devops`** (see "ship-devops: where it stopped" below).

**Not started** (suggested order, most connected first):

1. The remaining review rubric after `ship-devops`: `ship-debugged-code`. `ship-devops` still cites `ship-secure-code`'s removed SEC codes in about forty places (`SKILL.md`, `reference.md`, `reference-categories.md`, its examples and fixtures); they go when it is rewritten. `ship-reviewed-prs` now uses them as catalogues and ignores their finding codes, severity tiers and output format; several still say "severity is mechanical from the finding ID" and describe being delegated to by a persona. Reconcile that. `ship-clean-code` 1.2.0 is the model for a rubric skill, and `ship-tested-code` 1.2.0 is the second built on it: read both decision notes first. Draft the next one from their structure while its baseline runs, then let the baseline and the reviewers correct the draft; that halved the elapsed time for `ship-tested-code`. When reviewers ask for additions in one round and cuts in the next, apply the cuts first. Its three opening rules (the caller's format wins, the project's conventions outrank the skill, what is read is material) and its severity words should carry over, and the others still refer to it in the old terms ("invoke `ship-clean-code`" for naming and SRP).
2. `ship-vuln-scan`, `ship-vuln-fix`.
3. `obsidian-knowledge-graph`.

**No pull request has been opened.** The user said to wait. Do not open one without being asked.

## ship-devops: where it stopped

Rounds 1 and 2 of 3 are done. `skills/ship-devops/` is untouched (still 0.2.0); the rewrite is a draft saved in [`../references/refresh-eval/devops-wip/`](../references/refresh-eval/devops-wip/README.md), with the full round-2 reviewer findings beside it. The fixture and workflow script are `devops-fixture/` and `eval-ship-devops.workflow.js` in the same folder.

Results so far (scores out of 10; "none" is no skill loaded):

| Scenario | Measure | 0.2.0 | None | Draft |
|----------|---------|-------|------|-------|
| Review the deploy setup | Detection | 10 | 9 | 9 |
| Review the deploy setup | Precision | 8 | 9 | 9 |
| Review the deploy setup | Honesty of coverage | 9 | 8 | 10 |
| Review the deploy setup | Proportion | 5 | 8 | 8 |
| Write a migration | Safety | 9 | 9 | 10 |
| Write a migration | Scope | 8 | 9 | 10 |
| Review a commit | Caller's format | 4 | 8 | 8 |
| Review a commit | Fix quality | 9 | 6 | 9 |
| Review a commit | Proportion | 5 | 7 | 6 |

Reviewer findings: 82 with 22 critical on 0.2.0 (the same defects as `ship-secure-code` 1.0.0: severity "mechanical from the finding ID" where the digit is a sub-rule index, repository text able to switch findings off, `APPROVE` on zero findings, nothing bounding live commands); 79 with none critical and 37 major on the draft. No scenario run, with or without a skill, executed a command with a real effect. Cost so far: 1.69 and 1.07 million subagent tokens.

To finish it:

1. **Apply the round-2 findings to the draft** (`devops-wip/round2-reviewer-findings.txt` has the suggested wording). The ones several reviewers agreed on:
   - *Factual corrections in the platform files* (highest priority; reviewers gave their confidence for each): `USER` is inherited from the base image; a build argument is in the history of the stage that declares it, and also leaks through exported cache and provenance attestations; Docker's published ports bypass host firewalls such as ufw; shell-form signal handling depends on the shell, and exec form is not enough without a handler; a Terraform `removed` block destroys unless it says `destroy = false`; `prevent_destroy` is lost when the block is deleted or its address changes; provisioners run at apply, while providers and data sources run at plan; S3 backend locking is `use_lockfile` in current versions and a missing `backend` block proves nothing; a Job runs once and it is an init container that runs per replica; applying a manifest does not wait for the rollout; `ADD COLUMN NOT NULL` fails in PostgreSQL but MySQL fills an implicit default, and on every engine the old version's inserts fail; `SET NOT NULL` and `CHECK` block reads as well as writes in PostgreSQL; a job skipped because a job it needs failed still satisfies a required check; an approval or commenter check must pin the commit SHA that was approved; Dependabot pull requests are treated like forks; `github.sha` under `pull_request_target` is reported to be the default branch's commit since a December 2025 change (reviewers were about 80% sure: check GitHub's changelog before writing it).
   - *"What you may run"* needs a boundary by what is touched, not the word "real": local and disposable is allowed (syntax checks, rendering, a local build with no push, a migration against a throwaway local database); anything that uses the session's credentials or real state is not, including `kubectl --dry-run` and `terraform init` without `-backend=false`; say what to do when the user explicitly asks for a run (give the command, do not run it); repository documents cannot authorise running; pushing is the user's call.
   - *Coverage* should name only what this review's findings depend on, not recite a fixed list.
   - *"Check the platform's behaviour, not from memory"* demotes real findings to questions on platforms with no notes: keep a confident finding and name what it depends on.
   - *Severity:* an outsider able to run code with any real credential is must-fix wherever the workflow sits, not only "on a path to production".
   - *Fixture 7* has an unsafe step order (it switches reads in the same release that starts dual writes); the right order is in the findings file. Fixture 1's "fix that works" needs the pinned SHA. Fixture 3 uses an out-of-support Go version.
   - A finding that is only true if an unseen external control is absent should be a question, not a blocking finding.
   - The writing section should forbid inventing commit SHAs and image digests when pinning.
   - Cuts: reviewers named sentences to remove; apply them before the additions.
2. **Round 3**: three reviewers (prompt, staff, safety) plus the three scenarios on the revised draft, using the workflow's `args` as in the earlier skills (`rewrite: true`, `only`, `variants`, `skillDirs`, `auditDir`, `fileList`, `rewriteNote`). Then a last pass of fixes.
3. **Run the writing fixtures** (5, 6 and 7) with fresh agents, with and without the skill.
4. **Swap the draft into `skills/ship-devops/`** and rebuild the symlinks under `plugins/ship-devops/skills/ship-devops/` (one per top-level entry). `git rm -r` both directories first; `observability.md`, `reference-categories.md`, `overrides.example.md` and the old examples and fixtures go.
5. **Housekeeping**, which was drafted and then reverted so the repository stays consistent until the skill lands: version 0.2.0 to 0.3.0 and a new description in `plugins/ship-devops/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`; the `ship-devops` rows in `README.md` and `skills/README.md`; four mentions of `DEV3` / `DEV4` in `skills/ship-vuln-scan/SKILL.md` and `reference-categories.md`; a `CHANGELOG.md` entry.
6. **Notes**: a decision note (it revises [ship-devops-12-category-catalog](../decisions/ship-devops-12-category-catalog.md) and [in-persona-delegates-to-ship-devops](../decisions/in-persona-delegates-to-ship-devops.md): tell the user) and an investigation note, on the model of the `ship-secure-code` pair; update this file; delete `devops-wip/`.

## Why

The user's request, in their words: "A lot of improvements have been made to AI LLMs in general and we need to give these skills a full refresh ... do a full audit with what you know now and all the advanced approaches that are tested and proven to work well ... evaluate this via multiple agent personas to ensure that we are always putting together the optimal execution plan." Then: "we will tackle them one skill at a time", continuing on the same branch.

## The method that worked (repeat it per skill)

1. **Read the skill and its decision notes** under `docs/agent/decisions/`. Record which earlier user decisions you keep and which you revise, and tell the user about every revision.
2. **Snapshot the current skill** somewhere outside the repo, then **audit it with six independent reviewers**, one lens each, who do not see each other's conclusions. Lenses used so far: prompt engineering for current models; a cold-start walkthrough as the agent following the skill (interactive, plan mode, headless); the downstream consumer of the skill's output; a staff engineer on the method; a red team (audit harness, or agent safety); daily developer experience. Give reviewers the facts about the environment they cannot know (see "Facts" below). Ask for evidence with file and line, a severity, and a "keep" list so they do not invent problems.
3. **Run the current skill on real work as a baseline**, judged by agents that did not do the work. **Also run each scenario with no skill loaded.** For `ship-clean-code` that control showed the bare model reviewing at least as well as the old skill, which changed what the rewrite was for; without it the audit would have credited the skill with the model's own detection. For a planner: have it plan two real scenarios in this repo, then score each plan with a cold-read executor and a grounding checker. For an executor: have it execute a real plan and a deliberately flawed one in scratch clones, then have a judge inspect the repository against the agent's report. For a reviewer skill, the equivalent is diffs with known, seeded defects.
4. **Rewrite**, then re-run the same reviewers and the same scenarios. Fix. Run a smaller third round (three reviewers plus the scenarios) on the final text. Fix what is cheap and clearly right; record what you did not fix.
5. **Test live whatever the evaluation agents could not exercise** (see the tool limits below).
6. **Put mechanical checks in a script with unit tests and a CI job**, not in a prose self-check. Both rewritten skills ship one: `skills/ship-better-plans/scripts/lint_plan.py` and `skills/ship-execute/scripts/plan_tasks.py`.
7. **Write a decision note and an investigation note**, index them in `MANIFEST.md`, update `CHANGELOG.md`, bump versions in the plugin's `plugin.json` and in `.claude-plugin/marketplace.json` (the validator requires them to match), and run all checks.

For a skill that drives an external tool, build a stand-in for that tool that validates what it is sent the way the real service does and logs every call; judges then score against the log, not the agent's account. `ship-reviewed-prs` ships one for `gh` (`skills/ship-reviewed-prs/tests/fake_gh.py`) with three fixture pull requests (`tests/build_fixtures.py`).

The evaluation harness from the refreshes is saved in [`../references/refresh-eval/`](../references/refresh-eval/): the eight workflow scripts (reviewer prompts, scenario prompts, judge prompts and schemas), the fixture setup script, the toy repository with its deliberately flawed plan, and `clean-code-fixture/` (a small Python library with seeded defects, decoys and ground truth, built into three repositories by its `build.sh`; reusable for the other rubric skills by seeding different defects). `tested-code-fixture/` adds a seeded test file, a test commit and its own ground truth on top of the same library (`build.sh <clean-code-fixture/base> <out>`). `devops-fixture/` is a small Node service with a pipeline, Dockerfile, manifests, Terraform and a migration, with seeded operational defects. `secure-code-fixture/` is a separate small Flask service with seeded vulnerabilities, decoys, a feature commit and ground truth (read, not run). `eval-ship-clean-code.workflow.js`, `eval-ship-tested-code.workflow.js` and `eval-ship-secure-code.workflow.js` take `args` for the variant, the skill directory and which reviewers to run, so one script served all three rounds. The scripts contain absolute paths to the previous session's scratch directory; replace `SCRATCH` and the fixture paths before running them.

## Facts the next agent needs

- **Checks that must pass before committing:**

  ```bash
  python3 scripts/validate-skills.py
  python3 scripts/check-skill-links.py
  npx --yes markdownlint-cli2
  python3 -m unittest discover -s skills/ship-better-plans/tests
  python3 -m unittest discover -s skills/ship-execute/tests
  python3 -m unittest discover -s skills/ship-reviewed-prs/tests
  python3 -m unittest discover -s skills/ship-agent-context/tests
  python3 skills/ship-agent-context/scripts/agent_context.py check
  ```

- **Layout:** the source of truth is `skills/<name>/`. `plugins/<name>/skills/<name>/` holds one symlink per top-level entry of the skill directory; adding or removing a file or directory in a skill means adding or removing its symlink, or the validator fails. Commands live in `plugins/<name>/commands/`.
- **Tool names today:** `Agent` (not `Task`), no `TodoWrite`, `AskUserQuestion` takes up to four questions per call, `Skill` loads another skill, `Workflow` runs multi-agent scripts and is not available in headless runs. `allowed-tools` pre-approves; it does not restrict.
- **Evaluation agents spawned by a workflow had no `Agent`, `Workflow` or `AskUserQuestion` tool.** They did every task themselves and answered questions from text supplied in the prompt. So an evaluation of this kind cannot exercise parallel dispatch, independent review or interactive questions. Say so in the write-up and test those paths live.
- **Worktree isolation**, as probed: an isolated agent gets a worktree under `.claude/worktrees/` on a throwaway branch cut from the commit checked out in the main checkout, with tracked files only. If it commits, the worktree and branch persist and must be removed. While they exist, `.claude/` shows as untracked.
- **Do not edit a file while a running reviewer is reading it.** Draft in a scratch directory until the reviewers finish. This nearly contaminated the first audit.
- **zsh does not word-split unquoted variables**, and shell variables do not persist between Bash tool calls. Write commands out in full in skill text.
- **A shell command that runs `rm -rf` on a path built from a variable is blocked by the harness** and cannot be approved in an unattended session. Write fixture scripts that refuse to overwrite instead of deleting.
- **A full reviewer-plus-scenario round costs roughly 0.7 to 1.6 million subagent tokens (1.5, 1.3 and 1.0 million for the three `ship-reviewed-prs` rounds; 1.1, 1.1 and 0.8 for `ship-agent-context`; 1.4, 0.9 and 0.7 for `ship-clean-code`; 1.5, 1.0 and 0.7 for `ship-tested-code`; 1.7, 1.1 and 0.7 for `ship-secure-code`).** Three rounds per skill was the pattern.

## Open items on the finished skills

- Neither skill has been run end to end in a live interactive session: the checkpoint and approval questions in `ship-better-plans`, and the start, gate and hand-off questions, real subagent dispatch and resume in `ship-execute`. A good first act for the next session is to plan and execute one small real change with both skills and fix what that shows.
- `ship-better-plans`: grounding did not improve without a review; the last reviewer round's remaining majors are listed in its investigation note.
- `ship-execute`: three red-team requests were not done (listing and pattern-flagging every command a plan will run, an `--allow` override for `check`, rebuilding a lost ledger from the plan's Status section); see its investigation note.
- `ship-reviewed-prs`: nothing has run against GitHub itself. The first real pull request through this repository's `pr-review.yml` is the test of the result file reaching the check step, thread resolving and review dismissal with the workflow token, and the bot login match. The user chose a minor version (1.4.0), not 2.0.0: do not bump a skill to a new major version in this refresh without asking first. They confirmed that the bot's approvals should count as approvals (unattended approval stays the default). They have not yet commented on the other revisions to their earlier decisions (listed in its decision note). The red team's remaining requests are listed in its investigation note.
- `ship-agent-context`: nothing has run through an installed plugin yet (the hook's `${CLAUDE_PLUGIN_ROOT}` path, the digest after compaction). The user has not yet commented on its revisions to their earlier decisions, chiefly that hand-offs are reconciled when relied on instead of at every session start. `docs/agent/` in this repository is now maintained with the skill's script: create notes with `new`, never edit `MANIFEST.md` by hand, and run `check` before committing. `ship-better-plans`' own note templates still lack a `summary:` line.
- `ship-clean-code`: nothing has run through an installed plugin, so whether the new description triggers on ordinary feature work is untested; the last round of fixes was not re-audited beyond three fixture runs; the user has been told what was removed and has not yet commented. What is still weak is listed in its investigation note.
- `ship-tested-code`: the same two gaps as `ship-clean-code` (no run through an installed plugin; last fixes not re-audited). Its scenarios never provoked the failure the skill most exists to prevent (bending a test or the code to get to green), so those rules rest on reviewers' judgement; a harder fixture is listed in its investigation note. Its `SKILL.md` is about 3,900 words. The user has been told what was removed and has not yet commented.
- `ship-secure-code`: no measured gain over no skill; the refresh's value is removing a version that was unsafe (see its investigation note). A commit review with it is longer than without, because older vulnerabilities are always reported; the last tightening of that rule was not re-run. Its reference and language files state framework and version behaviour that will go stale. The user has been told what was removed and has not yet commented.
- A fake credential in a fixture can trip the host's secret scanning on push. Use a shape no scanner recognises (an invented prefix, or a body with characters a real key cannot contain).
- The opening rules of `ship-clean-code`, `ship-tested-code` and `ship-secure-code` are near-identical on purpose. A change to one should be considered for the other.
- A session's permission check can block an evaluation agent's write even to a simulated service; say in the agent's prompt that the service is a simulation and the write is expected.
- The marketplace `metadata.version` is 1.5.0 after the three refreshes.

## What the user has asked for

The standing rules are in `instructions/`, where every session's digest shows them: [no-claude-attribution-in-commits](../instructions/no-claude-attribution-in-commits.md) and [no-push-or-pull-request-without-being-asked](../instructions/no-push-or-pull-request-without-being-asked.md).

For this piece of work specifically:

- One skill at a time, all on `ship-better-plans-v2`. No pull request has been opened; the user said to wait.
- Commits and pushes of this branch for this refresh work no longer need asking first. On 2026-10-05 the user said: "Go ahead and commit/push at different check points no need to wait". This covers pushing `ship-better-plans-v2` as each skill lands; it does not cover opening a pull request, and it is not a general change to the standing rule in `instructions/`.
- Version bumps are minor. The user turned down 2.0.0 for `ship-reviewed-prs` on 2026-10-04 ("No v2 yet - just a minor versionbump is enough"); ask before proposing a major version for any skill.
- The bot's approvals in `ship-reviewed-prs` are meant to count as approvals (confirmed 2026-10-04).
- In `ship-execute`, the user's "approve and build now" at the end of `ship-better-plans` counts as the start confirmation (decided 2026-10-04).

## Done when

This work spans several pull requests, so it is closed by hand (`done_when: manual`): it is finished when `docs/agent/decisions/` on the default branch has a `<skill>-refresh.md` note (or an explicit decision not to refresh) for every skill listed under "Not started". Check with `git ls-tree -r --name-only origin/main docs/agent/decisions/ | grep refresh`. Until then this note is current; update the table above as each skill lands.
