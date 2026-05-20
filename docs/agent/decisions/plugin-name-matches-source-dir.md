---
type: decision
status: active
created: 2026-05-20
updated: 2026-05-20
author: claude-opus-4-7
tags: [marketplace, plugins, naming, conventions]
importance: standard
---

# Marketplace plugin `name` matches its source directory

## Context

The obsidian-knowledge-graph plugin was originally registered in `marketplace.json` with `name: "ship-it-ops"` — the org/owner name, not the plugin's own identity. Its directory was `plugins/obsidian-knowledge-graph/`. This produced two collisions:

1. The root `.claude-plugin/plugin.json` (the repo-as-a-plugin) is *also* named `"ship-it-ops"`. Two installable plugins shared an identity.
2. The README's install command was `/plugin install ship-it-ops@booster` with a parenthetical "(legacy plugin name)" — i.e., the docs already conceded the name was wrong but the rename had been deferred.

The validator allowed the divergence by design (comment: *"the booster marketplace allows plugin name != source basename"*) but it was load-bearing only as a coping mechanism for the inconsistency, not a feature.

## Decision

A marketplace plugin's `name` matches its source directory basename. The obsidian plugin is now `obsidian-knowledge-graph` everywhere it appears as a plugin identity:

- `.claude-plugin/marketplace.json` plugin entry name
- `plugins/obsidian-knowledge-graph/.claude-plugin/plugin.json` name
- README / install docs / examples

The org name `ship-it-ops` remains where it belongs: marketplace owner, plugin authors, copyright, GitHub paths.

The root `.claude-plugin/plugin.json` (the meta-plugin that bundles the whole repo) keeps `name: "ship-it-ops"` — it represents the brand, not an individual plugin.

## Alternatives Considered

- **Keep the legacy `ship-it-ops` name and ship a migration note**: rejected — the install had been broken anyway (see related scar), so no one had successfully installed under the old name. No migration burden.
- **Rename to something marketing-friendlier (e.g., `obsidian-memory`)**: rejected — `obsidian-knowledge-graph` is what the skill is called in `skills/`. Match the source of truth.

## Consequences

- Install command shape becomes uniform: `/plugin install <name>@booster` where `<name>` is also the directory basename. Easier to teach, easier to grep.
- The validator's "plugin name may differ from source basename" comment was relaxed but not removed — the rule still permits divergence for future cases, we just stopped exercising it.
- Anyone who scripted around `ship-it-ops@booster` breaks. Acceptable cost because the install was failing anyway; no real users on the old name.

## Revisit Triggers

- If a future plugin has a legitimate reason for `name != directory` (e.g., a single source dir served under multiple plugin identities), revisit and document the case here.

## Related

- [marketplace-pluginroot-silently-ignored](../scars/marketplace-pluginroot-silently-ignored.md) — the install bug that surfaced this issue
- [agent-context-initialized](agent-context-initialized.md) — bootstrap entry
