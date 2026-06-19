# Remediation — 1 finding

## Tiering
| Finding | CVE | Fix | Tier | Decision |
|---------|-----|-----|------|----------|
| legacy-orm@2.4.0 (runtime) | CVE-2026-99999 (**KEV**, CVSS 9.1) | 3.0.0 (major) | advise-risky | **ADVISE** |

Gate clauses for `vs1-002`:
1. Clean tree ✅  2. Mechanical? ✅ (a bump) → but
3. Changelog shows **breaking API change** (removed/renamed query APIs the app uses) → **FAIL** → advise
4. Fixed version adds a **new `postinstall` build step** → independent advise trigger (untrusted-code surface)

> This is the most urgent finding (KEV, CVSS 9.1) but it is **NOT auto-applied** — the only fix is a
> breaking major upgrade that also adds an install script. Auto-applying it would risk both a runtime
> break and untrusted-code execution. It needs a human-driven migration.

## Advisory (exact plan — not applied)
**Upgrade `legacy-orm` 2.4.0 → 3.0.0 (breaking).** Steps for a human:
1. On a branch, bump `package.json`: `"legacy-orm": "^3.0.0"`.
2. Migrate call sites for the removed/renamed query APIs (see 3.0.0 changelog § Breaking).
3. Review the new `postinstall` script before installing; install with `--ignore-scripts` first, then
   enable deliberately once vetted.
4. `npm ci` (frozen) + full test suite must pass.
5. Re-scan (`osv-scanner`, replay `osv-2026-06-18`): confirm CVE-2026-99999 closed and no new finding in
   the `legacy-orm` subtree.

**Interim mitigation (until the upgrade lands), since this is KEV:** if the vulnerable codepath is
isolatable, disable/guard the affected feature or add a network control; track with a VEX
"affected-but-mitigated" statement and a short expiry. Do not mark it not-affected — it is KEV and
reachable.

## Result
- **Applied:** 0 (correctly — breaking + install-script).
- **Advised:** 1 (with migration steps + interim mitigation).
- Residual risk: **HIGH and open** — a KEV-listed CVE remains until the human-led major upgrade ships.
  This is surfaced loudly precisely because the skill won't paper over it with an unsafe auto-apply.
