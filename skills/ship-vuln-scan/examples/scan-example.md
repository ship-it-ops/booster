# Example — multi-surface scan with mixed coverage

A worked example showing the cardinal rule: **never report "clean" when you mean "couldn't scan."**

## Scenario
A repo with `package-lock.json`, a `Dockerfile`/built image, and Terraform. `osv-scanner` and
`checkov` are installed; `trivy`/`grype` are **not**.

## What the skill does
1. **Discover surfaces:** deps ✓, container ✓ (image ref present), iac ✓, secret (repo present).
2. **Select engines:** deps → `osv-scanner` (full); iac → `checkov` (full); container → no
   engine, **no manual fallback** → `not-scanned`; secret → `gitleaks` absent → high-signal grep
   over tree only → `degraded`.
3. **Run + normalize**, mapping exit codes (osv `1` = findings, not failure).
4. **Triage** and produce the report.

## Output (abridged)

```
## Coverage (read this first)
| Surface    | Engine      | Coverage     | Note                                   |
|------------|-------------|--------------|----------------------------------------|
| deps       | osv-scanner | full         | db_snapshot osv-2026-06-18             |
| container  | —           | NOT-SCANNED  | trivy/grype absent; no fallback        |
| iac        | checkov     | full         |                                        |
| secret     | grep-only   | degraded     | gitleaks absent; tree-only, no history |

> Container coverage is NOT-SCANNED. The image may contain critical OS-package CVEs that this run
> could not see. Do not treat the absence of container findings as safe.

## Tier 1 — Act now
- [VS3.1] iac-misconfig CKV_AWS_20 infra/s3.tf:12 — S3 bucket public-read. Fix: set ACL private.
...
```

## The point
The deps and IaC results are trustworthy (`full`); the container result is an explicit **unknown**,
surfaced at the top — not silently omitted. A consumer (`ship-vuln-fix`) must refuse to claim the
image is clean. Installing `trivy` and re-running is the recommended next step.
