# booster

> Boost your AI agents with powerful tools. An open-source collection of skills, agents, and workflows for supercharging AI-assisted development.

Built on the [Agent Skills open standard](https://agentskills.io) and the Claude Code Skills 2.0 format.

## Featured Skills

Two complementary memory skills — use either one, or both together.

### obsidian-knowledge-graph — cross-repo memory

Turn Obsidian into a persistent, AI-managed knowledge graph. Captures decisions, bug investigations, and codebase patterns as linked notes in a central vault that follows you across every project.

- **Central vault** — One knowledge base across all your repos
- **Cross-project discovery** — A pattern from project A surfaces when working in project B
- **MANIFEST-first retrieval** — Compact index, 1–2 reads to find what you need
- **Scoped writes** — Agent only writes to `_ai/` inside your vault

```bash
npx skills add ship-it-ops/booster --skill obsidian-knowledge-graph
```

### ship-agent-context — in-repo memory

Manages `docs/agent/` inside the repo itself — committed alongside the code so every branch and every agent sees the same handoff context. Designed for the multi-agent / next-agent handoff problem: plans that didn't finish, decisions made and *why*, what's in flight on parallel branches, open questions, and incident scars.

- **Travels with the code** — Lives in git, not an external vault
- **Standalone** — No dependency on Obsidian or any other skill
- **Auto-activates** — Ships a bundled SessionStart hook (when installed via the plugin marketplace) that fires automatically in any repo with `docs/agent/`; silent everywhere else
- **Complements AGENTS.md / CLAUDE.md** — Those hold static rules; this holds dynamic state
- **Parallel-agent coordination** — `status/` entries prevent agents from stomping each other
- **Captures what `git log` doesn't** — Rejected alternatives, blockers, scars, in-flight intent

```bash
# Recommended: install via the plugin marketplace for auto-activation
/plugin install ship-agent-context@booster

# Or, manual install (no bundled hook — see SKILL.md for the CLAUDE.md anchor workaround)
npx skills add ship-it-ops/booster --skill ship-agent-context
```

The two are independent. Use the in-repo one for handoff context that should travel with branches, and the obsidian one for cross-repo pattern reuse.

## Code-Quality Skills

Production-quality review and engineering-practice skills, migrated here from the former `ship-it-ops/ship-code` marketplace. They compose: `ship-reviewed-prs` delegates depth to the others (security → `ship-secure-code`, infra → `ship-devops`, code quality → `ship-clean-code`, tests → `ship-tested-code`).

| Skill | What it covers |
|-------|----------------|
| **ship-clean-code** | Clean code principles for Python/TypeScript/Java — naming, functions, classes, error handling, 66 cataloged code smells |
| **ship-tested-code** | Test design, TDD, mocking, integration testing, flaky-test management, 49 cataloged test smells |
| **ship-debugged-code** | Systematic debugging — reproduction, hypothesis-driven investigation, bisection, root-cause analysis, postmortems |
| **ship-secure-code** | Application security (SEC1–SEC12) — auth, injection, XSS, crypto, secrets, supply chain, SSRF, and more |
| **ship-reviewed-prs** | Multi-persona PR review with lifecycle-aware suppression and decisive APPROVE/REQUEST_CHANGES/COMMENT submission; works locally and fully automated in CI |
| **ship-devops** | DevOps/CI-CD review (DEV1–DEV12) for Terraform, Kubernetes, Docker, and GitHub Actions |
| **ship-vuln-scan** | Known-CVE / vulnerability detection (VS1–VS8) across dependencies, container images, IaC, and secrets. Hybrid: orchestrates real scanners (osv-scanner, trivy, grype, pip-audit, checkov, gitleaks) when present, falls back to manual analysis, and never reports "clean" when it couldn't scan. Triages by CVSS/EPSS/KEV |

```bash
/plugin install ship-clean-code@booster
/plugin install ship-reviewed-prs@booster   # includes the /ship-reviewed-prs:review-pr command
/plugin install ship-vuln-scan@booster
# ...same pattern for ship-tested-code, ship-debugged-code, ship-secure-code, ship-devops
```

## Installation

### Option 1: Add as a marketplace (recommended — get all current and future skills + bundled hooks)

This repo is a Claude Code plugin marketplace. Add it once and get access to all skills — including new ones as they're released:

```bash
# In Claude Code, run:
/plugin marketplace add ship-it-ops/booster

# Then install any skill from the marketplace:
/plugin install <skill-name>@booster

# Examples:
/plugin install ship-agent-context@booster        # in-repo agent memory + auto-activation hook
/plugin install obsidian-knowledge-graph@booster  # AI-managed knowledge graph in your Obsidian vault

# To see all available skills:
/plugin marketplace list booster
```

> **Why this path is recommended**: Some skills (notably `ship-agent-context`) ship a bundled SessionStart hook for guaranteed activation. **Only the marketplace install path activates bundled hooks** — Options 2–7 below install the skill files but skip the hook layer. If a skill's auto-activation matters to you, use Option 1.

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

> **Note for Options 2–7**: These install the skill's files only. They do **not** install plugin-bundled hooks. For `ship-agent-context` specifically, you can recover guaranteed activation by adding the `CLAUDE.md` / `AGENTS.md` anchor described in [`skills/ship-agent-context/examples/initialization-example.md`](skills/ship-agent-context/examples/initialization-example.md).

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
