---
type: scar
status: active
created: 2026-05-20
updated: 2026-05-20
author: claude-opus-4-7
tags: [marketplace, plugins, claude-code, install, schema]
importance: core
incident-date: 2026-05-19
tripwire: "if a plugin install fails with 'Validation errors: skills: Invalid input', remove the `skills` field from plugin.json — Claude Code rejects it; skills auto-discover from `<plugin>/skills/<name>/SKILL.md`"
---

# Don't put a `skills` array on plugin.json — Claude Code's schema rejects it

## What Happened

After fixing the `pluginRoot` issue (see related scar), `/plugin install ship-agent-context@booster` got further but then failed with:

```
Failed to install: Plugin temp_local_xxx has an invalid manifest file at
  .../temp_local_xxx/.claude-plugin/plugin.json.
Validation errors: skills: Invalid input
```

The plugin.json declared `"skills": ["../../skills/ship-agent-context"]` — a relative path back to the source skill at the repo root. The booster validator was specifically written around this convention. But Claude Code's plugin schema rejects the `skills` field entirely — not just the path format, the field itself.

## Tripwire

If a plugin install fails with **"Validation errors: skills: Invalid input"** (or any complaint about the `skills` field), **delete the `skills` field from `plugin.json`**. Skills must be auto-discovered from `<plugin>/skills/<name>/SKILL.md` instead.

## Why It Hurt

- Same as the `pluginRoot` scar: the validator approved a convention the installer rejects, so CI couldn't catch it.
- The `../../` paths in the field were doubly broken: even if the schema accepted the field, the path escapes the plugin's cached directory at install time. The marketplace only copies `plugins/<name>/` to the cache — `../../skills/<name>` from inside that cache resolves to nothing.
- This bug was masked by the first scar — until `pluginRoot` was fixed, no install made it far enough to surface this second failure.

## Don't Do This

- **Don't** declare `"skills": [...]` in any `plugin.json`. Not in plugin plugin.jsons, not in the root plugin.json.
- **Don't** put skill source files outside the plugin directory and reference them with `../` paths. The marketplace cache only contains the plugin tree.
- **Do** use the layout Anthropic's official marketplace + ship-code use:
  ```
  plugins/<name>/
  ├── .claude-plugin/plugin.json   (no `skills` field)
  └── skills/<name>/
      ├── SKILL.md       (symlink → ../../../../skills/<name>/SKILL.md)
      ├── reference.md   (symlink → ../../../../skills/<name>/reference.md)
      └── examples       (symlink → ../../../../skills/<name>/examples)
  ```
  Per-file symlinks keep the root `skills/<name>/` as single source of truth while presenting the auto-discovery layout the installer expects.
- **Do** test installs by actually running `/plugin install <name>@<marketplace>` end-to-end. A green validator does not mean a working install. Two consecutive bugs (this one and the `pluginRoot` one) made it through CI.

## Related

- [marketplace-pluginroot-silently-ignored](marketplace-pluginroot-silently-ignored.md) — same incident chain; this scar surfaced only after that one was fixed
- [plugin-name-matches-source-dir](../decisions/plugin-name-matches-source-dir.md) — naming cleanup shipped in the same session
