# Using booster Skills with Cursor

## Setup

Cursor supports custom instructions through its Rules system. You can use booster skills as Cursor Rules.

### 1. Install the skill

```bash
# Quickest — npx with Cursor target
npx skills add ship-it-ops/booster --skill <skill-name> -a cursor

# Or npx add-skill (auto-detects Cursor)
npx add-skill ship-it-ops/booster --skill <skill-name>

# Or manually copy into Cursor Rules
mkdir -p your-project/.cursor/rules
cp skills/<skill-name>/SKILL.md your-project/.cursor/rules/<skill-name>.md
```

### 2. Add supporting files

For the full experience, copy the reference files too:

```bash
# Copy all supporting files (if the skill has them)
cp skills/<skill-name>/reference.md your-project/.cursor/rules/<skill-name>-reference.md
```

### 3. Alternative: Use .cursorrules file

You can also paste the core principles from `SKILL.md` into your project's `.cursorrules` file:

```bash
# Append the skill to your existing .cursorrules
cat skills/<skill-name>/SKILL.md >> your-project/.cursorrules
```

## Usage in Cursor

Once installed as a Rule, Cursor will automatically apply the skill's instructions when:

- **Composing code** in the editor (Cmd+K / Ctrl+K)
- **Chatting** about code in the sidebar
- **Generating** new files or functions

## Differences from Claude Code

| Feature | Claude Code | Cursor |
|---------|-------------|--------|
| Auto-invocation | Skill triggers automatically | Rule always loaded |
| Slash commands | `/<skill-name>` | Not available |
| Reference loading | Loads files on demand | All rules loaded at once |
| Team overrides | Separate overrides file | Edit the rule directly |

## Tips

- Cursor's context window is smaller than Claude Code's, so prefer the compact `SKILL.md` over full reference files when possible
- Only copy the reference files most relevant to your project to avoid unnecessary context usage
