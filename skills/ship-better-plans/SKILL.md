---
name: ship-better-plans
description: >
  Use when the user asks for an implementation plan, spec or design before
  building, or is about to start development work where a vague or wrong plan
  would be costly: a new feature, a refactor across several files, a
  migration, an integration, or anything touching data, auth or a public
  interface. Writes a plan grounded in the actual codebase, reviewed before
  approval, that `ship-execute` can build. Also runs on `/ship-plan` (start
  the arguments with `ultra` for the deepest review), and works inside Claude
  Code plan mode. Not for trivial or single-file changes, quick questions,
  debugging one known bug, or executing an existing plan (use
  `ship-execute`). Do not start when another planning skill is already under
  way in the session, such as a `superpowers` brainstorming or writing-plans
  run.
allowed-tools: Read, Glob, Grep, Agent, Workflow, AskUserQuestion, ExitPlanMode, Write(docs/agent/**), Edit(docs/agent/**), Bash(mkdir -p docs/agent/*), Bash(python3 *lint_plan.py*), Bash(git rev-parse *), Bash(git status *), Bash(git log *), Bash(git branch *)
---

# ship-better-plans

Produce an implementation plan that survives execution. The plan is finished when a fresh agent could carry out every task without asking a question, every claim it relies on about the existing code was checked against the code, and it has been reviewed at the depth the user chose.

This skill plans and stops. The plan is saved under `docs/agent/plans/` so later sessions inherit it, and the user decides when to build it, normally with `ship-execute`.

If the conversation is compacted partway through, re-read the plan file and the reference file for the step you are on before continuing.

## What the plan must be

The process below exists to produce these five properties. Where a step does not fit the work at hand, serve the property rather than the step.

- **Grounded.** A plan written from what a codebase probably looks like fails at the first task. Every claim about existing code that the plan depends on is a fact with evidence from this session: a `path:line` you opened, or a command you ran and what it printed. The parts of existing files that a task will change were read. Anything not checked is listed as an assumption, with what settles it.
- **Aligned.** A well-executed plan for the wrong goal is the most expensive failure. The success criteria are checkable, and the user has confirmed them and the approach before the detailed work starts.
- **Decided.** The approach was chosen from real candidates, judged against the success criteria and constraints, with the deciding factor named. An option invented only to be rejected teaches nothing; when one approach is the only viable one, the plan says which constraint rules out the rest.
- **Executable cold.** A task agent receives its card, the plan's "Conventions for every task" block, and the text of each id the card lists under Covers. Nothing else. From that alone it must be able to do the work and prove it is done.
- **Verified.** Every requirement has an acceptance criterion with a check that would fail if the requirement were not met, the plan passes the linter, and the review's findings have been dealt with.

**Size the plan to the work**, judging the size after discovery. For small work (about four tasks or fewer, easy to undo, no data, auth or public interface) read the files yourself instead of dispatching subagents, expect one viable approach and one risk, skip separate requirements and let acceptance criteria verify the success criteria directly, write `N/A — reason` in the sections that do not apply, and recommend a light review. A migration or anything hard to undo gets everything. Do not pad a section to look thorough, because the executor cannot tell filler from requirement.

## Before starting

- **Is a plan warranted?** For a one-file change, a quick question or a single known bug, say that a written plan is not needed and proceed as you would without this skill. If the user asked for a plan in so many words, write one, sized to the work.
- **Did the user ask for a plan?** If this skill started on its own, say in one sentence that you are planning first and why. The user can tell you to just build it. In an unattended run, do not turn a request to build something into a plan-only run: use this skill there only when a plan was asked for.
- **Is it one plan?** If the request contains parts that could each ship and be useful alone, propose the split, plan the first part, and list the others as follow-on plans. A single feature that spans layers is one plan. The user can decline the split.
- **Does a plan for this already exist?** Look in `docs/agent/plans/`. A plan that has not been executed is revised in place (`reference-review.md`, "Revising a plan"). Work that follows a completed plan gets a new plan that links to the old one.
- **Plan mode.** If Claude Code plan mode is active, the repository stays untouched until the user approves. See [Plan mode](#plan-mode).
- **No one to ask.** You are running unattended if you were told so, if the user asked you to plan without questions, or if you are a subagent or a headless run. If `AskUserQuestion` is unavailable and you cannot tell whether anyone is there, treat the run as unattended too: a draft with stated assumptions, and your questions at the top of the final message, serves both cases. See [When no one can answer](#when-no-one-can-answer).
- **Other missing tools.** Without the Agent tool, do the reading yourself. Without the Workflow tool, review through the fallback in `reference-review.md`. With neither, review the plan yourself against the `executor` lens and "How plans go wrong", and say in the Audit section that no independent review ran.

## Process

Three reference files hold the detail. Read each when you reach the steps it covers: [`reference-planning.md`](reference-planning.md) for steps 2 to 5; [`reference-cards.md`](reference-cards.md) before you write the specification and the cards, starting with its "How plans go wrong"; [`reference-review.md`](reference-review.md) for step 7 and for revising a plan.

### 1. Frame

From the request alone, draft the brief: the problem (what is observably wrong or missing, with no solution in it), why it matters now if the user said, success criteria, non-goals, constraints. Mark each item as stated by the user, inferred, or unknown. Ask nothing yet, because the repository answers many of these better than the user can.

### 2. Discover

Read before designing. For a large area or several independent questions, send read-only subagents in parallel (the Agent tool, `Explore` type where available), one per question. Find:

- the code the work touches: entry points, callers, types, and the patterns neighbouring code follows
- what already exists that the plan should reuse instead of rebuilding
- how this repository builds, tests and lints, what a fresh checkout needs first, and where the tests for this area live
- how a change reaches the main branch here: CI jobs and what triggers them, required checks and reviews
- `AGENTS.md` / `CLAUDE.md`, and `docs/agent/` when it exists: standing instructions, work in flight, and the decisions, scars and patterns that bear on this area. Search those notes for the names of the things you are changing; index summaries miss details.
- the current branch and commit

Subagent summaries tell you where to look; they are not evidence. Open the files the design will hinge on yourself. Settle cheap questions with read-only commands (a search, `--help`, listing tests). Outside plan mode, when the build and test commands are safe to run here, run them once (the tests for the area, or the whole suite if it is quick) and record the result as the baseline; otherwise record that they were not run. Use what you learn to settle the unknowns from step 1. Whatever is still unknown becomes a question for the user or a stated assumption.

### 3. Design

Lay out the approaches a senior engineer who knows this repository would actually consider: usually two or three, sometimes one. For each, say how it meets each success criterion, its relative effort, its main risk, how reversible it is, and what existing code it builds on. Pick one and name the deciding factor.

Then run a premortem on your pick: suppose it shipped and failed, and name the most likely reasons, up to three. Each one changes the design, or becomes a risk with something that handles it and a way to notice it.

Unless the work is small, have the pick challenged before you build on it: give one subagent the brief, the facts and your approach, and ask for the strongest case that it is the wrong approach for this repository and for the best alternative. When the design space is wide, or the user asked for `ultra` up front, get three independent proposals instead (`reference-planning.md`, "Design"). An approach-level problem found now costs minutes; found after the cards are written, it costs the plan.

### 4. Checkpoint

This is normally the only stop before approval. Put everything that needs the user in one message: the brief (marking what you inferred), what discovery established, and the approach you recommend with the alternatives and the deciding factor. If this skill started on its own, add that they can tell you to build from this brief without a written plan. Then make one `AskUserQuestion` call. It takes up to four questions; use them in this order of priority:

1. the success criteria, if any of them was inferred and not stated
2. the approach, when there is a real choice, with your recommendation first
3. anything still open that the repository could not answer and that would change the plan
4. the review depth for step 7, unless the user already chose it (see [Review depth](#review-depth))

If more than four things would change the design, make a second call instead of guessing. Questions that would not change the design become assumptions with defaults the user can correct when they see the plan. If the goal itself is still unclear after discovery, ask about the goal first, before step 3, and hold this checkpoint as well.

After the checkpoint the success criteria and the approach are settled. If later work shows either was wrong, say so and come back to the user; do not change them quietly.

### 5. Specify

Start the plan file now, from [`templates/plan.md`](templates/plan.md), with `approval: draft`, and keep it current from here on so the work survives a long session (see [Where the plan lives](#where-the-plan-lives)). The files in [`examples/`](examples/) show the form and level of detail for a small, a mid-sized and a high-risk plan; read the one closest to your work, and take nothing from it but the form.

- **Requirements** (`FR-n`): atomic, each traced to a success criterion. A mitigation, rollback mechanism or migration step that needs code is a requirement too. A small plan may skip them.
- **Acceptance criteria** (`AC-n`): each names the requirement or success criterion it verifies and a concrete check: a command, a named test, or what to observe. A new check or gate must be shown failing on a bad case, not only passing on a good one.
- **Non-functional targets**: only those that apply, each with a number and where the number came from.
- **Interfaces and data shapes**: inputs, outputs and errors for every boundary the work adds or changes.
- **Edge cases**: go through empty, maximum, malformed, concurrent, partial failure, permission denied, and retried or duplicated input. Each one that applies gets an expected behaviour and the criterion or task that covers it, or is ruled out of scope with a reason. An expected behaviour that rests on how existing code behaves is a claim about the codebase: check it or list it as an assumption.
- **Verification**: setup for a fresh checkout, the build, test and lint commands with their baseline, and a final check that shows each success criterion met, naming who runs anything that needs a person or a special environment.

### 6. Sequence

Break the work into task cards. A card names its files, carries the context needed to do the work, and ends in a command that proves it. Rules that apply to every task (setup, commit message style, banned dependencies) go once in "Conventions for every task". When a requirement is delivered by more than one card, each card's `Do` says which part is its own. Order the cards so that:

- the riskiest unknown is tested first: a spike task settles an assumption before the work that depends on it begins
- a contract (interface, schema, type) lands before the tasks on either side of it, which is what makes parallel work safe
- the pieces are joined as early as the work allows, so integration problems surface while they are cheap
- every task leaves the repository building with its tests passing, so it can be verified and reverted on its own
- anything that is not safely reversible (a destructive migration, deleting data, removing a public API) comes late and carries a `Gate`: what a person confirms before it runs
- two tasks that touch the same file, or need the same exclusive resource (a port, a database, a migration sequence), are linked by a dependency, because an executor runs unlinked tasks at the same time

Tasks describe changes to the repository. The executor commits each task's work, and branching, pushing and opening pull requests need the user's say-so, so do not write cards for them. If the work must land in more than one pull request, say so in the Approach section and put a `Gate` on the first task of each later part.

Generate the execution order from the cards instead of drawing it by hand, and paste the output into the plan:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/lint_plan.py" <plan-file> --dag
```

### 7. Check

1. **Lint.** First write "Review pending" in the Audit section and the draft state in Status, so the linter does not report them empty. `python3 "${CLAUDE_SKILL_DIR}/scripts/lint_plan.py" <plan-file> --repo <repo-root>` checks structure, leftover placeholders, traceability from success criteria down to tasks, the dependency graph and pasted execution order, tasks that would collide in parallel, gates on tasks that are not safely reversible, and that the files, evidence and scripts the plan cites exist. Fix every error. Fix every warning, or note in the Audit section why it does not apply. Without `python3`, do the same checks by hand from the list in `reference-cards.md`.
2. **Review**, at the depth the user chose. Call the Workflow tool with `scriptPath` set to `${CLAUDE_SKILL_DIR}/workflows/audit.workflow.js` and `args` of `{ planPath, repoRoot, request, mode }`, where `mode` is `light`, `standard` (the full review) or `ultra`. The user's choice of depth is the opt-in that tool requires. `reference-review.md` covers the other arguments, reading the result, and what to do when the Workflow tool is unavailable.
3. **Deal with every finding** the result lists as `confirmed`, `disputed` or `unverified`. A light review returns all of its serious findings as `unverified`: check each against the plan and the code yourself. Every finding ends one of three ways, recorded in the plan's Audit section: the plan changed, the user accepted the risk, or you rejected it with evidence. A finding that changes scope, the approach or a success criterion goes to the user, even when the user chose that approach on your recommendation. A blocker against the approach sends you back to step 3. Record what the review did not cover.
4. **Lint again, then recheck in proportion to what you changed.**

   | What changed after the review | What to do |
   |-------------------------------|------------|
   | Facts, paths or wording only | Nothing more. |
   | A requirement or a card, after a full or ultra review | Run the script with `mode: "recheck"`, so an agent other than you reads the plan that will ship. Full: once. Ultra: a second time if the first still finds something. |
   | A requirement or a card, after a light review | Re-read the changed cards yourself. Offer a recheck, with its cost, if the change was structural. |
   | The approach | Tell the user why, then run the review once more at the chosen depth. |

   A second blocker against the approach, or a recheck that still finds problems after its allowed runs, goes to the user with what remains. Do not start further runs on your own.

### 8. Approve and save

Present the plan for approval in one message: the summary, the decisions the user should look at, the assumptions still open, what the review changed, and where the plan is saved. A plan with a blocking open question is not ready; settle the question, or make settling it the first task with a gate. Ask one question with three choices:

- approve and build now: `/ship-execute docs/agent/plans/<slug>.md` (add `solo` to run tasks one at a time). This choice also counts as `ship-execute`'s start confirmation, so say that the build will begin without a second question. If `ship-execute` is not installed, offer to build it in this session card by card, and mention the plugin once.
- approve and stop here
- revise

On approval, set `approval: approved` in the frontmatter, update the Status section, and write the remaining artifacts (see [What gets written](#what-gets-written)). Do not start building unless the user chose that.

## Review depth

The review is the part of this skill that spends real tokens, so the user chooses, once, at the checkpoint. Offer four options, recommend one for this plan's size and risk, and say how many agents each means:

- **None:** the linter only.
- **Light:** one cold-read reviewer; nothing is independently verified. One agent. Recommend for small, reversible work.
- **Full:** four reviewers always (`executor`, `grounding`, `adversary`, `scope`) plus `security`, `data`, `ops` or `tests` where the plan's content calls for them, then a second agent checks each blocker or major finding. About 10 to 20 agents, plus about 5 for a recheck when findings change the plan. Recommend for most plans.
- **Ultra:** the full review repeated until a round finds nothing serious (at most three rounds), then rechecks of the revised plan. Typically 20 to 50 agents. Recommend when the work is hard to reverse, touches live data, or has a wide blast radius.

An explicit `/ship-plan ultra` is the user's choice already made; say what will run and proceed.

## Plan mode

Plan mode forbids writing to the repository, which suits planning: steps 1 to 7 only read. Keep the working plan in plan mode's own plan file and pass that path to the linter and the review. (If the session gives you no plan file, keep the plan in the conversation, pass it to the review as `planText`, and lint once it is saved.)

Approval in plan mode can clear the conversation, so the plan file must carry its own next steps. Put this block directly under the title, filled in, and remove it from the saved copy:

```text
After approval (do this first, do not start implementing):
1. Save this plan to docs/agent/plans/<slug>.md without this block. Set `approval: approved` and update the Status section.
2. Run `python3 <absolute path of lint_plan.py> docs/agent/plans/<slug>.md --repo .` and fix what it reports.
3. If docs/agent/MANIFEST.md exists, add or update this plan's entry, and write the decision and open-question notes the plan lists under Related.
4. Tell the user where the plan is, then ask: build now with /ship-execute docs/agent/plans/<slug>.md, or stop here.
For approval, look at: <decisions to check> · <assumptions still open> · <what the review changed>
```

Then call `ExitPlanMode` to ask for approval. It replaces the approval question in step 8.

## Where the plan lives

Outside plan mode, write the plan to `docs/agent/plans/<slug>.md` at step 5, where the slug is a short kebab-case form of the title. Its frontmatter says `approval: draft`, which tells any executor not to build it, and its `docs/agent/MANIFEST.md` entry (when that file exists) starts with "DRAFT". Edit the file in place as the plan develops. In plan mode, the plan-mode file plays that role until approval.

## What gets written

- the plan → `docs/agent/plans/<slug>.md`
- a decision that outlives this plan and that a future agent would otherwise reopen → `docs/agent/decisions/<slug>.md`
- an open question that outlives the session → `docs/agent/open-questions/<slug>.md`
- an entry for each in `docs/agent/MANIFEST.md`

Templates are in [`templates/`](templates/) and follow the `ship-agent-context` conventions. If the user gives a standing instruction while planning ("always", "never", "from now on"), record it under `docs/agent/instructions/`; a constraint on this one task is not a standing instruction.

If the repository has no `docs/agent/`, create `docs/agent/plans/` and save only the plan there, keeping decisions and open questions as sections inside it. Tell the user where it went, and mention once that `ship-agent-context` can maintain the rest.

## When no one can answer

Do not stall and do not invent the user's answers. Skip the checkpoint and the approval question. Take the best-evidenced default for each open item and record it under assumptions with what would settle it. Run a review only if the invocation asked for one. Finish with the written plan, still `approval: draft`, its Status section naming the unconfirmed assumptions, and a final message that lists them and the next steps the user can take.
