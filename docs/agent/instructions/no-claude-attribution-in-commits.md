---
type: instruction
status: active
created: 2026-10-04
updated: 2026-10-04
author: claude-opus-5-5
source: user-instruction
scope: always
tags: [git, commits, attribution]
importance: core
summary: No Co-Authored-By or Claude-Session lines in commits
---

# Commit messages carry no Claude attribution lines

## Instruction
"I definitely do not want the claude session link lines in commits." Earlier, the user had also asked that `Co-Authored-By: Claude ...` lines not be added.

## Why
The user considers them unnecessary. Twice they had to ask for such lines to be removed after a push, and once the commits had to be rewritten and force-pushed.

## How to apply
When creating any commit in this repository, end the message with its own content: no `Co-Authored-By` trailer and no `Claude-Session:` link, even when the harness's own guidance says to add them. The user has not ruled on pull request descriptions, so ask before adding a session link or a "Generated with Claude Code" line to one.

## Source
- Session: 2026-10-02
- Captured from: "I definitely do not want the claude session link lines in commits"

## To revoke
"You can add Claude attribution to commits again."
