# ship-better-plans — review reference

Detail for step 7 of `SKILL.md` (running the review, reading its result, dealing with findings, rechecking) and for revising an existing plan.

## Contents

- [Review](#review)
- [Revising a plan](#revising-a-plan)

---

## Review

### Reviewers

| Key | Lens | Runs |
|-----|------|------|
| `executor` | Could a fresh agent execute each card cold? Do the tasks add up to the success criteria? | always |
| `grounding` | Does the plan match the repository, and what did it miss? | always |
| `adversary` | Premortem: unchecked assumptions, uncovered inputs, steps with no way back, broken intermediate states, a wrong approach | always |
| `scope` | Does the plan do what was asked, no less and no more? What can be cut? | always |
| `security` | New or changed attack surface without stated protection | when the plan calls for it |
| `data` | Migration order, compatibility during rollout, backfill, recovery | when the plan calls for it |
| `ops` | Deploy, gating, rollback, monitoring, CI and configuration changes | when the plan calls for it |
| `tests` | Would each check fail if the requirement were not met? | when the plan calls for it |
| `coldread` | The executor's read plus a spot-check of the claims the approach rests on | the light review |
| `revision` | Damage done by edits made under review | the recheck |

The prompts live in the `REVIEWERS` table of `workflows/audit.workflow.js`. That file is the single source for them. The four core reviewers always run. Leave `reviewers` out of the arguments and the script reads the plan and picks the extra lenses itself, which keeps the choice out of the author's hands; pass a list of extra keys only when the user asked for a specific lens.

### Cost

Reviewers read the plan and explore the repository, so each agent costs about as much as a small research task. As a guide, two measured full reviews of plans of 300 to 380 lines in a mid-sized repository used 11 and 12 agents, 1.1 and 1.4 million subagent tokens (mostly reading), and 12 and 14 minutes.

| Depth | Agents |
|-------|--------|
| Light | 1 |
| Full (`standard`) | 1 to choose lenses, 4 to 8 reviewers, 1 to merge, then one verifier per blocker or major finding, capped at `maxVerify` (default 12). Typically 10 to 20. |
| Ultra | Up to three rounds of the above (it stops early when a round confirms nothing serious, or confirms a blocker), plus a recheck after each revision. Typically 20 to 50. |
| Recheck | One per prior finding, plus one reviewer and the verifiers for what it raises. Typically about 5. |

Tell the user these counts when you offer the choice.

### Running the review

Call the Workflow tool with `scriptPath` pointing at `workflows/audit.workflow.js` in this skill's directory, and `args` as an object (not a string):

```json
{
  "planPath": "/abs/path/to/the/plan.md",
  "repoRoot": "/abs/path/to/the/repo",
  "request": "the user's original request, verbatim",
  "mode": "standard",
  "notes": "Choices the user already made that reviewers should not relitigate."
}
```

`mode` is `light`, `standard` (the full review), `ultra` or `recheck`. Reviewers read the plan file themselves, so the text they review is exactly the text on disk; `planText` exists only for the case where there is no file. `request` lets the scope reviewer compare the plan with what the user actually asked for. Keep `notes` factual and short: it is for decisions the user made, not for arguing the plan's case.

### Without the Workflow tool

Read the `REVIEWERS` table and the `reviewPrompt` function in the script, and send the same prompts as parallel Agent calls in one message: one `coldread` call for a light review, the four core lenses (plus any the plan clearly calls for) for a full one. When they return, merge duplicates yourself, then check each blocker or major finding against the plan and the code before accepting it: confirm it, refute it with evidence, or mark it disputed. Say in the plan's Audit section that verification was done by the planner, not independently.

With neither the Workflow tool nor the Agent tool, read the plan yourself through the `executor` lens and against "How plans go wrong" in `reference-cards.md`, and record in the Audit section that no independent review ran.

### Reading the result

| Field | Meaning | What to do |
|-------|---------|------------|
| `confirmed` | A second agent checked the finding and agrees. `basis` says whether the failure was demonstrated from the plan or code, or is plausible but not shown. `verifierEvidence` often narrows the reviewer's claim, and `betterFix` may improve on the proposed fix. | Every one gets a disposition |
| `disputed` | The verifier could not settle it, two verifiers disagreed, or verification failed to run | Look yourself; if still unsure and it matters, ask the user |
| `unverified` | Serious findings nobody verified: everything in a light review, and anything beyond `maxVerify`. `unverifiedBlockers` counts the blockers among them. | Check each against the plan and code yourself, then give it a disposition |
| `minor` | Not verified | Apply the ones that are cheap and clearly right |
| `dropped` | Refuted, with the reason | Skim; if a refutation looks wrong, treat the finding as disputed |
| `duplicates` | Findings in later rounds that repeated earlier ones | Nothing |
| `failedReviewers`, `incomplete` | Lenses that returned nothing | Coverage is incomplete: re-run, or tell the user what was not reviewed |
| `stoppedEarly` | `blocker` (a round confirmed a blocker; revise before spending more rounds), `maxRounds`, `budget`, or `reviewers-failed` | Act on it and say so in the Audit section |
| `resolved`, `unresolved` | Recheck only: the state of each prior finding | Fix what is unresolved |
| `selected` | The extra lenses the script chose, with reasons | Record them in the Audit section |
| `next` | One sentence from the script on what this result needs from you | Follow it |
| `error` | The arguments were wrong; nothing was reviewed | Fix the call. Never record this as a clean review |

The result can be long. Its full text is in the output file the completion notice names.

### Dealing with findings

Sort the confirmed, disputed and unverified findings:

- **Apply directly:** factual corrections, wrong paths, missing edge cases, a card that cannot run cold, a missing dependency.
- **Take to the user:** anything that changes scope, the approach or a success criterion, and any blocker you would rather accept than fix. That the user chose the approach on your recommendation is not a reason to reject a finding against it; they chose without this evidence, so bring it to them.
- **Reject with a reason:** the finding contradicts a non-goal or a constraint, or you checked it against the code and it is wrong. Record the evidence.

When two findings pull in opposite directions (one says add, one says cut), the success criteria and non-goals decide. A blocker against the approach reopens step 3: redesign, tell the user what changed, then redo the specification and cards that depended on it instead of patching around it.

After editing, make the plan consistent again. A changed approach leaves old terms behind in requirements, cards and the summary; search for them. Then re-run the linter and `--dag`.

Record the outcome in the plan's Audit section: depth, reviewers, counts, each confirmed finding with its disposition, and anything not covered.

### Recheck

`SKILL.md` step 7 says when a recheck is due. To run one, call the script on the revised plan with `"mode": "recheck"` and `"prior"` set to the findings you acted on:

```json
{
  "planPath": "/abs/path/to/the/plan.md",
  "repoRoot": "/abs/path/to/the/repo",
  "mode": "recheck",
  "prior": [
    { "id": "executor-r1-2", "title": "T3 and T4 both edit src/http/app.ts and can run in parallel", "detail": "…", "resolution": "Mounting moved entirely into T4; T3 no longer lists app.ts" }
  ]
}
```

It checks that each prior finding is resolved and has one reviewer read the revised plan cold for damage the edits caused. Fix anything it returns as `unresolved` or newly `confirmed`. A full review rechecks once; ultra may recheck a second time. After that, stop and show the user what remains: a plan that will not converge has a design problem that more review rounds will not fix.

If the approach itself changed, a recheck is too narrow: tell the user why and run the review once more at the chosen depth. The same applies when ultra stops with `stoppedEarly: "blocker"`; it stopped so the remaining rounds are spent on the plan that will ship. A second approach-level blocker goes to the user, not to another run.

---

## Revising a plan

When a plan for this work already exists in `docs/agent/plans/` and has not been executed:

1. Read it, and ask what changed if the user has not said.
2. Check its `base` against the current commit. If the files its cards name have changed, re-run discovery for those files before trusting its facts.
3. Edit the affected sections and cards in place, bump `updated`, set `approval: draft` until the user approves the revision, and note the revision under Status with the date and the reason.
4. Re-run the linter. Review again only if the approach, the scope or a success criterion moved.

In plan mode, make the same edits in the plan-mode file and save over the existing plan after approval.

For a plan that is partly executed, corrections discovered during execution are written back the same way, so the plan stays the record of what was built; lint it with `--revising`, which accepts files marked `(new)` that now exist. Once a plan is completed, further work gets a new plan that links to it.
