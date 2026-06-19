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
**v1 (`ship-vuln-scan`) SHIPPED** on branch `feature/ship-vuln-scan` (commit 779c638): all 9 tasks
built, both validators green, ship-reviewed-prs final vetting = APPROVE (2 Should-fix found + fixed in
the rework loop). Not yet pushed/PR'd (awaiting user). **v2 (`ship-vuln-fix`) still pending** — the
remediation half. Plan + decisions remain the source of truth; the heaviest v2 work is the
evidence-gated apply engine (VF1–VF8) and the `docs/security/vuln-remediation/` audit log.
