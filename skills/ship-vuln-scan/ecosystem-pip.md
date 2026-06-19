# Ecosystem — pip / poetry / uv (VS1)

Per-ecosystem detail for Python dependency scanning. General procedure is in
[`reference.md`](reference.md); shapes in [`contract.md`](contract.md).

## Inputs (pinned vs unpinned)

| Source | Pinned? | Resolved tree source |
|--------|---------|----------------------|
| `requirements.txt` (`==`) | yes | the file itself (but transitive only if it's a compiled/locked file) |
| `requirements.in` (`pip-compile`) | no | needs `requirements.txt` output to know resolved versions |
| `poetry.lock` | yes | `[[package]]` entries — full resolved tree incl. transitive |
| `uv.lock` | yes | `[[package]]` entries — full resolved tree |
| installed venv | yes | `pip list --format=json` against the active environment |

A bare `requirements.txt` with loose pins (`>=`) or a `.in` without its compiled output is
**degraded** — the resolved transitive set is unknown. A `poetry.lock`/`uv.lock` or a pinned compiled
`requirements.txt` is `full`-capable.

## Preferred engine
```
pip-audit -r requirements.txt -f json          # or against the environment: pip-audit -f json
osv-scanner --format json --lockfile poetry.lock
```
`pip-audit` (PyPA) queries the PyPI advisory DB + OSV; `osv-scanner` reads `poetry.lock`/`uv.lock`/
`requirements.txt` directly. Either is fine; prefer `osv-scanner` for lockfiles, `pip-audit` for a
live environment.

Manual fallback (no engine): parse pinned versions, query the OSV API (ecosystem `PyPI`) per
`(package, version)`. **Degraded.**

## Ecosystem gotchas
- **Name normalization (PEP 503):** `Flask`, `flask`, `flask_` normalize to `flask`. Normalize before
  matching or you'll miss/duplicate advisories.
- **Extras:** `package[extra]` pulls extra deps; the resolved tree (lockfile) reflects them — scan the
  resolved set, not the extras syntax.
- **Environment markers:** `; python_version < "3.9"` means a dep may not be installed on this
  interpreter — prefer the actual resolved lockfile/venv over the requirements expression.
- **Hashes (`--hash`):** confirm integrity but don't change version matching.
- **System vs venv:** scan the environment the app actually runs in; a global `pip-audit` against the
  wrong interpreter is `degraded`/misleading.
- **VCS/URL installs (`git+https://...`):** no PyPI version → can't OSV-match; mark `unknown`.

## Reachability (VS7) for Python
Reflection (`getattr`, `importlib`), dynamic imports, and framework auto-discovery make static
reachability false-negative-prone. Default `verdict: unknown`; only a high-confidence call-graph tool
result downgrades priority, and never below the severity floor (rule 7).
