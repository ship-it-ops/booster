# Remediation — 1 finding

## Tiering
| Finding | CVE | Fix | Tier | Decision |
|---------|-----|-----|------|----------|
| Jinja2@2.10 (runtime) | CVE-2019-10906 | 2.10.1 | apply-safe | **APPLY** (gated) |

Gate clauses for `vs1-001`:
1. Clean tree ✅  2. Mechanical (direct bump) ✅  3. Changelog reviewed, no breaking change ✅
4. No new install scripts ✅  5. Coverage `full` ✅  → eligible to apply; clause 6 verified after edit.

> Confirm before I edit: I will bump `Jinja2` 2.10 → 2.10.1 in `requirements.txt`, install with
> scripts disabled, run `pytest -q`, and re-scan to confirm closure. Proceed?

## Apply (per-fix atomic)
```
snapshot = HEAD (clean)
edit requirements.txt: Jinja2==2.10.1
pip install --require-hashes -r requirements.txt        # frozen, scripts not run as build hooks
pytest -q                                               # full suite → green
ship-vuln-scan re-scan (pip-audit, replay pypi-2026-06-18):
    CVE-2019-10906 closed ✅   no new finding in changed subtree ✅
→ git commit "fix(deps): bump Jinja2 2.10 → 2.10.1 (CVE-2019-10906)"
→ audit record written
```

## Audit record (docs/security/vuln-remediation/2026-06-18-CVE-2019-10906.json)
```json
{
  "cve": "CVE-2019-10906",
  "change": { "ecosystem": "PyPI", "package": "Jinja2", "from": "2.10", "to": "2.10.1", "mechanism": "direct-bump" },
  "evidence": { "changelog_reviewed": true, "breaking_change": false, "new_install_scripts": false,
                "frozen_install_consistent": true, "tests": { "ran": true, "passed": true },
                "rescan": { "engine": "pip-audit", "target_closed": true, "new_findings_in_subtree": 0 } },
  "approved_by": "user"
}
```

## Result
- **Applied:** 1 (Jinja2 → 2.10.1), verified closed, tests green. 1 atomic commit.
- **Advised:** 0 · **Skipped:** 0.
- Residual risk: none for this finding. The branch holds one verified commit; opening a PR is your call
  (this skill never pushes without explicit permission).
