---
description: Produce a bulletproof, audited implementation plan (intake → discovery → tradeoffs → spec → task DAG → multi-persona audit) written to docs/agent/plans/. Append "ultra" for the loop-until-dry convergence audit.
argument-hint: "[ultra] <what you want to plan>"
---

Invoke the **ship-better-plans** skill to produce an audited implementation plan.

Arguments: `$ARGUMENTS`

- If the arguments begin with `ultra`, run in **ultra** mode (full persona set + adversarial-verify + loop-until-dry). Otherwise run **standard** mode.
- Treat the rest of the arguments as the planning request. If empty, ask the user what to plan (one question at a time).

Follow the skill exactly: structured intake, automatic `docs/agent/` + codebase discovery, 2–3 scored tradeoff options, numbered specs with edge cases, a Mermaid task DAG with subagent delegation, and the **D6 audit cost gate** before launching the Workflow audit. Respect plan mode (D5): if plan mode is active, keep Phases 1–6 read-only, call ExitPlanMode for approval, and defer all `docs/agent/` writes until after approval. End by offering the execution choice — do not auto-execute.
