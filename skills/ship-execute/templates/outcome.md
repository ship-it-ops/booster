---
type: investigation
status: completed
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: <agent-id>
tags: [ship-execute, outcome]
---

# Execution outcome: {plan-slug}

## What was executed
Plan + branch + final disposition (merged / PR #N / kept / discarded).

## Evidence
- Tasks: <done>/<total>. Full suite: <green/red>.
- Acceptance criteria: <met/total>, each checked against its FR.
- Final vetting: ship-reviewed-prs <APPROVE/…> (or fallback review).
- `git diff --stat` BASE..HEAD summary.

## Deferred / concerns
Any DONE_WITH_CONCERNS notes or follow-ups.

## Decisions / scars captured
Links to any `docs/agent/decisions/` or `docs/agent/scars/` written during execution.

## Related
- Link the plan, e.g. `[slug](../plans/<slug>.md)`
