---
description: Build an approved implementation plan task by task, verifying each task on the branch before it counts, and hand back a reviewed branch with an honest report. Add "solo" to run tasks one at a time.
argument-hint: "[solo] [path/to/plan.md]"
---

Use the **ship-execute** skill to build the plan named below.

Arguments: `$ARGUMENTS`

- A path argument is the plan file. With none, the skill finds the approved plan to build, and asks if there is more than one.
- `solo` means the user wants tasks run one at a time, with no parallel worktrees.

The user asked for execution explicitly. The skill still shows its start summary and asks its one start question before changing anything, unless the user has just chosen "approve and build now" for this plan in `ship-better-plans`, which already is that confirmation.
