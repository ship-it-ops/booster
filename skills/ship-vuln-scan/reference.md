# ship-vuln-scan — Reference

Full procedure, scanner selection, exit-code maps, advisory reconciliation, and the triage formula.
`SKILL.md` is the lean dispatcher; read this before the first run. The findings shapes are in
[`contract.md`](contract.md); the per-category deep rubric is in
[`reference-categories.md`](reference-categories.md).

---

## Procedure (detail)

1. **Discover surfaces.** Glob for manifests/lockfiles (`package-lock.json`, `pnpm-lock.yaml`,
   `yarn.lock`, `requirements*.txt`, `poetry.lock`, `uv.lock`), Dockerfiles/images, IaC
   (`*.tf`, k8s YAML, CloudFormation), and the git repo itself (for secrets). Record which surfaces
   are present — an absent surface is `not-scanned` with `reason: surface-absent` (benign).
2. **Select an engine per surface** (§ Scanner selection). Probe with `command -v`; never assume.
3. **Run, capturing real output + exit code** (§ Exit-code map). Bash is scoped to the scanner/PM
   allowlist — do not run arbitrary commands.
4. **Establish coverage** per surface (`full | degraded | not-scanned`) using the freshness and
   reachability checks below.
5. **Normalize** into `contract.md` per-surface records; resolve `CVE↔GHSA` aliases; dedup alias-aware.
6. **Enrich + triage** (§ Triage): EPSS, KEV, reachability, fix-availability → `tier`.
7. **Report** (SKILL.md § Report format) and, on request, emit the artifact.

---

## Scanner selection (preferred → fallback)

| Surface | Preferred | Then | Manual fallback |
|---------|-----------|------|-----------------|
| deps (VS1) | `osv-scanner` | `pip-audit` (pip), `npm audit --json` / `pnpm audit --json` / `yarn npm audit` | Parse the lockfile, query the OSV API per package. **Degraded.** |
| container (VS2) | `trivy image` | `grype` | **None** → `not-scanned`. |
| iac (VS3) | `checkov` | `trivy config` | **None** → `not-scanned`. |
| secret (VS4) | `gitleaks detect` | `trufflehog` | High-signal pattern grep over tree (NOT history). **Degraded.** |
| sbom (VS5) | `syft` | `trivy sbom` | n/a |

Prefer `osv-scanner` for deps because it normalizes ecosystems and emits OSV directly. Use the
native package-manager `audit` only as a secondary — its output schema is noisier and ecosystem-specific.

---

## Exit-code map (exit code ≠ failure)

Scanners signal *findings* with nonzero exit codes, with **different conventions**. Never run them
under blanket `set -e`. Capture the exit code and map it:

| Tool | clean | findings | error → degraded/not-scanned |
|------|-------|----------|------------------------------|
| osv-scanner | `0` | `1` | `127/128` or other |
| trivy | `0` | `0` (default) or your `--exit-code 1` | nonzero w/o `--exit-code`, DB-download fail |
| grype | `0` | `0` (default) or `--fail-on <sev>` | DB-update fail, nonzero otherwise |
| checkov | `0` | `1` | `2`+ / parse error |
| gitleaks | `0` | `1` | `126` and others |
| trufflehog | `0` | version-dependent (`183`/`0`) | other |
| pip-audit | `0` | `1` | other |

Rule: `findings` codes → parse results. `error` codes → that surface is `degraded` (engine present
but failed) or `not-scanned` — **never reported as clean**. Pin and record the exact command + exit
code in provenance.

---

## Coverage determination

A surface is `full` ONLY when all hold; otherwise `degraded` (or `not-scanned` if no engine ran):

- **Engine version in range** — `engine_version` within the parser's tested range (see
  reference-categories § per-tool ranges). Output schemas drift across versions; outside the range,
  the parser cannot trust field positions → `degraded`.
- **DB fresh** — `advisory_db_timestamp` within the staleness bound (default 7 days; configurable).
  A present scanner with a stale/absent DB finds fewer CVEs → `degraded`, never clean.
- **Target reachable** — VS2: the image was pullable/loaded (not an unresolved remote ref). VS4:
  full git history present (`git rev-parse --is-shallow-repository` is `false`); a shallow clone or
  since-ref scan sets `history_scope` and `degraded`.

---

## Advisory reconciliation (OSV vs GHSA vs NVD)

The same CVE can carry different scores and affected-ranges across databases, and ids alias
many-to-many. Apply deterministically:

1. **Alias resolution first.** Build the `CVE ↔ GHSA` alias set per finding (OSV `aliases`, GHSA
   `identifiers`). KEV lookup uses the CVE id; a GHSA-only finding without a resolved CVE is checked
   again after resolution, and if still unresolved, **fails toward flag** (treated as potential-KEV).
2. **Range precedence.** For "is installed version affected?", prefer the OSV/GHSA `introduced/fixed`
   events over NVD CPE ranges (OSV ranges are package-accurate; CPE is coarse). If they disagree and
   either says "affected", treat as affected (fail safe) and note the disagreement.
3. **Score precedence.** Prefer GHSA's CVSS for package ecosystems (GitHub re-scores for real-world
   package context), else NVD. Record `cvss.source`.
4. **Dedup.** Collapse records sharing any alias into one finding, keeping the highest tier and the
   union of dependency paths. Never drop a unique advisory during dedup.

---

## Triage (the formula)

Compute `tier` per finding (SKILL.md § Severity is the summary; this is authoritative):

```
fix_available = fixed_version is not null (deps/container) OR a documented mitigation exists
reachable     = reachability.verdict == "reachable"
               OR (reachability.verdict == "unreachable" AND reachability.confidence != "high")
               OR reachability.verdict == "unknown"
               # i.e. only HIGH-CONFIDENCE unreachable suppresses (rule 7)

tier 1 if kev == true
     or (cvss >= 9.0 and fix_available and reachable)
     or (epss >= 0.5 and fix_available)
tier 2 if (7.0 <= cvss < 9.0 and fix_available)
     or (epss >= 0.5 and not fix_available)         # mitigation track
tier 3 otherwise (low cvss, dev/test-only scope, or high-confidence-unreachable)
```

- **KEV unreachable feed** → treat every finding as potential-Tier-1 for the KEV test (fail safe);
  record `feeds.kev_reachable: false`.
- **Scope** (`runtime` vs `dev`/`optional`) can lower a tier by one for non-KEV findings, never for KEV.
- Pin `epss_snapshot` / `kev_snapshot` so the same scan re-run gives the same tiers.

---

## Bash allowlist (tool scoping)

The skill's `Bash` is for scanners and read-only inspection only. Allowed verbs: the scanners in
§ Scanner selection, plus `command -v`, `git rev-parse`/`rev-list`/`log` (read-only), `jq`, and
package-manager *read* subcommands (`npm ls`, `pip list`, `go list`). It never installs packages,
edits files, or runs build/deploy commands.

**What is machine-enforced vs. behavioral (be honest about this):**
- *Enforced* by the `validate-skills.py` tool-policy rule: `ship-vuln-scan` declares **no `Write`/`Edit`**
  — it cannot edit your files. Remediation (editing manifests) is `ship-vuln-fix`.
- *Behavioral* (v1 limitation): the `Bash` grant in frontmatter is **not** narrowed to a per-command
  allowlist — Claude Code's `allowed-tools` cannot ergonomically enumerate every scanner + flag
  combination. So the allowlist above is a **discipline the skill follows**, not a sandbox. Do not run
  anything outside it. A future version may pin `Bash(osv-scanner *)`-style scopes once the command set
  is stable. Until then: a detection skill with `Bash` *can* technically run a writing command — it
  must not, and this rubric is the contract.

---

## Anti-patterns (do not do)

- Reporting "0 vulnerabilities" when a surface was `degraded`/`not-scanned`.
- Running scanners under `set -e` (nonzero-on-findings looks like a crash).
- Matching CVEs from model memory instead of an advisory DB.
- Dropping a high-CVSS finding because static analysis called it unreachable.
- Forcing IaC/secret findings into the package-vuln (OSV) schema.
- Editing a manifest to "fix" something — that is `ship-vuln-fix`.

---

## Related
- [`contract.md`](contract.md) — the findings artifact shape.
- [`reference-categories.md`](reference-categories.md) — VS1–VS8 deep rubric + per-tool version ranges.
- [`ecosystem-npm.md`](ecosystem-npm.md), [`ecosystem-pip.md`](ecosystem-pip.md) — per-ecosystem detail.
