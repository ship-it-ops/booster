# Contributing to booster

Thanks for your interest in contributing! Here's how to get started.

## How to Contribute

1. **Fork** the repository
2. **Create a branch** for your contribution (`git checkout -b add-my-skill`)
3. **Make your changes** following the guidelines below
4. **Submit a pull request**

## What to Contribute

- **Skills** — New `SKILL.md`-based skills (place in `skills/`)
- **Improvements** — Enhancements to existing skills
- **Examples** — Integration guides and usage examples (place in `examples/`)
- **Docs** — Guides, tutorials, and reference material (place in `docs/`)

## Skill Guidelines

### Structure

Every skill must follow the Skills 2.0 format:

```text
skills/skill-name/
├── SKILL.md              # Required — frontmatter + instructions
├── reference.md          # Optional — detailed reference material
├── examples.md           # Optional — example inputs/outputs
└── scripts/              # Optional — helper scripts
```

If your skill ships via the booster plugin marketplace, also add a plugin manifest and (optionally) a bundled hook:

```text
plugins/skill-name/
├── .claude-plugin/
│   └── plugin.json       # Plugin manifest (metadata + skill path)
└── hooks/                # Optional — bundled SessionStart / PreToolUse / etc.
    └── hooks.json        # Same schema as settings.json hooks
```

Bundled hooks fire automatically when the user installs the plugin via the marketplace. Use them only when guaranteed activation matters (e.g., session-start orientation). See `plugins/ship-agent-context/` for a working example. Hooks are not delivered by `npx skills add` or manual copy — only by the plugin install path.

### Naming

- Use `kebab-case` for directory names
- Be descriptive: `code-review/` not `review1/`

### SKILL.md Requirements

- Must include YAML frontmatter with at least `name` and `description`
- `description` should clearly state what the skill does AND when to use it
- Keep `SKILL.md` under 500 lines — use supporting files for detailed content
- Specify `allowed-tools` to limit tool access appropriately
- Set `disable-model-invocation: true` for skills with side effects (deploys, commits, etc.)

### Quality

- Test your skill before submitting (invoke it with `/skill-name` in Claude Code)
- Include examples of expected behavior
- Document any prerequisites or dependencies

### Commits

- Write clear, concise commit messages
- One logical change per commit

## Code of Conduct

Be respectful, constructive, and inclusive. We're all here to build better tools together.

## Questions?

Open an issue if you have questions or need help getting started.
