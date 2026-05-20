---
type: decision
status: active
created: 2026-05-20
updated: 2026-05-20
author: claude-opus-4-7
tags: [meta, agent-context, bootstrap]
importance: core
---

# Adopt `docs/agent/` as the in-repo agent memory

## Context

The booster repo ships the `ship-agent-context` skill but did not itself use `docs/agent/`. Without scaffolding the folder here, every new agent walking into this repo starts blind — including agents working *on* the skill that defines this folder. We were also accumulating real, hard-won context (the `pluginRoot` install bug, the plugin rename) that `git log` does not capture in a way the next agent will find.

## Decision

Adopt `docs/agent/` as the dynamic agent-memory layer for the booster repo. Commit it to git. Use it for decisions, plans, investigations, patterns, in-flight status, open questions, and scars. Static rules continue to live in `AGENTS.md` / `CLAUDE.md` (none yet for this repo).

## Alternatives Considered

- **Keep everything in commit messages**: rejected — captures *what* changed but not *why* alternatives were rejected, and is invisible to a fresh agent who hasn't grepped the log.
- **Use the user's auto-memory (`~/.claude/projects/.../memory/`)**: rejected for shared/team-relevant content — auto-memory is local to one user. Cross-agent / cross-machine handoff needs to be repo-committed.
- **Wait until we have content "worth" capturing**: rejected — we already do (see related entries below). The skill says scaffold *when* there is content; today qualifies.

## Consequences

- The next agent on this repo can read `MANIFEST.md` + `status/` and walk in with context instead of re-deriving it.
- We dogfood the very skill this repo ships, which surfaces friction in the workflow we're asking users to adopt.
- One more folder to maintain. Mitigated by the anti-bloat rules in [SKILL.md](../../../skills/ship-agent-context/SKILL.md) — incremental writes, 5-minute rule, prune stale `status/` entries.

## Revisit Triggers

- If `docs/agent/` exceeds ~100 notes, split MANIFEST per section as documented in SKILL.md.
- If multiple parallel agents start colliding on MANIFEST.md, adopt the ledger pattern in `skills/ship-agent-context/reference.md`.

## Related

- [marketplace-pluginroot-silently-ignored](../scars/marketplace-pluginroot-silently-ignored.md) — first scar captured here
- [plugin-name-matches-source-dir](plugin-name-matches-source-dir.md) — first non-meta decision captured here
