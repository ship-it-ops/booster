---
type: status
status: active
created: 2026-06-18
updated: 2026-06-18
author: claude-opus-4-8
branch: feature/ship-vuln-scan
agent: claude-session-2026-06-18-exec
tags: [skills, security, vulnerability, execution]
---

# Executing v1: ship-vuln-scan skill (ship-execute)

## Scope
Building the `ship-vuln-scan` detection skill (v1 milestone of
[../plans/ship-vuln-skills-design.md](../plans/ship-vuln-skills-design.md)): skill files + plugin
scaffolding + marketplace entry + a `validate-skills.py` tool-policy rule + `ship-reviewed-prs`
SC-persona wiring. v2 `ship-vuln-fix` deferred.

## Why
User chose execute-now after the twice-audited plan. Sequential mode on `feature/ship-vuln-scan`.

## Current state
v1 BUILT. All 9 tasks done; both validators green (`validate-skills.py`, `check-skill-links.py`).
Files: `skills/ship-vuln-scan/` (SKILL.md 190 lines + reference/contract/ecosystem/fixtures),
`plugins/ship-vuln-scan/` (symlinks), marketplace entry (v1.2.0), `ship-reviewed-prs` three-part
wiring, and a new `validate-skills.py` tool-policy check. Next: ship-reviewed-prs final vetting
(Stage 4), then handoff.

## Execution-time discovery
The plan's TVAL design listed `ship-reviewed-prs` in the read-only review allowlist — but it actually
declares `Task, TodoWrite, Bash` (it's the orchestrator that spawns personas and submits via `gh`).
The validator rule was scoped to the four PURE-RUBRIC skills only
(`ship-clean-code`/`ship-tested-code`/`ship-secure-code`/`ship-devops`), with `ship-reviewed-prs`
exempt. Bonus guard: `ship-vuln-scan` must not declare `Write`/`Edit` (enforces detect-only split).
