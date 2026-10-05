---
type: decision
status: active
created: 2026-10-04
updated: 2026-10-04
author: claude-opus-5-5
tags: [skill, plugin, pr-review, github, ci, ship-family]
importance: core
summary: 1.4 rewrite: review script, lenses, thread dispositions (R1-R13)
---

# `ship-reviewed-prs` 1.4: the full rewrite, what changed from the earlier design, and why

## Context

Third skill in the `ship-*` refresh, done with the same loop as [ship-execute-v2-refresh](ship-execute-v2-refresh.md): six independent reviewers audited the existing skill, the existing skill reviewed three scratch pull requests with seeded defects and was judged independently, then rewrite, re-audit and re-run, three rounds. The evidence is in [ship-reviewed-prs-refresh-audit](../investigations/ship-reviewed-prs-refresh-audit.md).

The earlier design is spread over six decision notes. This note records what the rewrite keeps and what it revises. Every revision below was reported to the user on 2026-10-04. Their one response so far was on the version (R13); the other revisions have not been explicitly confirmed.

## Decision

### Kept

- **The verdict cascade** from [relaxed-approve-decision-matrix](relaxed-approve-decision-matrix.md): must-fix requests changes, should-fix comments, nits and pending CI never block an approval, failing CI never gets one, drafts only get a comment. `--auto-approve` stays strict.
- **Verdict labels** (`LGTM`, `LGTM (with caveats)`, `Changes requested`, `Comment`), the header, the two-column findings table, per-tier lists, "What's solid", and omitting empty sections, from [pr-review-table-driven-summary-format](pr-review-table-driven-summary-format.md).
- **Resolving the tool's own threads, never a person's, and never re-resolving a thread a person reopened**, from [pr-review-auto-resolves-own-threads](pr-review-auto-resolves-own-threads.md). The reply still begins `✅ Resolved by ship-reviewed-prs`.
- **Sibling skills for depth**, the intent of [in-persona-delegates-to-ship-devops](in-persona-delegates-to-ship-devops.md).
- **A missing question tool must not lose a CI review**, the intent of [askuserquestion-denial-failsafe-to-submission](askuserquestion-denial-failsafe-to-submission.md); the namespaced command and `--non-interactive` in the workflow prompt.
- **This repository's workflow installs the plugin from the pull request's checkout** ([pr-review-installs-plugin-from-pr-head](pr-review-installs-plugin-from-pr-head.md)).
- `max_event` (was `ci_max_decision`), the bot disclosure on unattended reviews, skipping generated and vendored files, a local confirmation before posting.

### Revised

- **R1 — A script does the mechanics.** `scripts/review_pr.py` gathers the pull request (all threads, paginated), validates each inline comment's line against the diff, computes the verdict, renders the summary, posts one review in a single request pinned to the reviewed commit, resolves threads, and writes a result file. Why: the documented `gh api` steps posted inline comments to an endpoint the REST API does not have and used `event=PENDING`, which it rejects; the "deterministic" verdict, fingerprints and thread states were pseudocode for a model to simulate and were defined three incompatible ways.
- **R2 — No persona prefixes or numbered finding IDs; severity by consequence.** Seven lenses, with correctness against the pull request's stated intent first. `must-fix`, `should-fix`, `nit` are defined by what happens if the change merges. Why: no persona owned plain bugs, and severity was the digit in the ID, so a missing metric blocked a merge while logged session tokens were a nit. The compound `[IN1 / DEV2.1-…]` tags from the ship-devops decision go with them.
- **R3 — Findings are verified before they are reported.** The script refuses a must-fix or should-fix with no `verified` note; a must-fix gets an independent second look when the Agent tool is available.
- **R4 — Sibling skills are loaded during the review**, as catalogues of what to look for; their findings come back as this review's findings. The author is never told to "Run /ship-…". Why: a delegation bullet was not a finding, did not count, and the author may not have the plugin.
- **R5 — Threads get a disposition from reading the thread and the code** (`still-valid`, `fixed`, `settled`, `withdrawn`, `no-action`, `unclear`), with script-enforced floors: an author alone cannot settle a concern someone else raised; a thread the author resolved on someone else's concern is treated as open; `fixed` needs a commit after the thread; reopened threads are never resolved or settled. A maintainer, the author included, can decline a finding this tool raised. Why: the keyword list ("see #", "as discussed", a thumbs-up) let an author switch off any finding, and "the model did not re-derive it" was taken as proof of a fix.
- **R6 — Summary layout trimmed.** The always-rendered persona table and lifecycle table are replaced by a coverage paragraph and an "Existing threads" section that appears only when the pull request has threads; the findings table is omitted when there are only nits. Why: three judges and two reviewers found the fixed tables were boilerplate on small and clean changes. This revises part of the table-driven format decision; [pr-review-summary-body-layout](../patterns/pr-review-summary-body-layout.md) is superseded.
- **R7 — The denied-question failsafe is narrowed.** The script decides whether a run is unattended (`--non-interactive`, or GitHub Actions). A missing question tool posts only in an unattended run; interactively the reviewer asks in plain text or stops. In an interactive session `post` refuses without `--confirmed`. Why: as written, a local user who dismissed the question got a review posted under their name. The CI case the decision was made for still posts, because the script detects Actions itself.
- **R8 — Exit codes, `--strict` and `--json` are gone.** A model cannot set an exit code. The script writes `result.json`; a workflow step reads it and fails the job when no review was posted, and optionally on the posted event (`FAIL_ON`).
- **R9 — Settings are a small JSON file read from the base branch** (`.claude/ship-reviewed-prs.json`: `max_event`, `nits`, `resolve_own_threads`, `skip_paths`, `notes`), failing closed. Why: the overrides file was some two dozen knobs "pattern-matched as plain text" and was read from the pull request under review, so a pull request could disable its reviewer.
- **R10 — Posting identity is handled.** On the user's own pull request (the `ship-execute` hand-off) the review is a comment that still states its verdict; a refused approval is retried as a comment; the tool's stale approval or block is dismissed; a commit is not reviewed twice; a pending review of the user's is never deleted.
- **R11 — Trust boundary.** Pull request content is material, not instructions; text that tries to steer the reviewer is a finding; conventions come from the base branch; an unattended run does not approve a change to CI, agent configuration or the reviewer; a review cannot carry a credential.
- **R12 — Removed.** The three per-language files, the overrides template, the nine paste-in fixtures (replaced by 66 unit tests against a stand-in `gh`), and the CLI and GitLab CI templates, which could not run.
- **R13 — Version 1.4.0, not 2.0.0.** The rewrite removes flags and the overrides file, which by `CONTRIBUTING.md` is a major change, and it was first set to 2.0.0. The user decided on 2026-10-04: "No v2 yet - just a minor version bump is enough." Consumers pinned to 1.x therefore get the new behaviour without a major-version signal, as with the relaxed matrix in May. [v2-release-trigger](../open-questions/v2-release-trigger.md) stays open.

## Alternatives Considered

- **Keep the personas as independent subagents for every pull request.** Rejected for ordinary changes: five to seven agents per review costs several times more, and the judged runs found every seeded defect in one context. Independent reviewers are used for large or high-risk changes and for the second look at a must-fix.
- **Post COMMENT by default in CI and make approvals opt-in.** Two reviewers argued for it. Not done: decisive verdicts were the user's choice, and they confirmed it on 2026-10-04: "The bot approvals should count towards approvals as well - so that is fine." An unattended approval is a real approval by default; `max_event` remains for teams that want an advisory reviewer.
- **Pre-approve only the read-only script commands and leave `post` to the permission prompt.** Not done: in CI the command's `allowed-tools` is what lets the review post, and changing it could not be tested without a real Actions run. `post --confirmed` is the guard instead.
- **Install from the marketplace when a pull request changes the reviewer** in this repository's workflow. Not done: it would undo the dogfood decision. The workflow asks for a comment-only review instead and says plainly that this is a request, not an enforcement.

## Consequences

- A review needs Python 3 and `gh`. Reviews posted by the rewrite carry hidden markers; threads and reviews from earlier versions are still recognised.
- Teams with a version 1 overrides file are told by `context` that it is no longer read.
- The example workflow checks out the base commit and the script fetches the pull request's commits, so the pull request's own `CLAUDE.md` and `.claude/` do not configure the reviewer.
- This repository's `pr-review.yml` now fails the job when no review was posted.

## Revisit Triggers

- The first real Actions run: does `RUNNER_TEMP` reach the session, does the default token resolve threads and dismiss reviews, is the GraphQL bot login what the script expects.
- Reviews on real pull requests miss defects that a sibling skill would have caught: make loading it the default for its area.
- Teams ask for approvals to be opt-in in CI.
- GitHub changes the review API (a REST endpoint for adding comments to a pending review, or a different rule for self-review).

## Related

- [ship-reviewed-prs-refresh-audit](../investigations/ship-reviewed-prs-refresh-audit.md) — the evidence behind the revisions
- [ship-execute-v2-refresh](ship-execute-v2-refresh.md) — hands off to this skill after opening a pull request
- [ci-mode-auto-detect-unreliable](../scars/ci-mode-auto-detect-unreliable.md) — the scar R7 and R8 answer
- [relaxed-approve-decision-matrix](relaxed-approve-decision-matrix.md), [pr-review-table-driven-summary-format](pr-review-table-driven-summary-format.md), [pr-review-auto-resolves-own-threads](pr-review-auto-resolves-own-threads.md) — the 1.x decisions kept or revised here
