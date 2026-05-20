# Agent Context
Last updated: 2026-05-20 | Total notes: 4

<!--
  This file is the index for `docs/agent/`. Agents read it at session start.
  Format: - [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
-->

## Decisions

- [agent-context-initialized](decisions/agent-context-initialized.md) | decision | active | core | 2026-05-20 | Adopt docs/agent as in-repo agent memory
- [plugin-name-matches-source-dir](decisions/plugin-name-matches-source-dir.md) | decision | active | standard | 2026-05-20 | Marketplace plugin name matches source directory basename

## Scars

- [marketplace-pluginroot-silently-ignored](scars/marketplace-pluginroot-silently-ignored.md) | scar | active | core | 2026-05-20 | Claude Code installer ignores marketplace pluginRoot field
- [plugin-manifest-rejects-skills-field](scars/plugin-manifest-rejects-skills-field.md) | scar | active | core | 2026-05-20 | plugin.json skills field rejected by installer schema
