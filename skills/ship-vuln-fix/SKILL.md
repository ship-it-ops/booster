---
name: ship-vuln-fix
description: >
  Remediate the known CVEs and vulnerabilities that ship-vuln-scan finds. Tiered
  and evidence-gated: it AUTO-APPLIES only mechanical, reversible fixes (minimal
  dependency bumps, transitive overrides/resolutions) behind a confirmation gate
  and verifies them by re-scan + build/tests + a clean frozen install — and only
  ADVISES (produces an exact plan, never edits) for breaking/major upgrades,
  code-level mitigations, and no-fix-available cases. The apply decision is driven
  by EVIDENCE (reviewed changelog, no new install scripts, green tests), never by
  the semver delta. Every auto-apply emits a remediation audit record. Invoke for
  "fix the CVEs", "remediate vulnerabilities", "bump the vulnerable deps", or as the
  follow-on to ship-vuln-scan. Sibling ship-vuln-scan detects and verifies. Do NOT
  use to auto-fix code-level security bugs (that is intentionally out of scope).
allowed-tools: Read, Grep, Glob, Bash, Edit
---

# Vulnerability Fix Skill

## Purpose

This skill **remediates** the vulnerabilities that `ship-vuln-scan` detects — the remediation half of
the `ship-vuln-scan` → `ship-vuln-fix` pair. It consumes the scan's normalized findings artifact
(`contract.md` in `ship-vuln-scan`), decides per finding whether a fix is *mechanically safe to apply*
or *must be advised*, applies the safe ones behind a confirmation gate, and verifies closure by
re-invoking `ship-vuln-scan`.

It exists because the rest of the security family is review-only — `ship-secure-code` explicitly defers
auto-remediation as "a footgun." That caution is right for *code-level* bugs (rewriting auth logic
without a human is dangerous) but a *dependency version bump* is a different risk class: mechanical,
reversible, and verifiable by re-scan + tests. This skill automates **only** that safe class, and is
loud about everything it won't touch.

It is the **only** booster skill that mutates dependency manifests. That power is bounded three ways:
the evidence gate (below), `Edit` scoped by discipline to lockfile/manifest paths, and a mandatory
audit record per apply.

## Quickstart (New to remediation?)

Internalize these three before the rest:

1. **Semver is not evidence.** "It's only a patch bump" is not a reason to auto-apply. Patch releases
   ship behavior changes and install-script RCE vectors. The gate runs on *evidence* — a reviewed
   changelog, no new install scripts, and a green test suite — not on the version delta.
2. **Apply-safe, advise-risky.** Mechanical, reversible fixes (minimal bumps, transitive overrides)
   get applied behind a gate and verified. Breaking upgrades, code mitigations, and no-fix cases get an
   exact *plan* and nothing else. When in doubt, advise.
3. **A fix isn't done until the scan says so.** Editing a lockfile is the easy part. The fix is
   verified only when a re-scan (same engine, replayed advisory snapshot) shows the target CVE closed,
   no NEW vuln appeared in the changed subtree, and the build + full tests are green under a clean
   frozen install.

The detailed references (`reference.md`, `reference-categories.md`, the resolution files) assume the
`ship-vuln-scan` `contract.md` and familiarity with lockfile resolution.

## Mode Detection

- **Fix mode** (default and only mode): read a `ship-vuln-scan` findings artifact (or run the scan
  first), prioritize, and for each finding either APPLY (gated + verified) or ADVISE.
- **Triggered explicitly** by: `/ship-vuln-fix [artifact|path]`, "fix the CVEs", "remediate
  vulnerabilities", "bump the vulnerable deps", or as the follow-on after `ship-vuln-scan`.

If no findings artifact exists, run `ship-vuln-scan` first — never remediate against an unknown
inventory.

## The apply gate (the centerpiece)

Every finding is classified into exactly one tier. **A fix is AUTO-APPLIED (behind the confirmation
gate) only when ALL of these hold:**

1. **Clean tree.** The working tree is clean before any edit. A dirty tree → refuse (rollback would be
   undefined). This is a hard precondition, not a warning.
2. **Mechanical fix exists.** The fix is a dependency version change or a transitive
   override/resolution/constraint — not a code edit.
3. **Changelog reviewed, no breaking/behavioral change.** The release notes between installed and fixed
   version are read and show no breaking API or behavioral change. Absent/unreadable changelog → advise.
4. **No new install scripts.** The fixed package version introduces no new `postinstall`/`setup.py`/
   build hook. Installs run with **scripts disabled / sandboxed**; an install script present → advise
   (it is an execution-of-untrusted-code surface, not a mechanical bump).
5. **Coverage is trustworthy.** The originating scan surface was `full` (not `degraded`/`not-scanned`).
   You cannot prove closure on a surface you couldn't fully see.
6. **Verification passes** (after the edit, before the commit): re-scan closure + no-new-vuln + clean
   frozen install + full tests green (see VF5).

**Everything else is ADVISE-ONLY** — an exact diff + verification steps, no edit:
- major/breaking upgrades (changelog shows API change, or only a major release fixes it),
- code-level mitigations (config change, feature-disable, network control),
- no-fix-available (→ mitigation or VEX with expiry),
- any finding on a `degraded`/`not-scanned` surface,
- any case where verification used a weaker/absent engine than the original scan.

The gate is **evidence-based, not semver-based** (rule 1). A "patch" bump that fails any clause is
advised, not applied.

## Core Principles — Always Apply

These 12 rules apply to ALL remediation:

1. **Consume the contract, don't re-detect.** Start from a `ship-vuln-scan` artifact. Re-detecting ad
   hoc loses provenance, triage, and coverage flags the gate depends on.
2. **Tier before touch.** Classify apply-safe vs advise-risky for every finding before editing anything.
3. **Clean tree or refuse.** No edits on a dirty/uncommitted tree — rollback must be well-defined.
4. **Evidence over semver.** The apply decision keys on changelog + tests + install-script check, never
   on patch/minor/major alone.
5. **Scripts disabled on install.** Run package installs with lifecycle scripts disabled or sandboxed;
   an install script in the fixed version is an advise trigger, not a mechanical bump.
6. **Per-fix atomic.** Apply ONE fix, verify it, then commit or revert+reinstall — never batch many
   fixes then revert the batch. A failed fix must not strand good ones (VF6).
7. **Manifest + lockfile stay consistent.** Every apply produces a self-consistent pair that survives a
   clean frozen install (`npm ci` / `pip install --require-hashes` / `--frozen-lockfile` /
   `go mod verify`) — not just an incremental install in the agent's environment.
8. **Verify by re-scan, not by edit.** Closure means `ship-vuln-scan` (same engine, replayed
   `db_snapshot_id`) shows the target CVE gone AND no new finding in the changed subtree — plus green
   build/tests. A weaker/absent verify engine cannot prove closure → advise.
9. **Prioritize by exploitability.** Fix order is KEV → EPSS → CVSS × reachability (VF6). Don't burn the
   apply budget on a low-EPSS dev-only CVE before a KEV-listed one.
10. **Convergence is bounded.** If fixes oscillate (a bump re-opens another CVE via a peer-dep
    conflict) or the re-scan delta stops decreasing, STOP and advise — the tree needs a human/global
    solver. No infinite apply→revert loops (VF6).
11. **Audit every apply.** Each auto-applied fix emits a structured remediation record (below). No
    silent mutations.
12. **Advise loudly, never fake.** When advising, produce the exact diff and verification steps. Never
    claim a fix was applied that wasn't, and never claim closure that wasn't verified.

## The 8-Category Catalog

| ID | Label | Covers |
|----|-------|--------|
| VF1 | UPGRADE-STRATEGY | Minimal-fix vs latest; risk classified by **evidence** (changelog/tests), not semver delta. |
| VF2 | TRANSITIVE-RESOLUTION | npm `overrides`, yarn `resolutions`, pnpm `overrides`, pip constraints, maven `dependencyManagement`, go `replace` — keeping manifest+lockfile self-consistent. |
| VF3 | BREAKING-CHANGE | Changelog/migration analysis; test-gated. Determines apply vs advise for non-trivial bumps. |
| VF4 | MITIGATION | No-fix-available: config change, feature-disable, network control, backport/patch. Always advise. |
| VF5 | VERIFICATION | Re-scan closure (same engine + replayed snapshot, target CVE + no-new-vuln) + build/tests + clean frozen install. |
| VF6 | PRIORITIZE/BATCH | KEV→EPSS→CVSS×reachability order; per-fix atomic apply/verify/commit-or-revert; convergence bound. |
| VF7 | ACCEPTED-RISK/VEX | Document non-exploitable / won't-fix with justification + expiry; emit a VEX statement. |
| VF8 | APPLY-DISCIPLINE | The evidence-based apply gate (above) + rollback discipline (clean-tree precondition, reinstall-after-revert). |

Per-category procedure, false-positives, and per-ecosystem resolution mechanics are in
`reference-categories.md` and the resolution files.

## Per-fix atomic protocol (VF6)

For each finding, in priority order, within the confirmation-gated apply set:

```
assert working tree clean                          # else refuse the whole run
snapshot = current commit
edit manifest/lockfile (minimal fix or override)   # Edit, lockfile/manifest paths only
install with scripts disabled                       # npm ci --ignore-scripts / pip --no-build-isolation etc.
verify:                                             # VF5
  - clean frozen install consistent?
  - full build + tests green?
  - ship-vuln-scan re-scan (same engine, replayed db_snapshot_id):
      target CVE closed?  AND  no NEW finding in the changed subtree?
if all green:  commit this single fix  + write audit record
else:          revert to snapshot + reinstall  + record as "attempted, failed → advise"
if re-scan delta not monotonically decreasing across fixes: STOP, advise the rest   # convergence bound
```

## Remediation audit log (VF8 — apply discipline)

Every auto-applied fix appends a structured record — **NOT to `docs/agent/`** (that tree is owned by
`ship-agent-context`), but to a dedicated **`docs/security/vuln-remediation/<date>-<cve>.json`** with
its own append-only index. Each record carries: CVE/advisory id, matching scanner + version +
`db_snapshot_id`, old → new version, the changelog evidence consulted, the verify evidence (tests run +
result, re-scan engine), and the gate approver. This is the symmetric counterpart to VF7's VEX
(documenting what was *not* fixed): an immutable trail of what *was* changed and why, for incident
response and supply-chain attestation.

## Tooling boundary (be honest)

- **Enforced:** this skill never opens a PR or pushes without explicit user permission (it commits
  locally per-fix; the human decides on a PR).
- **Behavioral (v1 limitation):** `allowed-tools` declares `Edit` and `Bash` unscoped — Claude Code
  cannot ergonomically pin `Edit` to lockfile/manifest globs or `Bash` to a package-manager allowlist.
  So "Edit only lockfiles/manifests" and "installs run scripts-disabled" are **disciplines this skill
  follows**, not a sandbox. It must not edit source files or run arbitrary commands. A future version
  may add path/command scoping once the surface is stable.

## Anti-overlap & related skills

- **`ship-vuln-scan`** — detects and produces the contract this consumes; this skill re-invokes it to
  verify closure. The two are a matched pair.
- **`ship-secure-code`** — owns *code-level* security review and intentionally does NOT auto-remediate.
  This skill remediates *dependency/artifact* vulnerabilities only; it never rewrites application code.
- **`ship-devops`** — owns Dockerfile/IaC hygiene. A container/IaC fix here is a known-CVE/policy
  remediation (base-image bump, policy correction), not a hygiene rewrite.
- **`ship-execute` / `ship-reviewed-prs`** — if the user wants the applied fixes turned into a reviewed
  PR, hand the committed branch to those skills; this skill stops at verified local commits + advice.

## Verification (self-check before reporting)

- Every finding was tiered apply-safe vs advise-risky; the gate's six clauses were each checked.
- No edit happened on a dirty tree; every applied fix is an atomic commit with a passing verify.
- Closure was proven by re-scan (same engine + replayed snapshot), not asserted from the edit.
- No new vuln was introduced in any changed subtree.
- Every auto-apply wrote an audit record to `docs/security/vuln-remediation/`.
- Risky/no-fix findings were advised with exact diffs + steps, never silently skipped or faked.
- The convergence bound was respected (no infinite apply/revert loops).
