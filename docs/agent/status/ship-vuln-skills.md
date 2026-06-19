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
**BOTH skills BUILT** on branch `feature/ship-vuln-scan` (not yet pushed/PR'd — awaiting user):
- v1 `ship-vuln-scan` (commit 779c638) — detection, 9 tasks, APPROVE.
- v2 `ship-vuln-fix` (commit 9ca4ee4) — remediation, 5 tasks, APPROVE.
Both passed ship-reviewed-prs final vetting (findings found + fixed in rework each round). Marketplace
at v1.3.0. The matched detect→fix pair is complete. **PR open: https://github.com/ship-it-ops/booster/pull/7**
(commit 7fa26a7). When it merges, complete this entry and move it to archive/. Follow-on ideas (out of
current scope): ecosystem expansion beyond npm+pip, executable-fixture CI job with scanners, recipe
breadth beyond OpenRewrite/native fixers.
