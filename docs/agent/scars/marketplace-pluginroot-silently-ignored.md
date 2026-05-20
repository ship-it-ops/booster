---
type: scar
status: active
created: 2026-05-20
updated: 2026-05-20
author: claude-opus-4-7
tags: [marketplace, plugins, claude-code, install]
importance: core
incident-date: 2026-05-19
tripwire: "if a marketplace plugin install fails with 'Source path does not exist', check that every plugin's `source` field includes the full `./plugins/<name>` path — Claude Code's installer ignores `metadata.pluginRoot`"
---

# Inline the full `./plugins/<name>` path into every marketplace `source`

## What Happened

User ran `/plugin install ship-agent-context@booster` and it failed with:

```
Failed to install: Source path does not exist:
  /Users/mohamede/.claude/plugins/marketplaces/booster/ship-agent-context
```

`marketplace.json` had `metadata.pluginRoot: "./plugins"` and each plugin declared `"source": "./ship-agent-context"`. The documented contract says `pluginRoot` is prepended to `source`, so the installer should have looked at `marketplaces/booster/plugins/ship-agent-context/`. It looked at `marketplaces/booster/ship-agent-context/` instead — i.e., it silently ignored `pluginRoot`.

## Tripwire

If a marketplace plugin install fails with **"Source path does not exist"** and the marketplace.json relies on `metadata.pluginRoot`, **assume `pluginRoot` is being ignored**. Inline the full path into each `source` (e.g., `./plugins/<name>`).

## Why It Hurt

- Both plugins in the booster marketplace were unreachable. Users hit a hard install failure with a path that *looks* correct against the documented schema.
- The repo's own validator (`scripts/validate-skills.py`) encoded the broken convention — it stripped `./` from `source` and prepended `plugins/` internally. So CI was green while installs were broken. The validator confirmed the wrong contract.
- Time-wasting: the error message points at the cache directory, not the source repo. Easy to misread as "the cache is corrupt" and retry with `/plugin marketplace update`, which doesn't help.

## Don't Do This

- **Don't** rely on `metadata.pluginRoot` in `.claude-plugin/marketplace.json`. As of Claude Code 2026-05, the installer ignores it. Inline `./plugins/<name>` into each plugin's `source`.
- **Don't** write a validator that enforces a convention the installer doesn't implement. If `validate-skills.py` and Claude Code disagree, Claude Code wins — the validator is what's wrong.
- **Don't** assume "the docs say it works" means "it works in this version". Anthropic's own `claude-plugins-official` marketplace uses inline `./plugins/<name>` paths — that's the load-bearing evidence, not the schema doc.

## Related

- [plugin-name-matches-source-dir](../decisions/plugin-name-matches-source-dir.md) — second fix shipped in the same session
- [agent-context-initialized](../decisions/agent-context-initialized.md) — bootstrap entry
