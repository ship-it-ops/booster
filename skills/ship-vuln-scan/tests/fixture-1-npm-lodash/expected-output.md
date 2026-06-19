# Vulnerability Scan — demo-app

## Coverage (read this first)
| Surface | Engine | Coverage | Note |
|---------|--------|----------|------|
| deps (VS1) | none → manual lockfile + OSV fallback | **degraded** | no scanner installed; strictly weaker than osv-scanner |
| container (VS2) | — | not-scanned (surface absent) | no Dockerfile/image |
| iac (VS3) | — | not-scanned (surface absent) | no IaC |
| secret (VS4) | — | not-scanned | shallow clone — history not available |

> Coverage is **degraded** for deps and the repo is a shallow clone. Absence of additional findings
> is *not* a clean bill of health.

## Tier 1 — Act now
*(none)*

## Tier 2 — Plan a fix
- **[VS1.2] lodash@4.17.11** (runtime) — **CVE-2021-23337** (alias GHSA-35jh-r3h4-6jhm)
  - Command injection via `template`. CVSS 7.2 (High, source GHSA). Fix: **4.17.21**.
  - Dependency path: `demo-app → report-lib@2.0.0 → lodash@4.17.11` (transitive).
  - Reachability: **unknown** (no call-graph engine) — not suppressed.
  - EPSS/KEV: not on KEV; EPSS unconfirmed (feed not queried in fallback) → treated fail-safe.

## Triage summary
- Tier 1: 0 · Tier 2: 1 · Tier 3: 0
- KEV-and-reachable subset: 0 confirmed (reachability unknown; not cleared).

## Provenance & reproducibility
- deps: manual OSV API match, advisory data as of the run; no `db_snapshot_id` (fallback path).
- A real run with `osv-scanner` would upgrade deps coverage to `full` and pin a snapshot.

## Confidence
Only the dependency surface was examined, at **degraded** coverage. Container, IaC, and secret
surfaces were not scanned. Recommended: install `osv-scanner` (deps) and run on a full clone before
trusting absence of findings. Remediation (bump lodash → 4.17.21) is `ship-vuln-fix`'s job.
