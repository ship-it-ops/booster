---
name: ship-vuln-scan
description: >
  Detect KNOWN CVEs and supply-chain vulnerabilities across dependencies (SCA),
  container images, infrastructure-as-code, and secrets. Hybrid execution:
  orchestrates real scanners (osv-scanner, trivy, grype, pip-audit, npm/pnpm/yarn
  audit, checkov, gitleaks, syft) when present and falls back to manual
  lockfile/advisory analysis when absent — always recording scan provenance and a
  coverage flag so "couldn't scan" is never reported as "clean". Triages by CVSS +
  EPSS + KEV + reachability and emits a normalized findings artifact. Invoke for
  "scan for CVEs", "check dependencies for vulnerabilities", "vulnerability scan",
  "SBOM", or as the delegation target from ship-reviewed-prs SC when a PR changes a
  lockfile/manifest. Sibling ship-vuln-fix remediates what this finds. Do NOT use
  for novel-bug review of your own source (use ship-secure-code) or Dockerfile/IaC
  hygiene review (use ship-devops).
allowed-tools: Read, Grep, Glob, Bash
---

# Vulnerability Scan Skill

## Purpose

This skill finds **known, published vulnerabilities** in the things your project *depends on and
ships* — open-source dependencies, container images, IaC, and leaked secrets — and triages them so
the dangerous ones surface first. It is the detection half of the `ship-vuln-scan` → `ship-vuln-fix`
pair.

It is deliberately distinct from its siblings:

- **`ship-secure-code`** finds *novel* bugs in *your* source via a SAST-style rubric (injection,
  XSS, IDOR…). This skill matches *known CVE identifiers* against your dependency/artifact inventory.
- **`ship-devops`** reviews Dockerfile/IaC *hygiene* (non-root `USER`, immutable infra). This skill
  matches *known CVEs/policy violations* in the *built* image and IaC.
- **`ship-vuln-fix`** consumes this skill's findings artifact and remediates.

It operates in **detect mode** only — it never edits code or manifests. Remediation is `ship-vuln-fix`.

## Quickstart (New to vulnerability scanning?)

Internalize these three before the rest:

1. **A scanner is only as fresh as its data.** Every finding is `(advisory database) × (your
   inventory)`. A stale DB, a blocked network, or a missing engine produces *fewer* findings — which
   looks identical to "secure". Provenance and a coverage flag exist to break that ambiguity. **Never
   report "clean" when you mean "couldn't scan."**
2. **Not every CVE matters equally.** A CVSS 9.8 in a transitive dev-dependency you never call is
   less urgent than a CVSS 6.5 that is on CISA's Known Exploited list *and* reachable from your entry
   points. Triage (VS6) is the point, not raw counts.
3. **Match, don't reason.** Known-CVE detection is an *identity* problem (does installed version X of
   package P fall in the affected range of advisory A?), not a judgment call. Prefer an authoritative
   advisory source (OSV/GHSA) and a real scanner over LLM recall of "packages I think are vulnerable."

The detailed references (`reference.md`, `reference-categories.md`, `contract.md`, the ecosystem
files) assume familiarity with OSV, CVSS/EPSS/KEV, and lockfile formats.

## Mode Detection

- **Scan mode** (default and only mode): discover surfaces, run the best available scanner per
  surface (or fall back), normalize into the findings contract, triage, and produce a report. Never
  edits files.
- **Triggered explicitly** by: `/ship-vuln-scan [path]`, "scan for CVEs", "vulnerability scan",
  "check deps for vulnerabilities", "SBOM", "secret scan", or `ship-reviewed-prs` SC delegation on a
  lockfile/manifest change.

If asked to *fix* what is found, hand off to `ship-vuln-fix` — do not edit here.

## Hybrid execution model

For each surface: **prefer a real scanner; degrade explicitly.**

```
for surface in {deps, container, iac, secret}:
    engine = first available preferred scanner for surface     # see reference.md § Scanner selection
    if engine:
        raw = run engine (Bash, restricted BY DISCIPLINE to the scanner allowlist — reference.md)
        coverage = full   (engine_version in supported range AND advisory DB fresh AND target reachable)
                 | degraded (engine ran but DB stale / version out of tested range / partial input)
    else if a manual fallback exists for this surface:          # deps + secrets only
        raw = parse lockfiles / grep for secret patterns; match against OSV/GHSA
        coverage = degraded                                     # strictly weaker than a real engine
    else:                                                       # container, iac have NO manual fallback
        raw = none
        coverage = not-scanned
    normalize(raw) -> findings contract records (carry engine, version, db timestamp, coverage)
```

Two rules make this safe (both enforced in `reference.md` and the contract):

- **Exit codes ≠ failure.** Scanners exit nonzero *on findings* by design, with per-tool
  conventions. Never run them under blanket `set -e`; map each tool's exit code to
  `{clean | findings | error}` per `reference.md` § Exit-code map. An *error* → `degraded`/`not-scanned`,
  never silent "clean".
- **No fabricated closure.** A missing engine, a missing/stale DB, or an unpullable image is
  `not-scanned`/`degraded` — recorded as such, surfaced in the report, never collapsed to zero findings.

## Core Principles — Always Apply

These 12 rules apply to ALL vulnerability scanning:

1. **Inventory before advisory.** Establish what is actually present (resolved lockfile tree, image
   layers, IaC resources, tracked+historical files) before matching CVEs. A finding against a package
   that isn't actually installed is noise; a package present but unscanned is the real risk.
2. **Authoritative source of truth.** Match against OSV/GHSA (and the engine's curated DB), not
   model recall. Record which database and which timestamp produced each match.
3. **Provenance is mandatory.** Every finding carries `scan_engine`, `engine_version`,
   `advisory_db_timestamp`, and `db_snapshot_id`. A finding with no provenance is not trustworthy.
4. **Coverage honesty.** Every surface reports `coverage ∈ {full, degraded, not-scanned}`. The
   report's headline distinguishes "scanned and clean" from "could not scan." This is the cardinal rule.
5. **Direct and transitive.** Transitive dependencies are where most CVEs live. Resolve the full
   lockfile graph; attribute each finding to its dependency path (who pulls it in).
6. **Triage over counting.** Rank by KEV → EPSS → CVSS × reachability. A 200-finding wall sorted by
   CVSS alone is not triage; the KEV-and-reachable subset is what a human acts on first.
7. **Reachability deprioritizes, never silences.** Static reachability has structural
   false-negatives (reflection, dynamic dispatch, DI, `eval`, config-driven dispatch). Use it to
   *lower* priority only at high confidence; never drop a high-CVSS or high-EPSS finding below a
   severity floor because it "looked unreachable."
8. **KEV fails safe.** If the KEV/EPSS feed is unreachable, a finding fails toward *flag it*, never
   toward *deprioritize*. Record the feed snapshot timestamp so the triage is reproducible.
9. **Alias resolution before KEV.** KEV is keyed on CVE id; a GHSA-only finding must have its
   `CVE ↔ GHSA` alias resolved before the KEV lookup, or it silently misses enrichment.
10. **One finding, one identity.** Deduplicate alias-aware across engines (the same CVE reported by
    two tools, or a CVE with multiple GHSA aliases, is one finding) — but never *drop* a real finding
    during dedup.
11. **Surface-appropriate records.** A dependency CVE, a container-layer advisory, an IaC misconfig,
    and a leaked secret are different shapes. Normalize into the per-surface record types in
    `contract.md` — do not force them into one schema.
12. **Detect, don't fix.** Produce findings + an exact remediation *hint* (fixed version, mitigation),
    but never edit. Handing a clean artifact to `ship-vuln-fix` is the deliverable.

## The 8-Category Catalog

| ID | Label | Covers | Primary engine(s) (fallback) |
|----|-------|--------|------------------------------|
| VS1 | DEP-CVE | Vulnerable direct + transitive deps; lockfile-aware OSV/GHSA match. **v1: npm + pip**; maven/gradle/go/cargo additive. | osv-scanner, pip-audit, npm/pnpm/yarn audit (manual lockfile parse) |
| VS2 | CONTAINER-CVE | OS packages + app layers in built images. **No manual fallback → `not-scanned` when no engine.** | trivy, grype |
| VS3 | IAC-MISCONFIG | Known-insecure policy violations in Terraform / k8s / CloudFormation. | checkov, trivy config |
| VS4 | SECRET-EXPOSURE | Leaked credentials in the tree **and git history**; shallow-clone aware. | gitleaks, trufflehog (manual high-signal pattern grep) |
| VS5 | SBOM | Generate / ingest CycloneDX or SPDX; completeness check; basis for VEX. | syft, trivy sbom |
| VS6 | TRIAGE | Score and order: CVSS + EPSS + KEV + fix-availability + reachability. Feed snapshots pinned. | EPSS API, CISA KEV feed |
| VS7 | REACHABILITY | Is the vulnerable symbol actually called? Bounded suppression (rule 7); feeds VEX justification. | osv-scanner v2 reachability, call-graph heuristics |
| VS8 | NORMALIZE | Scanner selection, version-range + exit-code + DB-freshness handling, parse → per-surface records, alias-aware dedup, coverage flag. | (orchestration) |

Per-category antipatterns, false-positives, and engine-flag details are in `reference-categories.md`.

## Severity & triage (mechanical)

Severity is computed, not negotiated (`reference.md` § Triage has the full formula):

- **Tier 1 — Act now:** on CISA **KEV**, OR (CVSS ≥ 9.0 AND a fix exists AND not proven-unreachable),
  OR EPSS ≥ 0.5 with a fix available.
- **Tier 2 — Plan a fix:** CVSS 7.0–8.9 with a fix, or high EPSS without a fix (mitigation track).
- **Tier 3 — Track:** lower CVSS, dev-only/test-only scope, or high-confidence-unreachable.
- **Coverage caveat:** any surface at `degraded`/`not-scanned` is called out at the top of the report
  regardless of finding count — absence of findings there is *unknown*, not *safe*.

## Report format

Produce a structured report (and, on request, the raw findings artifact per `contract.md`):

1. **Coverage header** — per surface: engine + version + DB timestamp + `coverage`. Lead with any
   `degraded`/`not-scanned` surface.
2. **Tier-1 findings** — `[VSn.tier] package@version (path) — CVE-id / GHSA-id` → fixed-in version,
   KEV/EPSS/CVSS, reachability, dependency path.
3. **Tier-2 / Tier-3** — same shape, collapsed.
4. **Triage summary** — counts by tier and surface; the KEV-and-reachable subset highlighted.
5. **Provenance & reproducibility** — `db_snapshot_id`, EPSS/KEV snapshot timestamps, the exact
   scanner commands run.
6. **Confidence** — what was scanned at `full` vs `degraded`/`not-scanned`, and the residual unknown.

## Anti-overlap & related skills

- **`ship-secure-code`** — SEC7 owns the *secret-literal-in-code-under-review*; **VS4 owns
  repo-wide + git-history secret scanning**. `ship-secure-code`'s supply-chain category owns *risky
  dependency-add code patterns* (install scripts, typosquat, integrity); **VS1 owns authoritative
  known-CVE matching**. Cross-reference, don't duplicate.
- **`ship-devops`** — DEV4/DEV3 own *Dockerfile/IaC hygiene* (how it's written); **VS2/VS3 own
  known-CVE/policy matches on the built artifact**. Same file can draw both; they report different things.
- **`ship-reviewed-prs`** — its SC persona delegates to this skill (`Run /ship-vuln-scan on <lockfile>`)
  when a PR changes a lockfile/manifest, for known-CVE depth beyond a one-line pattern match.
- **`ship-vuln-fix`** — consumes the findings contract and remediates; re-invokes this skill to verify
  closure.

## Verification (self-check before reporting)

- Every surface has an explicit `coverage` value; degraded/not-scanned surfaces are in the header.
- No surface with a present-but-errored scanner is reported as "clean".
- Every finding carries provenance (engine + version + DB timestamp).
- Triage ordering applied (KEV → EPSS → CVSS × reachability); KEV alias-resolved.
- Reachability suppression respected the severity floor (rule 7).
- The artifact validates against `contract.md` (per-surface record types).
