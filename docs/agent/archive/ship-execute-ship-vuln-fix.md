---
type: status
status: completed
created: 2026-06-19
updated: 2026-06-19
author: claude-opus-4-8
branch: feature/ship-vuln-scan
agent: claude-session-2026-06-19-exec
tags: [skills, security, vulnerability, remediation, execution]
---

# Executing v2: ship-vuln-fix skill (ship-execute)

## Scope
Building the `ship-vuln-fix` remediation skill (v2 milestone of
[../plans/ship-vuln-skills-design.md](../plans/ship-vuln-skills-design.md)) on the same branch as v1.
VF1-VF8: evidence-based tiered apply gate, per-fix atomic apply/verify/commit-or-revert, remediation
audit log to docs/security/vuln-remediation/.

## Why
User chose to build v2 after v1 shipped (handoff option 4). Sequential mode, continuing on
`feature/ship-vuln-scan` so it can reference v1's contract.md.

## Current state
v2 BUILT. All 5 tasks done; validators green; ship-reviewed-prs final vetting = APPROVE
(1 nit found + fixed). Both skills now on `feature/ship-vuln-scan`. Archived 2026-06-19.
