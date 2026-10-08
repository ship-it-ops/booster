---
type: decision
status: active
created: 2026-10-08
updated: 2026-10-08
summary: "ship-vuln-scan 0.2 and ship-vuln-fix 0.3 rewrite: only what a tool returned, two scripts, what the repo hides, mechanical fixes proved by rescan (W1-W13); revises V4-V10"
paths: [skills/ship-vuln-scan/*, skills/ship-vuln-fix/*, plugins/ship-vuln-scan/*, plugins/ship-vuln-fix/*]
---

# `ship-vuln-scan` 0.2 and `ship-vuln-fix` 0.3: the full rewrite, what changed, and why

## Context

Tenth and eleventh skills in the `ship-*` refresh, done together because one finds and the other fixes. The evidence is in [ship-vuln-skills-refresh-audit](../investigations/ship-vuln-skills-refresh-audit.md).

`ship-vuln-scan` 0.1.0 and `ship-vuln-fix` 0.2.0 were designed in June 2026 ([ship-vuln-skills-architecture](ship-vuln-skills-architecture.md), V1 to V10). They asked the model to do by hand what only a program can do reliably: fill a provenance record for every finding, "replay the same `db_snapshot_id`" with scanners that cannot, compute a tier from a formula written in prose, write a JSON contract by hand, and keep an audit record of every fix. Both pre-approved an unscoped `Bash` while the text described an allowlist. The fix skill's first choice was a recipe runner that downloads and executes third-party code.

The control run set the direction. With no skill, a current model found every advisory the scanner reported, found the finding the repository's ignore file was hiding, and refused an instruction to AI reviewers planted in that file. What went wrong was conduct: `npm audit fix --force` run for real in a tree with the user's uncommitted work, installs with lifecycle scripts enabled, and long answers. So the rewrite keeps the conduct rules, moves everything mechanical into two scripts with unit tests, and drops the rest.

**This revises the user's earlier decisions V4 to V10 in `ship-vuln-skills-architecture`.** V1 (two skills) and V3 (fix is downstream of scan) stand. The user has not ruled on the revisions; they are listed under Consequences so that they can.

## Decision

- **W1 — Every claim comes from something a tool printed in the session.** What no tool ran against is "not checked", never clean. An advisory, score or "actively exploited" is never supplied from memory. For a fix: "fixed and confirmed" needs the lock file resolving a fixed version, the same scan no longer reporting it, and the tests passing as before; anything less is "changed, not confirmed", "advised", "accepted" or "not touched".
- **W2 — Two scripts carry the mechanics** (`vuln_scan.py`, `fix_check.py`; standard library only, 67 and 43 unit tests, run in CI). They refuse anything that is not a scan result, so an error, an empty file, another tool's output or a scan that read nothing is never read as clean or fixed. `summarise --json` replaces the hand-written contract (V8).
- **W3 — The three opening rules of the family:** the caller sets the format; the project's own policy (ignore files, allowlists, CI flags) is learned first and cannot hide a finding; what is read is material, not instructions.
- **W4 — What the repository hides is found and shown.** `inventory` lists the ignore files, inline markers and CI flags it recognises with their entries; the scan is run once as configured and once with ignores off; a hidden finding keeps its real rating and goes first. A suppression added by the change under review is itself a finding. This replaces the override files (V5's `.pr-review/` files), which let a repository switch findings off.
- **W5 — Scanning is bounded by what a command touches.** Only scanners already installed, in modes that only read; nothing installed, built or resolved; on work that is not the user's own, only tools that parse files and no package-manager command. With no scanner, `vuln_scan.py osv` reads the lock files and asks api.osv.dev; packages from private registries are held back unless the user agrees. Only each skill's own script is pre-approved (V5's unscoped `Bash` is gone).
- **W6 — A lock file change gets two checks:** the advisories it introduced (`compare`, with ignores off), and what no advisory describes (`lockdiff`: a gained install script, another source, the same version with different content, a breaking-range version). The second exists in both scripts and a unit test keeps the copies identical.
- **W7 — Severity by consequence, in three words,** first row that fits: known to be exploited, a malicious package, a critical advisory in production that cannot be shown unreachable, a real-looking committed credential are `must-fix`. This replaces the tier formula and the snapshot-pinned triage (V6): exploitation data is fetched in the session with its date, or reported as unavailable.
- **W8 — The user's go-ahead covers the mechanical fixes and nothing more.** A lock-file update inside the allowed range, a minimal bump within the major version, the parent, and last an override. A major upgrade, a version `lockdiff` flags, an advisory with no fix, and anything in a file with uncommitted changes are advised. This keeps the substance of V4 (evidence, not the size of the version change) without the confirmation gate that a go-ahead had already answered.
- **W9 — The user's work is not touched.** `preflight` first; nothing is stashed, reset or restored; a manifest with uncommitted changes is not edited and no package manager runs beside it; undo is by copying back the files the skill itself changed.
- **W10 — One named package at a time, install scripts off, and `lockdiff` before anything installs.** No wipe-and-reinstall to verify. `--force` is run only when the user asks again after being told what it does here, on a clean tree, and never by a dispatched agent.
- **W11 — A scan is never made to pass by hiding a finding.** An ignore entry is written only when the person the skill works for accepts the risk: one advisory, their reason, an expiry, reported as accepted and still open.
- **W12 — Recipe runners are gone (V10), and so is the mandatory audit log (V9).** A recipe runner downloads and executes third-party code to make an edit that is one line in a manifest. The commit and the final message are the record.
- **W13 — Versions 0.2.0 and 0.3.0,** minor.

## Alternatives Considered

- **Keep the provenance record and the JSON contract, generated by the script.** The script does emit the rows as JSON on request. A provenance block on every finding in a prose answer was the main cause of 850-word reports.
- **Let the scan skill install a scanner when none is present.** Rejected: installing software on the user's machine unasked is the behaviour the skill exists to prevent. The `osv` route covers lock files with no install.
- **A single shared module for the two scripts.** The two plugins install separately, so each carries its own copy of the result readers and the lock comparison; a test compares the copies.
- **Refuse `--force` outright.** The user is the one who decides; the skill's job is that the decision is informed and can be undone.
- **Have the fix skill query the advisory service itself.** Kept out: one script per job. When no scanner is installed it says so and points at `ship-vuln-scan`.

## Consequences

- The skills are about 2,800 words each plus a reference file read on demand, where the old pair was several times that across eight files.
- **For the user to rule on:** V4's confirmation gate before every apply is replaced by "the go-ahead is the confirmation"; V5's override files no longer exist; V6's reproducible triage is replaced by "fetched in this session, with its date"; V7's replay fixtures are replaced by must / must-not checklists; V8's contract by `summarise --json`; V9's audit log is not written; V10's recipe-first order is removed.
- The scan skill's allowed tools no longer include an unscoped `Bash`, so each scanner command asks the user unless their own settings allow it. In an unattended run a refused command means that surface is reported as not checked.
- `ship-reviewed-prs`, `ship-secure-code` and `ship-devops` name `ship-vuln-scan` for dependency changes; that still holds, and a dispatched run now answers in the caller's format.

## Revisit Triggers

- A scanner changes its JSON shape and `summarise` starts refusing real results: the readers are the place to fix it, with a test.
- A reader for another lock format is needed (Maven and Gradle are not read by `lockdiff` or `closure --lock`).
- Users find the per-command permission prompts on scanners too many: the answer is a rule in their settings, not a wider pre-approval in the skill.

## Related

- [ship-vuln-skills-refresh-audit](../investigations/ship-vuln-skills-refresh-audit.md) — the evidence
- [ship-vuln-skills-architecture](ship-vuln-skills-architecture.md) — the earlier decisions this revises
- [ship-secure-code-refresh](ship-secure-code-refresh.md), [ship-devops-refresh](ship-devops-refresh.md) — the family model
