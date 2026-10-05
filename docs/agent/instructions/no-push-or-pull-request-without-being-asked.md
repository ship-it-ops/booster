---
type: instruction
status: active
created: 2026-10-05
updated: 2026-10-05
summary: Never push or open a pull request unless the user asks in this session; each push is approved one at a time
source: user
---

# Do not push or open a pull request without being asked

## Instruction
Recorded by earlier agents in the skills-refresh hand-off as the user's standing rule: "Do not push or open a pull request without being asked. Pushes of this branch have been approved one at a time." Moved here on 2026-10-05 so every session sees it; the user's original sentence was not kept verbatim.

On 2026-10-04 the user said, for one push: "go ahead and commit push then lets move onto the next skill". That approved that push only.

## How to apply
Committing locally is part of the work. Before `git push`, `gh pr create` or anything else that publishes, ask, unless the user's current message already asks for it. One approval covers one push.

## To revoke
"You can push without asking now."
