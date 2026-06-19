# Vulnerability Scan Categories — Deep Rubric

For each of VS1–VS8: what it detects, antipatterns that hide vulnerabilities, common false-positives,
and the tested engine version ranges. Cross-references to `reference.md` and `contract.md`.

---

## Per-tool tested version ranges

The normalizer parses these output schemas; outside the range → `coverage: degraded` (the parser
cannot trust field positions). Widen the range only after adding a parser test fixture.

| Tool | Tested range | Output flag | Schema note |
|------|--------------|-------------|-------------|
| osv-scanner | 1.7 – 2.x | `--format json` | v2 adds `experimental` reachability fields; parse defensively |
| trivy | 0.45 – 0.5x | `--format json` | `Results[].Vulnerabilities[]`; severity from `Severity` |
| grype | 0.6x – 0.8x | `-o json` | `matches[].vulnerability`; `descriptor.schema` is versioned independently |
| checkov | 3.x | `-o json` | `results.failed_checks[]`; multi-framework run emits a LIST, not an object |
| gitleaks | 8.x | `--report-format json` | v8 field casing (`StartLine`); v7 differs — reject v7 |
| pip-audit | 2.x | `-f json` | `dependencies[].vulns[]` |

---

## VS1 — DEP-CVE

Known CVEs in direct + transitive dependencies, matched against the resolved lockfile graph.

### Antipatterns (hide real vulns)
- Scanning the manifest (`package.json`) instead of the lockfile — misses the resolved transitive tree.
- Ignoring `pnpm`/`yarn` workspace hoisting — a vuln in a hoisted dep is attributed to the wrong package.
- Treating `npm audit` exit `0` as "clean" without checking it actually ran against the full tree.
- Skipping dev dependencies entirely (they run in CI, which often has secrets/network).

### False-positives (don't over-report)
- A CVE whose `affected_range` excludes the installed version (range-boundary off-by-one — trust OSV ranges).
- A withdrawn/rejected advisory (check OSV `withdrawn`).
- A finding against an `optional`/`dev` dependency that the production artifact never bundles — keep,
  but scope it down a tier (non-KEV only).

### Fix hint
Populate `fixed_version` from the lowest non-affected release ≥ installed (minimal-fix), and note the
nearest patch/minor. The actual fix is `ship-vuln-fix`'s job.

---

## VS2 — CONTAINER-CVE

OS-package and app-layer CVEs in a *built* image (not the Dockerfile — that's `ship-devops` DEV4).

### Antipatterns
- Scanning `FROM` base by name instead of the pinned digest actually built.
- Reporting only OS packages and missing the app layer (or vice-versa) — scan both.
- Marking `not-scanned` (no trivy/grype) as "clean" — **there is no manual fallback for VS2.**

### False-positives
- A distro that backports the fix without bumping the version string (Debian/RHEL) — trust the distro
  advisory status (`will_not_fix` / `fixed`), not just the version compare.

---

## VS3 — IAC-MISCONFIG

Known-insecure policy violations in Terraform / k8s / CloudFormation.

### Antipatterns
- Confusing this with `ship-devops` DEV3 (immutability/idempotency *hygiene*) — VS3 is *policy* (e.g.
  public S3 bucket, privileged container, no encryption-at-rest).
- Parsing the multi-framework checkov output as an object when it is a list.

### False-positives
- A policy intentionally waived via the repo's `overrides` / a `checkov:skip` comment — honor it.

---

## VS4 — SECRET-EXPOSURE

Leaked credentials in the working tree **and git history**.

### Antipatterns
- Scanning only the tree and not history (a removed secret is still in the pack and still valid).
- Reporting `coverage: full` on a shallow clone — history isn't all there. Check
  `git rev-parse --is-shallow-repository`; set `history_scope` and `degraded`.
- Running unbounded full-history scans on a huge monorepo until CI times out — use a since-ref budget
  and record `history_scope: since-ref` (degraded), don't silently truncate to "full".

### False-positives
- Test fixtures / example keys (clearly fake) — keep but mark low validation; never print the raw secret.

---

## VS5 — SBOM

Generate or ingest a CycloneDX/SPDX bill of materials; basis for VEX and reachability.

### Notes
- An SBOM of a *partial* build is itself `degraded` coverage — note what wasn't included.
- Prefer ingesting an existing CI-produced SBOM over regenerating, when its provenance is trustworthy.

---

## VS6 — TRIAGE

Score and order findings. The formula is in `reference.md` § Triage.

### Antipatterns
- Sorting by CVSS alone (ignores exploitation reality — that's what EPSS/KEV add).
- Letting an unreachable KEV feed silently deprioritize (must fail toward flag).
- Non-reproducible runs — pin `epss_snapshot` / `kev_snapshot`.

---

## VS7 — REACHABILITY

Whether the vulnerable symbol is actually callable from the app.

### Antipatterns (the dangerous ones)
- Trusting a "static" unreachable verdict on code that uses reflection, dynamic dispatch, DI
  containers, `eval`, or config-driven routing — these are structural false-negatives.
- Dropping a finding to Tier 3 on a *low/medium*-confidence unreachable — the severity floor (rule 7)
  forbids it for high-CVSS/high-EPSS.

### Use
Reachability is an *input* to triage (lowers priority at high confidence) and a *justification* for a
VEX "not-affected" statement — never a silent filter.

---

## VS8 — NORMALIZE

The orchestration layer: scanner selection, version/exit-code/DB handling, parse → per-surface
records, alias-aware dedup, coverage flagging.

### Antipatterns
- One schema for all surfaces (see `contract.md` — per-surface record types).
- Dedup that drops a unique advisory instead of merging.
- Acting on `engine_version` only by *recording* it — the parser must *gate* on it.

---

## Cross-references
- Boundaries with `ship-secure-code` (SEC7, supply-chain) and `ship-devops` (DEV3/DEV4) — SKILL.md
  § Anti-overlap.
- Output shapes — [`contract.md`](contract.md).
- Procedure, exit-codes, triage formula — [`reference.md`](reference.md).
