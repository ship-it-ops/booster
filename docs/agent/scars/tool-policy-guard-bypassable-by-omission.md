---
type: scar
status: active
created: 2026-06-18
updated: 2026-06-18
author: claude-opus-4-8
tags: [validation, security, allowed-tools, guard]
importance: standard
incident-date: 2026-06-18
tripwire: "if a policy/allowlist check keys off a frontmatter/config field, verify what happens when the field is ABSENT — absence usually means 'unrestricted', which silently bypasses the guard"
---

# A policy guard that skips on a missing field is bypassable by deleting that field

## What Happened
The new `validate-skills.py` tool-policy rule (enforcing that pure-rubric review skills stay
read-only) was first written to `continue` (skip) when a skill had no `allowed-tools` key. But
omitting `allowed-tools` grants UNRESTRICTED tools in Claude Code — so a future edit could make a
read-only review skill all-powerful simply by deleting its `allowed-tools` line, and the guard
designed to prevent exactly that would say nothing. Caught in Stage-4 review of the ship-vuln-scan
build and fixed (missing field on a guarded skill is now a violation).

## Tripwire
If a guard/allowlist check reads a config or frontmatter field, ask: "what does ABSENT mean?" If
absent = permissive/unrestricted, the missing-field case must be an explicit violation, not a skip.

## Why It Hurt
A security guard with a silent bypass is worse than no guard — it creates false confidence. The whole
point of the rule was to make the read-only trust model non-bypassable.

## Don't Do This
`if field not in config: continue` in a deny/allow policy check, when a missing field defaults to the
permissive state.

## Related
- [ship-vuln-skills-architecture](../decisions/ship-vuln-skills-architecture.md) — V5 tool-policy decision
