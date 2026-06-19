# Example — a mixed remediation run

A run over several findings, showing the tiered gate and the per-fix atomic loop.

## Input
A `ship-vuln-scan` artifact with 4 deps findings (all surface coverage `full`), clean working tree,
`npm test` available.

| # | Package | CVE | Fix | KEV/EPSS | Notes |
|---|---------|-----|-----|----------|-------|
| 1 | lodash 4.17.11 | CVE-2021-23337 | 4.17.21 (patch) | — / 0.41 | clean changelog, no scripts |
| 2 | minimist 1.2.0 | CVE-2021-44906 | 1.2.6 (patch) | — / 0.2 | transitive; needs override |
| 3 | node-foo 1.1.0 | CVE-2026-1 | 2.0.0 (major) | KEV | breaking API change |
| 4 | bar 0.9.0 | CVE-2026-2 | none | — / 0.6 | no fix released |

## What the skill does

**Prioritize (VF6):** #3 (KEV) → #4 (EPSS 0.6, no fix) → #1 → #2.

**Tier:**
- #3 → **advise** (breaking major). Most urgent, but not auto-applied; migration plan + interim
  mitigation emitted.
- #4 → **advise** (no fix) → mitigation / VEX with expiry.
- #1 → **apply-safe** (direct patch, clean changelog, no scripts).
- #2 → **apply-safe** (transitive → `overrides`, must pass frozen install + tests).

**Apply loop (atomic, one at a time):**
```
#1 lodash: edit package.json → npm install --package-lock-only --ignore-scripts → npm ci --ignore-scripts
   → npm test green → re-scan: CVE closed, no new finding → commit + audit
#2 minimist: add "overrides": { "minimist": "1.2.6" } → regenerate lockfile → npm ci → npm test
   → re-scan: closed, no new finding, peer ranges intact → commit + audit
convergence check: re-scan finding count 4 → 3 → 2, monotonically decreasing ✅
```

## Result
- **Applied:** 2 (lodash, minimist) — verified, 2 atomic commits, 2 audit records.
- **Advised:** 2 (#3 breaking + KEV → migration plan & interim mitigation; #4 no-fix → mitigation/VEX).
- **Residual risk:** the KEV finding (#3) remains open until a human lands the major upgrade — surfaced
  at the top, not buried.

The point: the two mechanical fixes are handled automatically and proven closed; the two that need
judgment are handed back with exact plans. Nothing risky was auto-applied, and nothing was faked.
