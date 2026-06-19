---
type: decision
status: active
created: 2026-06-18
updated: 2026-06-18
author: claude-opus-4-8
tags: [skills, security, vulnerability, architecture, allowed-tools]
importance: core
---

# ship-vuln-scan + ship-vuln-fix — Architecture Decisions (V1–V10)

## Context
booster needed coverage for **known CVEs / supply-chain vulnerabilities** — a gap left by
`ship-secure-code` (novel-bug SAST rubric, which also explicitly defers auto-remediation as
"a footgun"). Two skills were commissioned: detection and remediation. This note records the
load-bearing decisions; the full spec lives in
[ship-vuln-skills-design](../plans/ship-vuln-skills-design.md).

## Decision

- **V1. Two skills, not one** — `ship-vuln-scan` (detect) + `ship-vuln-fix` (remediate), coupled
  by a shared normalized findings contract. The scan→fix→verify loop is driven by fix re-invoking
  scan; **no third orchestration plugin**.
- **V2. Hybrid execution** — orchestrate OSS scanners (osv-scanner, trivy, grype, pip-audit,
  npm/pnpm/yarn audit, checkov, gitleaks, syft) when present; fall back to manual lockfile/advisory
  analysis when absent, **recording a coverage-degraded flag** so "couldn't scan" ≠ "clean".
- **V3. Phased delivery** — v1 = `ship-vuln-scan`; v2 = `ship-vuln-fix`. Fix is strictly downstream;
  build it only after a real producer proves the contract.
- **V4. Evidence-based apply gate** (not semver-based) — auto-apply requires clean working tree +
  reviewed changelog + no new install scripts (installs run scripts-disabled/sandboxed) + full
  tests green + clean frozen install + re-scan closure with a same-or-stronger engine + per-fix
  atomic commit/revert. Everything else is advise-only.
- **V5. Constrained tools, machine-enforced** — scan = `Read,Grep,Glob,Bash` (Bash scoped to a
  scanner/PM allowlist); fix adds `Edit` scoped to lockfile/manifest paths. The CI guard enforces
  **the pure-rubric review family stays read-only** — allowlist `{ship-clean-code,
  ship-tested-code, ship-secure-code, ship-devops}` must be ⊆ `{Read,Grep,Glob}`. (Round-2 family-04
  correction: "only `ship-vuln-*` may write" is false — `ship-agent-context`, `ship-better-plans`,
  `ship-execute`, `obsidian-knowledge-graph` already write. Net-new tokenizing parser work.)
  **Execution-time correction (2026-06-18):** `ship-reviewed-prs` is ALSO not read-only — it declares
  `Task, TodoWrite, Bash` as the persona orchestrator / `gh` submitter, so it is EXEMPT from the
  allowlist (the plan had wrongly included it). Bonus guard shipped: `ship-vuln-scan` must not declare
  `Write`/`Edit` — machine-enforces the detect-only half of the detect/fix split.
- **V6. Reproducible triage** — EPSS/KEV/CVSS feed snapshot timestamps + `db_snapshot_id` pinned in
  the artifact; verify re-scan **replays the same snapshot** and compares only the target CVE-set
  (plus a no-new-vuln-in-subtree check). KEV-unreachable fails toward *advise*. Reachability only
  deprioritizes at high confidence and never below a severity floor (round-2).
- **V7. Fixtures** — CI-gated contract = the family's model-replay (`input.*`+`expected-output.md`);
  an executable-scanner fixture is optional/separately-gated because CI installs no scanners
  (round-2 family-05). (The round-1 critique of existing fixtures as untested prose stands, but CI
  realities cap what "executable" can mean here.)
- **V8. Contract is a per-surface superset, not "one OSV schema"** (round-2 tooling-02) — OSV can't
  represent IaC/secret/container-layer findings; distinct record types per surface under a shared
  provenance envelope (engine+version+db_snapshot+coverage+exit-code-map+alias-set).
- **V9. Remediation audit log lives outside `docs/agent/`** (round-2 family-03) — that tree is owned
  by `ship-agent-context` (fixed taxonomy + MANIFEST + bounded `status/`). The unbounded per-fix log
  goes to a dedicated `docs/security/vuln-remediation/` path with its own index.
- **V10. Recipe-first remediation (ship-vuln-fix 0.2.0).** Prefer a tested recipe/tool
  (OpenRewrite/Moderne, non-`--force` native fixers, Dependabot scores as *context only*) over a manual
  edit, mirroring the scanner-then-fallback hybrid — but the recipe is a *fix source*, never a
  verification bypass. Hardened after a focused adversarial pass (7 findings): the recipe **process is
  untrusted code** → pinned+checksum-verified coordinate allowlist, run **offline with no credentials**
  (executes pre-install); no `--force`; compatibility score is non-gating; recipe-assisted *breaking*
  upgrades require **per-package opt-in + a coverage floor + scope bound** (a green thin suite is not
  proof); recipe runs write *source* files (not just manifests) → stage-for-total-revert + re-scan per
  step. `fix_source` recorded in the audit log.

## Alternatives Considered
- **One skill, two modes** — rejected: bloats SKILL.md past the 500-line target, muddies the
  apply/advise gate, and the user asked for two.
- **Third orchestration plugin for the loop** — rejected: over-built; the loop is one skill calling
  the other.
- **Semver-delta apply tier** ("patch/minor = safe") — rejected at audit (BLOCKER production-02):
  patch releases ship breaking behavior and install-script RCE vectors; risk must be evidence-based.
- **Blanket `Bash`/`Edit`** — rejected at audit (BLOCKER production-03): silently breaks the
  read-only invariant with no CI guard.

## Consequences
- These are the **first booster skills that execute tools and (in v2) mutate files** — a deliberate,
  bounded, CI-guarded exception to the read-only family norm.
- Requires a new `validate-skills.py` capability (allowed-tools value enforcement).
- Adds a remediation audit-log artifact convention under `docs/agent/`.

## Revisit Triggers
- A user wants auto-apply of major/breaking upgrades (would require a sandbox/CI-gated execution model).
- A second consumer of the findings contract appears (would justify promoting it to a standalone spec).
- The marketplace adds another tool-executing skill (generalize the validator rule beyond `ship-vuln-*`).

## Related
- [ship-vuln-skills-design](../plans/ship-vuln-skills-design.md) — full plan + rubrics + DAG
- [merge-ship-code-into-booster](./merge-ship-code-into-booster.md) — the family these join
- [add-user-instructions-to-skill](./add-user-instructions-to-skill.md) — prior skill-design decision pattern
