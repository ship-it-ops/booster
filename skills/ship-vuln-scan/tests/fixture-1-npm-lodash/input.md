Scan this project's npm dependencies for known CVEs. No scanner is installed in this environment
(osv-scanner / npm audit unavailable), so use the manual lockfile + OSV fallback and be explicit
about coverage.

`package-lock.json` (excerpt, lockfileVersion 3):

```json
{
  "name": "demo-app",
  "lockfileVersion": 3,
  "packages": {
    "": { "name": "demo-app", "dependencies": { "report-lib": "^2.0.0" } },
    "node_modules/report-lib": {
      "version": "2.0.0",
      "dependencies": { "lodash": "4.17.11" }
    },
    "node_modules/lodash": {
      "version": "4.17.11",
      "dev": false
    }
  }
}
```

There is no Dockerfile, no IaC, and this is a shallow clone.
