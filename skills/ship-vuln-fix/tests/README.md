# ship-vuln-fix — Test Fixtures

These fixtures exercise the skill's **apply-vs-advise judgment** and the evidence gate, not a live
package install. Each `fixture-*/` has an `input.md` (a `ship-vuln-scan` findings artifact + scenario)
and an `expected-output.md` (the remediation plan/result the skill should produce).

## Manual replay procedure
1. Start a session with the `ship-vuln-fix` skill active.
2. Paste the fixture's `input.md` as the user message.
3. The skill should produce a result **substantially matching** `expected-output.md`. The load-bearing
   parts must match:
   - the **tier decision** (apply-safe vs advise-risky) and **which gate clause** drove it,
   - for apply cases: the per-fix atomic protocol + verify-by-re-scan + an audit record,
   - for advise cases: an exact plan + why it was NOT auto-applied + (for KEV) an interim mitigation.

## Fixtures
- `fixture-1-apply-safe-patch` — Jinja2 2.10 → 2.10.1: clean changelog, no install script, tests green
  → **APPLY** (gated + verified + audit record). The happy path.
- `fixture-2-advise-breaking` — a KEV CVSS-9.1 finding whose only fix is a breaking major that also adds
  a `postinstall` → **ADVISE** despite being the most urgent. Tests that the gate refuses to
  auto-apply the scary case and surfaces the residual risk loudly.

## Optional: executable check (not CI-gated)
CI installs no package managers/scanners and has no network/Docker, so these are model-replay only. A
separate local check could materialize fixture-1's manifest and run a real bump + re-scan — but that is
environment-dependent and is **not** part of `validate-skills.py`.
