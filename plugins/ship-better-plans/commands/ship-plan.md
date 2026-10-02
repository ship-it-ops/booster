---
description: Write an implementation plan grounded in the codebase and reviewed before approval, saved to docs/agent/plans/. Start the arguments with "ultra" for the deepest review.
argument-hint: "[ultra] <what you want to plan>"
---

Use the **ship-better-plans** skill to plan the work described below.

Arguments: `$ARGUMENTS`

- If the arguments begin with `ultra`, the user has chosen ultra depth. Otherwise the skill asks for the review depth at its checkpoint.
- The rest of the arguments is the planning request. If it is empty, ask the user what they want planned.

The user asked for a plan explicitly, so begin the skill's process without asking whether to plan.
