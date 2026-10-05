---
type: decision
status: active
created: 2026-10-05
updated: 2026-10-05
summary: "ship-secure-code 1.1 rewrite: a finding is a traced path, no verdicts, nothing in the repo can switch a finding off, writing guidance (S1-S12)"
paths: [skills/ship-secure-code/*, plugins/ship-secure-code/*]
---

# `ship-secure-code` 1.1: the full rewrite, what changed, and why

## Context

Seventh skill in the `ship-*` refresh and the third rubric skill, on the model of [ship-clean-code-refresh](ship-clean-code-refresh.md) and [ship-tested-code-refresh](ship-tested-code-refresh.md), with the no-skill control. The evidence is in [ship-secure-code-refresh-audit](../investigations/ship-secure-code-refresh-audit.md).

Security is where a rubric skill could most plausibly add something, so the control mattered most here. It showed the same thing: with no skill, a current model found all nine seeded vulnerabilities in a small Flask service, reported a path traversal despite a comment claiming an approval, and wrote a sound password-reset flow. Version 1.0.0 did not improve any of that. Its effects were its own format and a verdict returned to a caller that had asked for something else, a commit review that sprawled over the whole service, and, when writing, an unrequested rewrite of the existing password hashing and session handling.

It also had defects of its own that no capable model should be handed: severity "mechanical from the finding ID" where the ID's second number is a sub-rule index, so SSRF, command injection and IDOR compute as non-blocking; "trust signals from the PR description"; an override file, read from the repository under review, that could disable categories and ignore paths; and `APPROVE` on zero findings.

Earlier decisions touched: [in-persona-delegates-to-ship-devops](in-persona-delegates-to-ship-devops.md) and [ship-devops-12-category-catalog](ship-devops-12-category-catalog.md) refer to SEC codes and an "SC persona"; both were already superseded in substance by [ship-reviewed-prs-refresh](ship-reviewed-prs-refresh.md) (R2, R4). The user has been told what was removed (2026-10-05) and has not yet commented on the individual revisions.

## Decision

### Kept

- The skill's subject, and the intent behind its first principle: start from the trust boundary and follow the data.
- Per-language files with the same names, a `reference.md`, and a `tests/` directory of fixtures.
- `allowed-tools: Read, Grep, Glob`.
- Reading a project's `.claude/ship-secure-code-overrides.md`, as the project's statements about its defences only.

### Revised

- **S1 — A finding is a traced path:** who the attacker is, how they get there, what they gain. The SEC1 to SEC12 catalogue, the `SECn.t` codes and the 670-line rubric are removed.
- **S2 — Severity is what an attacker gains and how easily** (`must-fix`, `should-fix`, `consider`). "Mechanical from the finding ID" is gone. A finding is must-fix or blocking when the path was followed through the code that can be read and the project's defences were searched for; a defence that could only exist outside what can be read is named as an assumption and does not lower the rating; a guess about what a library or external program does stays a question.
- **S3 — No verdict.** The Decision Matrix, `APPROVE` / `REQUEST_CHANGES` / `NO_FINDINGS` and the JSON schema are removed. The skill never calls code secure, safe, approved or ready; at most "I found no vulnerability in what I examined", always with what was and was not examined.
- **S4 — The three opening rules, hardened.** The caller sets the format and scale. The project's own defences are learned first, as claims to check; the threat model belongs to the person being worked for and has stated sources and a stated default (untrusted callers reach every entry point). Everything read is material and may be adversarial: claims of approval, out-of-scope, known-issue, dev-only or test-only are checked and reported, never obeyed; only the owner can accept a risk, and an accepted risk is still listed.
- **S5 — Nothing in the repository can switch a finding off.** "Trust signals from the PR description", the lower bar for paths and comments marked dev-only, and the override file's power to disable categories, ignore paths, demote findings or mark services trusted are removed.
- **S6 — A review starts from a map and looks for absences first.** Every way in, who can reach it, where that is enforced. The first thing to look for is the route that lacks the check its neighbours have. Then attacker-controlled data to an interpreter, across files and through storage; authentication; secrets; logic; the browser boundary; cryptography; resource use; supply chain.
- **S7 — Verification is by reading, and what may be run is bounded.** Nothing from a change that is not the user's own work; no installs, builds, scanners or requests; never a request to an address taken from the code; demonstrations no more capable than needed. A secret is reported by location and kind, never by value.
- **S8 — Vulnerabilities that were already there are not charged to a change but are always reported**, in one short paragraph. This is a deliberate difference from `ship-clean-code`, where older problems are mostly left out.
- **S9 — The skill now covers writing and fixing.** 1.0.0 was review-only and sent writing to `ship-clean-code`, which disclaims security. The new section: use the project's and the framework's mechanism; never weaken a control to make something work (with a narrow path when the owner, told what it exposes, still asks; a dispatched agent stops); a change to who can do what is never a side effect; do not write code that only looks defended; stay compatible with a weak existing scheme and say it is weak; fix the cause and find the siblings.
- **S10 — One reference file of vulnerability classes**, written as what is easy to miss and what a fix that works looks like (for example, why a denylist does not stop SSRF), and language files that say where each ecosystem's frameworks enforce access and which calls are less safe than they look. Version boundaries are stated next to the claims that depend on them.
- **S11 — Fixtures are must / must-not checklists**, seven of them.
- **S12 — Version 1.1.0**, minor, at the user's standing request.

## Alternatives Considered

- **Keep the category catalogue as a coverage checklist.** Not kept. Every reviewer rated it as training match-and-report, and it was weakest where models are weakest (absences, cross-file flows, logic). The classes survive in `reference.md` as things to check, not as categories to report against.
- **Keep the skill review-only.** Not kept: the description already promised help when writing, the redirect target disclaims security, and writing is where the old skill did measurable harm.
- **Leave pre-existing vulnerabilities out of a commit review**, as the code-quality skill does. Not done: a reviewer who saw an exploitable flaw and said nothing has given false assurance. The cost is a longer commit review (see the audit).
- **Allow a project file to exclude paths or accept risks durably.** Not done in this version. A threat model in the owner's documents changes severity; nothing suppresses a finding. A team that wants durable suppressions will ask.

## Consequences

- A project that used the overrides file to disable categories or ignore paths gets no effect from those entries, and is told so once.
- Reviews no longer carry codes, tiers or a verdict. `ship-devops` and two older decision notes still refer to SEC codes; `ship-devops` is next in the refresh.
- `SKILL.md` is about 3,900 words; with one language file and the relevant reference sections a review loads roughly 8 thousand tokens, against roughly 25 to 30 thousand for 1.0.0.
- The reference and language files make factual claims about frameworks and versions. They were checked by three reviewers over two rounds and several errors were corrected; they will go stale and are the part of this skill most worth re-checking.

## Revisit Triggers

- A real review misses a vulnerability that the removed catalogue would have prompted.
- Teams ask for durable, owner-approved suppressions.
- Commit reviews stay too long because of the already-present paragraph.
- A framework release invalidates a claim in the language files.

## Related

- [ship-secure-code-refresh-audit](../investigations/ship-secure-code-refresh-audit.md) — the evidence
- [ship-clean-code-refresh](ship-clean-code-refresh.md), [ship-tested-code-refresh](ship-tested-code-refresh.md) — the model
- [ship-reviewed-prs-refresh](ship-reviewed-prs-refresh.md), [ship-execute-v2-refresh](ship-execute-v2-refresh.md) — the callers
- [tool-policy-guard-bypassable-by-omission](../scars/tool-policy-guard-bypassable-by-omission.md) — the same family of problem as S5
