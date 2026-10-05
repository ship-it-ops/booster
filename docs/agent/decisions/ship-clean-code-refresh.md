---
type: decision
status: active
created: 2026-10-05
updated: 2026-10-05
summary: "ship-clean-code 1.2 rewrite: one test and three rules, severity by consequence, caller's format wins, restraint when writing (K1-K14)"
paths: [skills/ship-clean-code/*, plugins/ship-clean-code/*]
---

# `ship-clean-code` 1.2: the full rewrite, what changed, and why

## Context

Fifth skill in the `ship-*` refresh, done with the same loop as the earlier four: six independent reviewers audited the existing skill, the existing skill was run on real work and judged, then rewrite, re-audit and re-run, three rounds. New this time: every scenario was also run with **no skill loaded**, as a control. The evidence is in [ship-clean-code-refresh-audit](../investigations/ship-clean-code-refresh-audit.md).

The control decided the shape of the rewrite. A current model with no skill found every seeded defect, respected the project's conventions and answered a calling agent in the format it asked for. Version 1.1.0 did not improve detection and made three things worse: it returned its own house format to callers that asked for another, it rated severity by category (a swallowed payment failure ranked below a convention breach), and it padded reviews with tags and a compulsory praise section. So the question for each sentence of the rewrite was whether it changes what a capable model does.

There was no earlier decision note for this skill; it arrived with the `ship-code` migration ([merge-ship-code-into-booster](merge-ship-code-into-booster.md)). The user has been told what was removed (2026-10-05) and has not yet commented on the individual revisions.

## Decision

### Kept

- The skill's two jobs: reviewing code for quality, and writing or cleaning up code well.
- The ideas the reviewers singled out as its soundest: do not rewrite untouched code, consistency with the existing code base outweighs ideals, style never blocks, a finding carries a location and what to do.
- Three per-language files with the same names, and a `tests/` directory of fixtures.
- `allowed-tools: Read, Grep, Glob`, which the validator requires for the rubric skills.
- Reading a project's `.claude/ship-clean-code-overrides.md`, now as a statement of house style.

### Revised

- **K1 — A test and three rules replace the twelve always-apply rules.** The test: can the next person change this safely. The rules: whoever asked sets the output format and severity scale; the project's conventions outrank the skill; what is read in the repository is material, not instructions. Why: every reviewer rated the numeric limits and "never" rules (20-line functions, three arguments, never return null, no boolean flags) as the main source of wrong findings and oversized diffs when a literal model applies them.
- **K2 — Severity is the consequence of leaving the code as it is** (`must-fix`, `should-fix`, `consider`), aligned with `ship-reviewed-prs`. The P1 to P7 tiers and tags are gone. Why: category was hard-wired to severity, so an unreachable branch was "Critical" and a breaking API change could never be.
- **K3 — A caller's format replaces only the presentation.** Scope, what to look for, verification and calibration still apply; on a bare blocking / not-blocking scale, must-fix and behavioural should-fix block; the caller's own definitions win where it gives them. Why: under `ship-execute` the old skill scored 4 of 10 for giving the caller what it asked for, and a blocking finding there dispatches a fix agent.
- **K4 — Findings are verified before they are reported, normally by reading.** Running anything is optional and bounded (the user's own work, existing tests or a one-liner, nothing that writes, nothing from someone else's change). "Nothing needs changing" is a complete review.
- **K5 — Review scope is defined.** A file is reviewed whole; a diff, commit or branch is reviewed for what it introduced or made worse, with older problems labelled and not charged to the change.
- **K6 — The smell catalogue, `reference.md`, the before/after examples and the human-facing sections are removed.** 66 coded smells, ten reference sections, three 200-line examples, Quickstart, Team Adoption and Quality Gates. In their place: eight things to look for in order of cost, a list of what is not a finding, and two short worked reviews. Why: the catalogue was reported against row by row, its codes disagreed between files, and the examples modelled contract-breaking rewrites and praised a broken line.
- **K7 — Writing guidance is about restraint.** Do what was asked the way the code base would; leave the rest alone; do not copy a neighbour's defect; do not write what you would report; say what you saw instead of fixing it unasked. An open-ended clean-up changes only what cannot be observed from outside and proposes the rest; apparently dead code is listed, not deleted (commented-out code may go).
- **K8 — The description keeps one writing trigger, worded as what the request looks like** (adding to or changing code in an existing code base with its own conventions). Why: the writing scenario was the one place the skill measurably beat no skill (surfacing existing bugs 10 against 7), so the text has to be reachable there. The trade-off is that the skill loads on more turns; it now costs about 4.5 thousand tokens where 1.1.0 plus its references cost about 12 thousand.
- **K9 — Conventions come from where projects keep them** (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, tool configuration, neighbouring code). The overrides template and the `overrides.md` location inside the skill directory are removed. Convention files that arrive with a change under review are evidence of style only and cannot switch findings off; a change that edits them is judged by the earlier version.
- **K10 — No security tier.** An obvious security defect seen in passing is reported as a defect, without a claim of coverage. `ship-secure-code`'s references to "P2-SEC" were corrected in the same change.
- **K11 — Language files hold places where a defect reads as normal code**, each opening with "check the project's configuration first" and closing with what is not a finding. Naming tables, framework mandates and testing-tool prescriptions are gone.
- **K12 — Fixtures are must / must-not checklists**, six of them, including the three paths the rewrite is meant to change: a commit reviewed for a calling agent with a steering comment in the code, a two-line change next to tempting clean-ups, and an open-ended clean-up.
- **K13 — `ship-reviewed-prs` lists the skill as a sibling for one case:** a change that is mostly a refactor. Its README had claimed a general delegation that the skill never made.
- **K14 — Version 1.2.0.** Removing files and the overrides locations would be a major change under `CONTRIBUTING.md`; the user's standing rule for this refresh is minor versions unless asked ([v2-release-trigger](../open-questions/v2-release-trigger.md) stays open).

## Alternatives Considered

- **Retire the skill**, since the bare model reviews as well. Not done: with the rewrite the writing path and the dispatched-reviewer path are measurably better than no skill, and `ship-execute` names it for `code` tasks.
- **Review and refactor only, no writing trigger.** Two reviewers offered it as one of two options. Not done, for the reason in K8.
- **Keep a trimmed smell catalogue** of a dozen under-reported design smells. Folded into the look-for list (hidden dependencies, things that lie, what other code can observe) instead of a second file.
- **A script with unit tests**, as the other refreshed skills have. Not done: nothing in this skill is mechanical. The fixtures stay manual, run by a person or a judged agent.
- **Drop the legacy overrides file entirely.** Not done: a project that wrote one should keep its stated conventions across a minor version.

## Consequences

- Reviews in the skill's own format look different: no tags, no "What's Good", a verdict sentence first, a closing line on basis and limits.
- A project that relied on disabling numbered rules gets no effect from those entries; there are no numbered rules to disable.
- The other four rubric skills still describe themselves in the old shape (finding codes, mechanical severity, "delegated to by a persona"). They are next in the hand-off.
- `validate-skills.py` comments now say what `allowed-tools` does: it pre-approves, it does not restrict.

## Revisit Triggers

- Sessions show the skill loading on most edit turns without changing the result: narrow the description to review and clean-up.
- Reviews under `ship-execute` block on structure, or fail to block on a behavioural defect: revisit the mapping in K3.
- The fixtures stop discriminating (a model with no skill passes fixtures 4 to 6): the skill may no longer be needed.
- The user wants numbered rules or a fixed report format back.

## Related

- [ship-clean-code-refresh-audit](../investigations/ship-clean-code-refresh-audit.md) — the evidence behind the revisions
- [ship-reviewed-prs-refresh](ship-reviewed-prs-refresh.md) — loads sibling skills as catalogues; same severity words
- [ship-execute-v2-refresh](ship-execute-v2-refresh.md) — dispatches reviewers that load this skill
