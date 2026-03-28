# booster

> Boost your AI agents with powerful tools. An open-source collection of skills, agents, and workflows for supercharging AI-assisted development.

Built on the [Agent Skills open standard](https://agentskills.io) and the Claude Code Skills 2.0 format.

## Featured Skill: obsidian-knowledge-graph

Turn Obsidian into a persistent, AI-managed knowledge graph. Your AI agent builds long-term memory across coding sessions — capturing architecture decisions, bug investigations, and codebase patterns as linked notes in an Obsidian vault.

**What it does:**
- **Central vault** — Uses your existing Obsidian vault as a single knowledge base across all projects
- **Persistent memory** — Decisions, investigations, and patterns survive between sessions
- **Cross-project discovery** — A pattern found in project A helps prevent bugs in project B
- **MANIFEST-first retrieval** — A compact index lets the agent find relevant knowledge in 1-2 reads
- **Structured note types** — Decision, Investigation, Pattern, Onboarding, and Runbook templates with consistent frontmatter
- **Scoped writes** — The agent writes only to `_ai/` inside your vault, never touching your personal notes

**What it covers:**
- Vault discovery flow (finds your vault, or helps you create one)
- 5-step read protocol (MANIFEST -> targeted notes -> search fallback)
- 5-step write protocol (search -> decide -> write -> index -> link)
- Project-prefixed filenames as pseudo-primary keys
- Cross-project knowledge linking and discovery
- Scaling guidance for 100+ note vaults
- Team mode with shared and personal knowledge spaces
- Companion tool recommendations (kepano/obsidian-skills, MCP servers)

**Quick install:**
```bash
npx skills add ship-it-ops/booster --skill obsidian-knowledge-graph
```

## Installation

### Option 1: Add as a marketplace (recommended — get all current and future skills)

This repo is a Claude Code plugin marketplace. Add it once and get access to all skills — including new ones as they're released:

```bash
# In Claude Code, run:
/plugin marketplace add ship-it-ops/booster

# Then install any skill from the marketplace:
/plugin install <skill-name>@booster

# To see all available skills:
/plugin marketplace list booster
```

To auto-update when we release new skills or improvements:
```bash
/plugin marketplace update booster
```

You can also configure your project to recommend this marketplace to your team. Add to `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "booster": {
      "source": {
        "source": "github",
        "repo": "ship-it-ops/booster"
      }
    }
  }
}
```

### Option 2: npx (one command, single skill)

Using Vercel's [skills CLI](https://github.com/vercel-labs/skills):

```bash
# Install to your current project
npx skills add ship-it-ops/booster --skill <skill-name>

# Install globally (available in all projects)
npx skills add ship-it-ops/booster --skill <skill-name> -g

# Install to a specific agent (Claude Code, Cursor, Codex, etc.)
npx skills add ship-it-ops/booster --skill <skill-name> -a claude-code
```

### Option 3: npx add-skill (multi-agent)

Using [add-skill](https://add-skill.org/) to install across multiple agents at once:

```bash
# Auto-detects your installed agents and installs to all of them
npx add-skill ship-it-ops/booster --skill <skill-name>

# Install to specific agents
npx add-skill ship-it-ops/booster --skill <skill-name> -a claude-code -a cursor

# Non-interactive (great for dotfiles / CI)
npx add-skill ship-it-ops/booster --skill <skill-name> -g -y
```

### Option 4: Copy into your project

```bash
# Clone and copy
git clone https://github.com/ship-it-ops/booster.git
cp -r booster/skills/<skill-name>/ your-project/.claude/skills/<skill-name>/
```

### Option 5: Install globally (all projects)

```bash
git clone https://github.com/ship-it-ops/booster.git
mkdir -p ~/.claude/skills
cp -r booster/skills/<skill-name>/ ~/.claude/skills/<skill-name>/
```

### Option 6: Symlink for automatic updates

```bash
# Clone somewhere permanent
git clone https://github.com/ship-it-ops/booster.git ~/booster

# Symlink into your project (stays in sync with git pull)
ln -s ~/booster/skills/<skill-name>/ your-project/.claude/skills/<skill-name>

# Or symlink globally
mkdir -p ~/.claude/skills
ln -s ~/booster/skills/<skill-name>/ ~/.claude/skills/<skill-name>
```

### Option 7: Direct download (no clone, no npm)

```bash
# Download just a single skill using curl + tar
mkdir -p your-project/.claude/skills/<skill-name>
curl -sL https://github.com/ship-it-ops/booster/archive/refs/heads/main.tar.gz \
  | tar xz --strip-components=3 -C your-project/.claude/skills/<skill-name> \
  "booster-main/skills/<skill-name>"
```

### Verify installation

```bash
# In Claude Code, type / and look for the skill name
# Or run:
ls ~/.claude/skills/<skill-name>/SKILL.md 2>/dev/null \
  || ls .claude/skills/<skill-name>/SKILL.md 2>/dev/null \
  && echo "Installed!" || echo "Not found"
```

## What's Inside

```text
.claude-plugin/                      — Plugin marketplace manifest
  └── marketplace.json               — Marketplace catalog (add via /plugin marketplace add)
plugins/                             — Plugin-packaged skills (for marketplace distribution)
skills/                              — Standalone SKILL.md files (for manual / npx install)
templates/                           — Starter templates for creating new skills
docs/                                — Guides on writing, testing, and sharing skills
examples/                            — Integration examples for Claude Code, Cursor, etc.
```

## Skill Format (Skills 2.0)

Every skill is a directory with a `SKILL.md` entry point:

```text
skill-name/
├── SKILL.md              # Required — frontmatter + instructions (max 500 lines)
├── reference.md          # Optional — detailed docs Claude loads on demand
├── examples.md           # Optional — example inputs/outputs
└── scripts/              # Optional — helper scripts the skill can execute
```

`SKILL.md` uses YAML frontmatter to control behavior:

```yaml
---
name: skill-name
description: What this skill does. Claude uses this to decide when to auto-invoke.
allowed-tools: Read, Grep, Glob
---

Your skill instructions in markdown...
```

See [docs/writing-skills.md](docs/writing-skills.md) for the full guide.

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a pull request.

### Adding a new skill

1. Create a new directory under `skills/` with your skill name
2. Copy a template from [templates/](templates/)
3. Customize the `SKILL.md` frontmatter and instructions
4. Add supporting reference files as needed
5. Test it in Claude Code with `/skill-name`
6. Submit a PR

## License

[MIT](LICENSE) -- Copyright (c) 2026 ship-it-ops
