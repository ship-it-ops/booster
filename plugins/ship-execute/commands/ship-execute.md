---
description: Execute a written implementation plan with a fleet of expert subagents — runs the task DAG (parallel where independent), validates every step with real evidence (build + tests + acceptance criteria), vets the whole result via ship-reviewed-prs, then hands off for review or PR. Append "solo" to force sequential.
argument-hint: "[solo] [path/to/plan.md]"
---

Invoke the **ship-execute** skill to execute an implementation plan.

Arguments: `$ARGUMENTS`

- If the arguments contain `solo`, force **sequential** execution (no parallel worktree fan-out).
- Treat any path argument as the plan file; otherwise default to the most recent `docs/agent/plans/<slug>.md`. If no plan exists, suggest `/ship-plan` first — do not improvise a plan.

Follow the skill exactly: pre-flight parse of the task DAG / FRs / acceptance criteria, the **mandatory confirmation gate** before writing any code or running any command, the per-step **run + review** evidence gate (delegating coding depth to the `ship-code` skills), final vetting via `ship-reviewed-prs`, and the handoff menu. **Never open a PR or push without a separate explicit yes. Refuse to run in plan mode.**
