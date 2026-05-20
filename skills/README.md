# Skills

Ready-to-use AI skills for supercharging development. Each skill follows the [Skills 2.0 format](../docs/writing-skills.md) with a `SKILL.md` entry point.

Skills live at `skills/<skill-name>/` — one flat directory per skill, no nested subfolders.

## Available Skills

| Skill | Description |
|-------|-------------|
| [obsidian-knowledge-graph](obsidian-knowledge-graph/) | Turn Obsidian into an AI-managed knowledge graph. Captures architecture decisions, bug investigations, and codebase patterns as persistent memory across coding sessions. |
| [ship-agent-context](ship-agent-context/) | In-repo memory for AI agents. Manages `docs/agent/` — committed plans, decisions, in-flight status, open questions, and incident scars — so the next agent (or human) walks into context, not a blank slate. Standalone; complements `AGENTS.md`/`CLAUDE.md`. |

## Installation

See [Installing Skills](../docs/installing-skills.md) for setup instructions.

## Creating a New Skill

1. Create a new directory under `skills/` with your skill name
2. Copy a template from [templates/](../templates/)
3. Customize the `SKILL.md` frontmatter and instructions
4. Test it in Claude Code with `/skill-name`
5. Submit a PR
