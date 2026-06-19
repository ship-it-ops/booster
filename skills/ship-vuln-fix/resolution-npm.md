# Resolution — npm / pnpm / yarn (VF1 / VF2)

How to remediate JS/TS dependency CVEs while keeping the manifest+lockfile consistent. General gate is
in [`reference.md`](reference.md).

## Direct dependency (VF1)
Bump the range in `package.json` to the minimal fixed version and regenerate the lockfile under a clean
frozen install:
```bash
# edit package.json: "lodash": "^4.17.21"
npm install --package-lock-only --ignore-scripts   # update lockfile without running scripts
npm ci --ignore-scripts                             # prove the frozen install resolves
```
Verify (tests + re-scan) before committing.

## Transitive dependency (VF2)
The vulnerable package is pulled by a dependency you don't control. Use an override:

| Manager | Mechanism | Example |
|---------|-----------|---------|
| npm (v8.3+) | `overrides` | `"overrides": { "lodash": "4.17.21" }` |
| npm nested | scoped override | `"overrides": { "some-lib": { "lodash": "4.17.21" } }` |
| pnpm | `pnpm.overrides` | `"pnpm": { "overrides": { "lodash@<4.17.21": "4.17.21" } }` |
| yarn (berry) | `resolutions` | `"resolutions": { "lodash": "4.17.21" }` |

After adding the override:
```bash
npm install --package-lock-only --ignore-scripts    # or pnpm install --lockfile-only
npm ci --ignore-scripts                              # frozen install must succeed
```

## Consistency & risk (what the gate catches)
- **Peer-range violation:** forcing a transitive to a version the parent never tested against can break
  at runtime even if it installs. The frozen install + full test suite + re-scan must all pass, or →
  advise (a coordinated direct bump or a parent upgrade is needed).
- **Lockfile/manifest desync:** never hand-edit only the lockfile. Always regenerate from the manifest
  change so a clean `npm ci` reproduces the same tree.
- **Integrity:** `npm ci` validates `integrity` hashes; a mismatch after an override means the override
  didn't resolve as intended → advise.

## Install-script trap (gate clause 4)
A bumped/overridden package whose new version adds a `postinstall`/`install`/`prepare` script is an
execution-of-untrusted-code surface. Detect it (`npm view <pkg>@<ver> scripts`) and, if present →
**advise**, do not auto-apply. All installs in the apply loop use `--ignore-scripts`.

## Scope
Bumping a `devDependencies`-only CVE is lower-stakes but still goes through the same gate; the audit
record notes `scope: dev`.
