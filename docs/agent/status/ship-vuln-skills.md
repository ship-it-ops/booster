---
type: status
status: active
created: 2026-06-18
updated: 2026-06-18
author: claude-opus-4-8
branch: main
agent: claude-session-2026-06-18
tags: [skills, security, vulnerability, planning]
---

# Designing ship-vuln-scan + ship-vuln-fix skills

## Scope
New skills `skills/ship-vuln-scan/` + `skills/ship-vuln-fix/`, their plugins, marketplace entries,
a `validate-skills.py` allowed-tools rule, and a `ship-reviewed-prs` SC-persona wiring edit.

## Why
User commissioned a CVE/vulnerability detection skill + a remediation skill (2026-06-18).
Plan + decisions: [../plans/ship-vuln-skills-design.md](../plans/ship-vuln-skills-design.md),
[../decisions/ship-vuln-skills-architecture.md](../decisions/ship-vuln-skills-architecture.md).

## Current state
**Planning complete and audited twice** (standard: 10 findings; adversarial-only re-pass: 14 findings
incl. 3 factual corrections to repo claims; all folded in). No code written yet. Next: execute
**v1 = ship-vuln-scan** first (recommended), then v2. Heaviest remaining design work flagged by
round-2: VS8/the contract (per-surface record types, per-tool version/exit-code/DB handling) and the
`validate-skills.py` tokenizing tool-policy rule.
