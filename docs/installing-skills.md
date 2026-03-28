# Installing Skills

How to use booster skills in your projects.

## Marketplace (recommended — get all skills + auto-updates)

This repo is a Claude Code plugin marketplace. Add it once and get access to all current and future skills:

```bash
# In Claude Code:
/plugin marketplace add ship-it-ops/booster

# Install a skill:
/plugin install <skill-name>@booster

# Update when new skills or improvements are released:
/plugin marketplace update booster
```

### Team setup

Add to your project's `.claude/settings.json` so teammates get prompted to install automatically:

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

## Quick Install (npx)

The fastest way to install a skill — no cloning required:

```bash
# Using Vercel's skills CLI (recommended)
npx skills add ship-it-ops/booster --skill <skill-name>

# Or using add-skill (auto-detects all your agents)
npx add-skill ship-it-ops/booster --skill <skill-name>
```

### Install globally (all projects)

```bash
npx skills add ship-it-ops/booster --skill <skill-name> -g
```

### Install to specific agents

```bash
# Claude Code only
npx skills add ship-it-ops/booster --skill <skill-name> -a claude-code

# Multiple agents at once
npx add-skill ship-it-ops/booster --skill <skill-name> -a claude-code -a cursor

# Non-interactive (dotfiles / CI)
npx add-skill ship-it-ops/booster --skill <skill-name> -g -y
```

## Manual Installation

### Per-Project

Copy a skill directory into your project's `.claude/skills/` folder:

```bash
# From the booster repo
cp -r skills/<skill-name>/ /path/to/your-project/.claude/skills/<skill-name>/
```

The skill is now available only in that project.

### Global

Copy a skill to your personal skills directory to make it available across all projects:

```bash
mkdir -p ~/.claude/skills
cp -r skills/<skill-name>/ ~/.claude/skills/<skill-name>/
```

### Symlink (auto-update with git pull)

```bash
# Clone the repo somewhere permanent
git clone https://github.com/ship-it-ops/booster.git ~/booster

# Symlink globally
mkdir -p ~/.claude/skills
ln -s ~/booster/skills/<skill-name>/ ~/.claude/skills/<skill-name>
```

### Direct download (no clone, no npm)

```bash
mkdir -p your-project/.claude/skills/<skill-name>
curl -sL https://github.com/ship-it-ops/booster/archive/refs/heads/main.tar.gz \
  | tar xz --strip-components=3 -C your-project/.claude/skills/<skill-name> \
  "booster-main/skills/<skill-name>"
```

## Verifying Installation

1. Open Claude Code in your project
2. Type `/` to see available skills — your installed skill should appear
3. Invoke it: `/<skill-name>`

Or verify from the command line:

```bash
ls ~/.claude/skills/<skill-name>/SKILL.md 2>/dev/null \
  || ls .claude/skills/<skill-name>/SKILL.md 2>/dev/null \
  && echo "Installed!" || echo "Not found"
```

## Updating Skills

```bash
# If installed via npx — just re-run the install command
npx skills add ship-it-ops/booster --skill <skill-name> -g -y

# If installed via symlink — just pull
cd ~/booster && git pull

# If installed via copy — re-copy
cp -r skills/<skill-name>/ ~/.claude/skills/<skill-name>/
```

## Uninstalling

```bash
# Remove from project
rm -rf /path/to/your-project/.claude/skills/<skill-name>/

# Remove globally
rm -rf ~/.claude/skills/<skill-name>/
```
