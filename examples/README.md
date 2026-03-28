# Examples

Usage examples and integration guides showing how to use booster skills in real projects.

## Integrations

Guides for using booster skills with different AI coding tools:

| Tool | Guide | Description |
|------|-------|-------------|
| [Claude Code](claude-code/) | [README](claude-code/README.md) | Setup, usage examples, team customization |
| [Cursor](cursor/) | [README](cursor/README.md) | Using skills as Cursor Rules, setup, differences from Claude Code |

## Quick Start

### Claude Code

```bash
# One-command install via npx
npx skills add ship-it-ops/booster --skill <skill-name>

# Use it — invoke with the skill's slash command
claude "/<skill-name>"
```

### Cursor

```bash
# One-command install via npx
npx skills add ship-it-ops/booster --skill <skill-name> -a cursor
```

### Any agent (Claude Code, Cursor, Codex, etc.)

```bash
# Auto-detects all installed agents and installs to each
npx add-skill ship-it-ops/booster --skill <skill-name>
```

See the individual integration guides for manual installation and full details.
