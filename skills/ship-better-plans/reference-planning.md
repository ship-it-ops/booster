# ship-better-plans — planning reference

Detail for steps 2 to 5 of `SKILL.md`: discovery, design, the checkpoint and the specification.

## Contents

- [Discovery](#discovery)
- [Design](#design)
- [The checkpoint](#the-checkpoint)
- [Specification](#specification)

---

## Discovery

The aim is a short list of facts the plan can stand on, each with evidence. By the end of discovery you should be able to write down:

| What | Why the plan needs it |
|------|-----------------------|
| The files and symbols the work touches, and who calls them | Task cards name exact files; callers reveal blast radius |
| Existing code to reuse (helpers, patterns, a similar feature) | The cheapest correct plan usually extends something that exists |
| What a fresh checkout needs (install, env files, services) and the build, typecheck, test and lint commands, with where they are defined | Task agents start in fresh checkouts; every `Verify` uses these commands verbatim |
| The baseline: what those commands report today | Tells the executor which failures are not theirs, and proves the commands work |
| Where tests for this area live and how they are set up | Tasks say which test file to add to and which fixtures to use |
| How a change reaches the main branch: CI jobs, triggers, required checks and reviews, branch rules | "Done" often depends on a gate nobody mentioned |
| Rules in `AGENTS.md` / `CLAUDE.md` | They become entries in "Conventions for every task" |
| `docs/agent/`: instructions, status, relevant decisions, scars, patterns | Prior decisions bind the design; scars name traps; status shows work in flight |
| Branch and short commit (`git rev-parse --abbrev-ref HEAD`, `git rev-parse --short HEAD`) | Recorded as `base:` so an executor can tell if the code moved |

If the repository has no `docs/agent/`, skip those lookups without comment. If the session already loaded its index (the `ship-agent-context` hook does this at session start), do not re-read the index; do search the notes for the names of the files and concepts you are changing, because a one-line summary rarely shows that a note applies.

**Briefing subagents.** For a small area, read it yourself. Dispatch subagents when the area is large or there are several independent questions. Give each one a single question, say what you already know, and ask for paths with line numbers. For example: "In this repo, find how HTTP middleware is registered and ordered, and every place the auth context is read. Return file paths with line numbers and the two or three lines that matter at each. Read-only." Send them in one message so they run together.

**Evidence.** A subagent's summary tells you where to look. Before a fact goes into the plan, open the file and confirm the line. Read the parts of each file a task will change and the interfaces it relies on, and the whole file when it is short. A fact about behaviour is best settled by running something: write it as `ran: <command> → <what it printed>`. For a library or external API, check the installed source or its documentation, or record the claim as an assumption.

**Running things.** Searches, `--help` and listing tests are always fine. Run the build and the tests only when they are self-contained and safe here, and never in plan mode. Scope the run to the area you are changing unless the whole suite is quick. If you could not run them, write "not run" as the baseline so the executor knows the commands are unverified.

**A dirty working tree.** `base` records a commit. If files the plan touches have uncommitted changes, say so in a fact, plan against what is on disk, and give the first task a `Gate` confirming the tree is in the state the plan assumes.

**Assumptions.** After discovery, sort every unknown from the brief:

| The unknown | What to do |
|-------------|------------|
| The repository answers it | It becomes a fact with evidence |
| Only the user can answer it and it changes the plan | Ask at the checkpoint |
| It can only be settled by trying something | Make it the first task (a spike) with a stated outcome for each result |
| It barely matters | Take a default and record it as an assumption |

An assumption that the plan's approach depends on is never left as an open question on an approved plan. It is checked, asked, or made the first gated task.

---

## Design

**Real candidates.** A candidate is something a senior engineer on this codebase would seriously propose and that could meet the success criteria. "Do nothing" and "rewrite everything" are rarely candidates. An option that cannot meet a success criterion is not a row in the table; note it in one line as ruled out. Two honest options beat three padded ones, and a single option is fine when the constraints leave only one.

**Comparing.** Judge each candidate against the success criteria and constraints from the brief, in words. Effort is relative (S/M/L against each other), not hours. Numeric scores look rigorous and are not: nothing anchors a 3 against a 4. The comparison has done its job when you can name the one factor that decides it.

**Premortem.** For the chosen approach: "It is three months later and this failed. What happened?" Write the most plausible stories, up to three, and stop when the next one is a stretch. A small change may have one. Each story either changes the design or becomes a row in the risk table that points at the task, check or decision that handles it.

**Challenging the pick.** Send one subagent the brief, the facts and the chosen approach with: "Make the strongest case that this is the wrong approach for this repository, check your case against the code, and describe the best alternative. If the approach holds up, say so." Weigh what comes back yourself. This is the cheapest point at which to find an approach-level problem.

**Independent proposals** (a wide design space, or `ultra` requested up front). Dispatch three subagents in one message. Each gets the same brief and facts, and one mandate:

1. The smallest change that meets every success criterion.
2. The lowest-risk route: most reversible, smallest blast radius.
3. The best long-term structure, accepting more work now.

Ask each for an approach in under a page: what changes, what it reuses, the main risk, the first three tasks. Compare them yourself; do not average them. Take the strongest and adopt specific ideas from the others where they improve it.

---

## The checkpoint

One message, then one question call. The message is the brief the user is agreeing to:

```text
Here is what I plan to build and how.

Problem: …
Success criteria: SC-1 … (you said this) · SC-2 … (my inference)
Not doing: …
Constraints: …
What I found: the three or four facts that shaped the design, with paths
Approach: A, because <deciding factor>. Considered B (rejected: …).
Assumptions I am making: …
```

Then `AskUserQuestion` with up to four questions, in the priority order `SKILL.md` gives. A good question is about a decision, offers two to four concrete options with what each one leads to, and puts the recommended option first. Do not ask for facts the repository holds, for permission to continue, or for anything whose answer would not change the plan. If more than four things would change the design, make a second call; do not demote a design-changing question to an assumption to fit the first.

Carry the answers into the plan: each success criterion is marked stated, confirmed or assumed, and each choice the user made is recorded where it applies.

If the user's request already stated the success criteria, there is no real choice of approach and nothing is open, the only question is review depth. If the user already chose that too, state the brief and continue.

---

## Specification

**Requirements.** A requirement is atomic when it can pass or fail on its own. "Validate and store the upload" is two. Anything the risk table promises (a feature flag, a circuit breaker, an alert, a backfill) is a requirement with a task, or it will not get built.

**Acceptance criteria.** For each criterion ask: would this check fail if the requirement were not met? "Tests pass" fails that test; "request 601 from tenant A returns 429 while tenant B returns 200" passes it. Prefer a command that exits non-zero on failure. Where a human has to look, say exactly what they should see. When the work builds a check, a gate or an alarm, one criterion shows it firing on a bad case.

**Numbers.** A numeric target says where the number came from: the user, a measured baseline, or an assumption. Without a source, write "no target given".

**Edge cases.** Walk the list (empty, maximum, malformed, concurrent, partial failure, permission denied, retried or duplicated) against each interface. Drop the ones that cannot occur. Each remaining case names its expected behaviour and the criterion or task that covers it. Saying "out of scope because …" is a valid entry; silence is not. When the expected behaviour depends on what existing code does with that input, try it before you write it down.

**Final check.** The last line of the Verification section shows each success criterion met once all tasks are done. If a criterion can only be shown in an environment the task agents do not have (staging, another operating system, production data), name who shows it and when.
