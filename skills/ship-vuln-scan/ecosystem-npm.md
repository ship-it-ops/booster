# Ecosystem — npm / pnpm / yarn (VS1)

Per-ecosystem detail for JavaScript/TypeScript dependency scanning. General procedure is in
[`reference.md`](reference.md); shapes in [`contract.md`](contract.md).

## Lockfiles (scan the lockfile, not the manifest)

| Manager | Lockfile | Resolved tree source |
|---------|----------|----------------------|
| npm | `package-lock.json` (v2/v3) | `packages` map (v2+) has the full resolved tree incl. transitive |
| pnpm | `pnpm-lock.yaml` | `packages:` keys; note workspace hoisting + `importers` |
| yarn | `yarn.lock` (v1) / `.yarn/` (berry) | resolution entries; berry has its own format |

`package.json` alone is insufficient — ranges (`^1.2.0`) don't tell you the installed version. Always
resolve from the lockfile. If only a manifest exists (no lockfile), that surface is `degraded`
(can't know the resolved transitive tree) — say so.

## Preferred engine
```
osv-scanner --format json --lockfile package-lock.json
```
`osv-scanner` reads lockfiles directly and emits OSV — least normalization work. Fallback:
`npm audit --json` (npm), `pnpm audit --json`, `yarn npm audit --json` (berry). The native audits hit
the npm advisory endpoint (network) and use ecosystem-specific JSON — noisier, parse defensively.

Manual fallback (no engine): parse the lockfile's resolved versions, query the OSV API
(`https://api.osv.dev/v1/query`, ecosystem `npm`) per `(package, version)`. **Degraded** — depends on
network and lacks the engine's curated matching.

## Transitive attribution
Build the dependency path from the lockfile graph so each finding names *who pulls it in*
(`contract.md` → `dependency_path`). This is what makes a fix actionable (direct bump vs. override).

## Ecosystem gotchas
- **Workspaces / monorepos:** multiple lockfiles; scan each workspace and attribute findings to the
  right package. A root lockfile may hoist deps — don't mis-attribute.
- **`overrides` (npm) / `resolutions` (yarn) / `pnpm.overrides`:** already-pinned transitive versions;
  the *resolved* version is what matters, not the declared range.
- **Optional/dev scope:** `package-lock` marks `dev`/`optional`; carry `scope` into the record for
  triage (dev-only can drop a tier for non-KEV).
- **Bundled deps / `bundleDependencies`:** resolved versions can differ from the registry — trust the
  lockfile integrity entry.
- **Git/file/link deps:** no registry version → can't OSV-match; mark `unknown`, don't assume clean.

## Reachability (VS7) for npm
Static reachability is weakest here (dynamic `require`, re-exports, bundlers). Default `verdict:
unknown` unless a tool (osv-scanner v2 experimental) gives a high-confidence call-graph result. Never
suppress on a low-confidence unreachable.
