# Vulnerability Scan — Python project

## Coverage (read this first)
| Surface | Engine | Coverage | Note |
|---------|--------|----------|------|
| deps (VS1) | pip-audit (fresh DB) | **full** | pinned requirements, full resolution |
| container (VS2) | — | not-scanned (surface absent) | no image |
| iac (VS3) | — | not-scanned (surface absent) | no IaC |
| secret (VS4) | — | not-scanned | not requested |

## Tier 1 — Act now
*(none)*

## Tier 2 — Plan a fix
- **[VS1.2] Jinja2@2.10** (runtime) — **CVE-2019-10906** (alias GHSA-462w-v97r-4m45)
  - Sandbox escape via `str.format_map`. CVSS 8.6 (High, source GHSA). Fix: **2.10.1**.
  - Dependency path: `requirements.txt → Jinja2@2.10` (direct).
  - Reachability: unknown (no call-graph) — not suppressed.
  - KEV: no. EPSS: low (pinned snapshot). Fix available → Tier 2.

## Triage summary
- Tier 1: 0 · Tier 2: 1 · Tier 3: 0
- `MarkupSafe@1.1.1`: no known advisory matched at scan time.

## Provenance & reproducibility
- deps: pip-audit, fresh advisory DB; EPSS/KEV snapshots pinned to the run date.
- Reproducible: re-running against the same `db_snapshot_id` yields the same tier.

## Confidence
Dependency surface scanned at **full** coverage. No container/IaC/secret surfaces present or
requested. Remediation (bump Jinja2 → 2.10.1, a patch release) is `ship-vuln-fix`'s job — it would be
a candidate for the evidence-gated auto-apply tier (changelog + tests + frozen install).
