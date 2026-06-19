# Findings Contract — ship-vuln-scan output format

This is the normalized artifact `ship-vuln-scan` emits and `ship-vuln-fix` consumes. It is a
**per-surface superset**, not "one OSV schema" — OSV is a *package-vulnerability* schema and cannot
represent IaC misconfigurations, secret exposures, or container-layer distro advisories without
dropping fields. Each surface gets its own record type under a shared envelope.

The artifact is JSON. Emit it on request (`--artifact` / "give me the raw findings"); the
human-readable report (SKILL.md § Report format) is the default.

---

## Top-level shape

```json
{
  "schema": "ship-vuln-scan/v1",
  "generated_at": "<ISO-8601, supplied by caller — the skill does not invent timestamps>",
  "target": { "repo": "<path>", "ref": "<git sha>", "is_shallow": false },
  "coverage": [
    { "surface": "deps",      "engine": "osv-scanner", "engine_version": "1.9.2",
      "advisory_db_timestamp": "2026-06-18T04:00:00Z", "db_snapshot_id": "osv-2026-06-18",
      "status": "full" },
    { "surface": "container", "engine": null, "status": "not-scanned",
      "reason": "trivy/grype not installed; no manual fallback for container CVEs" },
    { "surface": "iac",       "engine": "checkov", "engine_version": "3.2.0", "status": "full" },
    { "surface": "secret",    "engine": "gitleaks", "engine_version": "8.18.0",
      "status": "degraded", "reason": "shallow clone; history_scope=since-ref" }
  ],
  "feeds": {
    "epss_snapshot": "2026-06-18",
    "kev_snapshot":  "2026-06-17",
    "epss_reachable": true,
    "kev_reachable":  true
  },
  "findings": [ /* per-surface records, below */ ]
}
```

### `coverage[].status` — the cardinal field
- `full` — engine ran, `engine_version` within the parser's supported range, advisory DB fresh
  (within the staleness bound), and the target was reachable (image pullable, full history present).
- `degraded` — engine ran but something weakened it: DB stale, version outside the tested range,
  partial input (shallow clone, since-ref history), or a manual fallback was used.
- `not-scanned` — no engine and no manual fallback (container, IaC). **Absence of findings here means
  UNKNOWN, never clean.** Consumers (and `ship-vuln-fix`) must refuse to assert closure on a
  `not-scanned`/`degraded` surface.

---

## Shared envelope (every finding)

```json
{
  "id": "<stable finding id, e.g. vs1-001>",
  "surface": "deps | container | iac | secret",
  "category": "VS1 | VS2 | VS3 | VS4",
  "tier": 1,
  "coverage_ref": "deps",            // links to coverage[].surface that produced it
  "provenance": {
    "engine": "osv-scanner",
    "engine_version": "1.9.2",
    "advisory_db_timestamp": "2026-06-18T04:00:00Z",
    "db_snapshot_id": "osv-2026-06-18"
  },
  "record": { /* one of the per-surface record types below */ }
}
```

`tier` is computed per SKILL.md § Severity (KEV / CVSS / EPSS / fix-availability / reachability).

---

## Per-surface record types

### `package-vuln` (VS1 — deps) — OSV-shaped
```json
{
  "type": "package-vuln",
  "ecosystem": "npm",
  "package": "lodash",
  "installed_version": "4.17.11",
  "advisory_ids": { "primary": "CVE-2021-23337", "aliases": ["GHSA-35jh-r3h4-6jhm"] },
  "affected_ranges": [{ "introduced": "0", "fixed": "4.17.21" }],
  "fixed_version": "4.17.21",
  "dependency_path": ["app", "some-lib@2.0.0", "lodash@4.17.11"],   // who pulls it in
  "scope": "runtime | dev | optional",
  "cvss": { "score": 7.2, "vector": "CVSS:3.1/...", "source": "GHSA" },
  "epss": 0.41,
  "kev": false,
  "reachability": { "verdict": "reachable | unreachable | unknown", "confidence": "low|medium|high" }
}
```
- `advisory_ids.aliases` MUST be populated (CVE↔GHSA resolved) before KEV lookup (SKILL.md rule 9).
- When OSV/GHSA/NVD disagree on score or range, the source-precedence rule in `reference.md`
  § Advisory reconciliation decides; `cvss.source` records who won.

### `container-finding` (VS2 — container)
```json
{
  "type": "container-finding",
  "image": "registry/app:1.2.3",
  "layer": "sha256:...",
  "package": "openssl",
  "installed_version": "1.1.1k-1",
  "distro_advisory": "DSA-5169-1",           // distro advisory, not always an OSV/CVE id
  "advisory_ids": { "primary": "CVE-2022-0778", "aliases": [] },
  "fixed_version": "1.1.1n-0+deb11u1",
  "class": "os-package | app-dependency",
  "cvss": { "score": 7.5, "source": "NVD" }, "epss": 0.12, "kev": false
}
```

### `iac-misconfig` (VS3 — iac)
```json
{
  "type": "iac-misconfig",
  "framework": "terraform | kubernetes | cloudformation",
  "policy_id": "CKV_AWS_18",                  // checkov/trivy policy id — no CVE/version range
  "title": "Ensure S3 bucket has access logging enabled",
  "file": "infra/s3.tf",
  "resource": "aws_s3_bucket.logs",
  "line": 14,
  "severity": "HIGH",                          // engine-reported policy severity
  "guideline": "<url or doc ref>"
}
```

### `secret` (VS4 — secret)
```json
{
  "type": "secret",
  "rule_id": "aws-access-key-id",
  "file": "config/old.env",
  "line": 7,
  "commit": "<sha if from history>",
  "history_scope": "full | since-ref",
  "match_fingerprint": "<hash, not the secret value>",   // never store the raw secret
  "validation": "active | inactive | unverified"
}
```
- Never write the raw secret into the artifact — only a fingerprint and location.

---

## Consumer contract (for `ship-vuln-fix`)
1. Read `coverage[]` first. Refuse to assert closure on any `degraded`/`not-scanned` surface.
2. Verify-by-re-scan MUST replay `db_snapshot_id` (same advisory data), compare only the targeted
   `advisory_ids`, and additionally assert no NEW finding appeared in the changed dependency subtree.
3. Honor `tier` ordering and the reachability `confidence` floor — do not deprioritize a Tier-1 on a
   low-confidence `unreachable`.
4. Treat `feeds.*_reachable: false` as "fail toward flag/advise," never toward deprioritize.
