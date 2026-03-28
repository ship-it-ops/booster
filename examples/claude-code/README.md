# Using booster Skills with Claude Code

## Setup

### 1. Install a skill

```bash
# Quickest — one command via npx
npx skills add ship-it-ops/booster --skill <skill-name>

# Or install globally (all projects)
npx skills add ship-it-ops/booster --skill <skill-name> -g

# Or manually copy into your project
cp -r skills/<skill-name>/ your-project/.claude/skills/<skill-name>/
```

See the full [installation guide](../../docs/installing-skills.md) for all options (symlink, curl, multi-agent).

### 2. Verify installation

Open Claude Code in your project and type `/` — you should see your installed skill in the skill list.

## Usage

Once installed, skills work in Claude Code either automatically (via auto-invocation) or explicitly (via slash commands):

```bash
# Explicitly invoke a skill
claude "/<skill-name>"

# Or just describe what you want — skills auto-invoke when relevant
claude "describe your task here"
```

## Team Customization

Many skills support an overrides file to adapt rules to your team's conventions:

```bash
# Project-level overrides
cat > your-project/.claude/<skill-name>-overrides.md << 'EOF'
# Skill Overrides

- Add your team-specific customizations here
EOF
```

## Combining with Other Tools

Booster skills are designed to complement your existing toolchain — linters, formatters, pre-commit hooks, and CI pipelines. Skills focus on higher-level concerns that automated tools can't catch.

## Tips

- Use explicit invocation (`/<skill-name>`) for thorough analysis; let auto-invocation handle the rest
- Create an overrides file early to prevent friction when a skill conflicts with your conventions
- Start with a single skill and expand as your team gets comfortable
