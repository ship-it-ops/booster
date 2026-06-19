# ship-vuln-scan — Test Fixtures

These fixtures exercise the skill's **judgment** (coverage honesty, triage, provenance), not a live
scanner. Each `fixture-*/` has an `input.md` (the scenario + inline lockfile/manifest) and an
`expected-output.md` (the report the skill should produce).

## Manual replay procedure
1. Start a session with the `ship-vuln-scan` skill active.
2. Paste the fixture's `input.md` content as the user message.
3. The skill should produce a report **substantially matching** `expected-output.md`. Minor wording
   differences are fine; the load-bearing parts must match:
   - the **coverage table** and its `full | degraded | not-scanned` values,
   - the correct **CVE id + fixed version + tier** for each finding,
   - the **degraded/not-scanned caveat** when coverage is incomplete.

## Fixtures
- `fixture-1-npm-lodash` — no scanner installed → **degraded** deps coverage via manual fallback;
  shallow clone; transitive lodash CVE-2021-23337. Tests coverage honesty + transitive attribution.
- `fixture-2-pip-jinja2` — pip-audit available → **full** deps coverage; direct Jinja2 CVE-2019-10906.
  Tests the happy path + reproducible triage.

## Optional: executable check (not CI-gated)
CI installs no scanners (no trivy/grype/checkov/osv-scanner, no Docker/network), so these fixtures are
model-replay only. A separate, locally-run check could materialize `fixture-1`'s lockfile and run a
real `osv-scanner` to confirm the same CVE surfaces — but that is environment-dependent and is **not**
part of `validate-skills.py`.
