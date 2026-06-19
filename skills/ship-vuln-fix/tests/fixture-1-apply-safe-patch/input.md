Remediate this ship-vuln-scan finding. The working tree is clean, `pip-audit` is available, and the
project's test suite is `pytest -q`.

Findings artifact (excerpt):

```json
{
  "schema": "ship-vuln-scan/v1",
  "coverage": [{ "surface": "deps", "engine": "pip-audit", "engine_version": "2.7.0",
                 "db_snapshot_id": "pypi-2026-06-18", "status": "full" }],
  "findings": [{
    "id": "vs1-001", "surface": "deps", "category": "VS1", "tier": 2,
    "provenance": { "engine": "pip-audit", "db_snapshot_id": "pypi-2026-06-18" },
    "record": {
      "type": "package-vuln", "ecosystem": "PyPI", "package": "Jinja2",
      "installed_version": "2.10",
      "advisory_ids": { "primary": "CVE-2019-10906", "aliases": ["GHSA-462w-v97r-4m45"] },
      "fixed_version": "2.10.1", "dependency_path": ["app", "Jinja2@2.10"], "scope": "runtime",
      "cvss": { "score": 8.6 }, "kev": false
    }
  }]
}
```

The 2.10 → 2.10.1 changelog shows only the sandbox-escape fix, no API change. The fixed version adds no
install hooks.
