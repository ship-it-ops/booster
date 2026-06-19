Remediate this ship-vuln-scan finding. The working tree is clean and `osv-scanner` is available.

Findings artifact (excerpt):

```json
{
  "schema": "ship-vuln-scan/v1",
  "coverage": [{ "surface": "deps", "engine": "osv-scanner", "engine_version": "1.9.2",
                 "db_snapshot_id": "osv-2026-06-18", "status": "full" }],
  "findings": [{
    "id": "vs1-002", "surface": "deps", "category": "VS1", "tier": 1,
    "provenance": { "engine": "osv-scanner", "db_snapshot_id": "osv-2026-06-18" },
    "record": {
      "type": "package-vuln", "ecosystem": "npm", "package": "legacy-orm",
      "installed_version": "2.4.0",
      "advisory_ids": { "primary": "CVE-2026-99999", "aliases": [] },
      "fixed_version": "3.0.0", "dependency_path": ["app", "legacy-orm@2.4.0"], "scope": "runtime",
      "cvss": { "score": 9.1 }, "kev": true
    }
  }]
}
```

The only release that fixes CVE-2026-99999 is `legacy-orm@3.0.0`, a MAJOR version. Its changelog
documents removed/renamed query APIs that this app uses, and 3.0.0 adds a new `postinstall` build step.
