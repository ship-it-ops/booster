# Agent Context
Last updated: 2026-06-02 | Total notes: 5

<!--
  This file is the index for `docs/agent/`. Agents read it at session start.
  Format: - [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
-->

## Instructions
<!-- standing user instructions — always-read at session start -->

(none yet — the agent will auto-capture entries here when the user uses persistent-intent phrasing like "always X", "never X", "ask before X")

## Decisions

- [agent-context-initialized](decisions/agent-context-initialized.md) | decision | active | core | 2026-05-20 | Adopt docs/agent as in-repo agent memory
- [plugin-name-matches-source-dir](decisions/plugin-name-matches-source-dir.md) | decision | active | standard | 2026-05-20 | Marketplace plugin name matches source directory basename
- [add-user-instructions-to-skill](decisions/add-user-instructions-to-skill.md) | decision | active | core | 2026-06-02 | Add instructions/ content type for standing user rules

## Scars

- [marketplace-pluginroot-silently-ignored](scars/marketplace-pluginroot-silently-ignored.md) | scar | active | core | 2026-05-20 | Claude Code installer ignores marketplace pluginRoot field
- [plugin-manifest-rejects-skills-field](scars/plugin-manifest-rejects-skills-field.md) | scar | active | core | 2026-05-20 | plugin.json skills field rejected by installer schema
