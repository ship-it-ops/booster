---
type: instruction
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: <agent-id>
source: user-instruction
scope: always | when-X | branch:feature/y | until:YYYY-MM-DD
tags: [list, of, tags]
importance: standard
---

# {The rule, phrased as a sentence}

## Instruction
Verbatim or near-verbatim what the user said.

## Why
(Optional) The reason the user gave — captures intent for edge cases.

## How to apply
Concrete: when it kicks in, what the agent does differently.

## Source
- Session: <session-id or date>
- Captured from: "<short paraphrase of the user's words>"

## To revoke
The phrasing the user can use to turn this off.
