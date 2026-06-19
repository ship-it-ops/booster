# ship-vuln-scan — Project Overrides (example)

Copy to `.pr-review/ship-vuln-scan.overrides.md` (or wherever your team keeps skill config) and edit.
The skill reads these to match team conventions instead of lecturing.

## Disabled surfaces
Disable a surface that doesn't apply (e.g. a library with no container or IaC):
```
disable: [container, iac]
```

## Staleness bound
How old an advisory DB may be before a surface is `degraded` (default 7 days):
```
db_staleness_days: 3
```

## Scanner preferences
Pin a preferred engine or a known-good version when multiple are installed:
```
engines:
  deps: osv-scanner
  container: grype        # prefer grype over trivy here
```

## Triage tuning
```
# escalate any KEV finding to Tier 1 regardless of reachability (this is already the default)
kev_always_tier1: true
# treat dev-only findings one tier lower (non-KEV only)
deprioritize_dev_scope: true
```

## Accepted findings (suppress with justification)
Suppress a specific finding (feeds a VEX statement). Requires a reason and an expiry:
```
accept:
  - id: CVE-2021-23337
    reason: "lodash.template not used; reachability manually confirmed unreachable"
    expires: 2026-12-31
```

## Secret-scan history budget
```
secret_history: since-ref   # full | since-ref ; since-ref records coverage=degraded
```
