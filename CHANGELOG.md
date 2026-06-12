# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **Migrated all 6 plugins from `ship-it-ops/ship-code`** — booster is now the single marketplace: **ship-clean-code** 1.1.0, **ship-tested-code** 1.1.0, **ship-debugged-code** 1.0.0, **ship-secure-code** 1.0.0, **ship-reviewed-prs** 1.3.1 (with the `/ship-reviewed-prs:review-pr` command), **ship-devops** 0.2.0. Versions carried over unchanged; install with `<plugin>@booster`.
- **PR dogfood workflow** — `.github/workflows/pr-review.yml` (from ship-code) runs ship-reviewed-prs against PRs to this repo. Requires the `CLAUDE_CODE_OAUTH_TOKEN` repo secret.
- **Validator checks ported from ship-code** — plugin file-parity (every skill file must have a plugin symlink; orphans are errors), `${SKILL_DIR}` leakage detection, test-fixture parity, and plugin.json name == directory basename. Plus a `plugin-symlinks` CI job that verifies symlinks survive checkout.
- ship-code's `docs/agent/` knowledge (decisions, patterns, scars, open questions about the migrated skills) merged into booster's `docs/agent/`.

- Initial project structure with skills, agents, workflows, templates, and examples directories
- Contributing guidelines
- Starter templates for creating new skills, agents, and workflows
- **obsidian-knowledge-graph** skill — AI-managed knowledge graph in Obsidian vaults for persistent memory across coding sessions
- **ship-agent-context** skill — In-repo agent memory in `docs/agent/`. Captures plans, decisions, in-flight status, open questions, and incident scars so successive agents inherit context instead of starting blind. Standalone; pairs with but does not depend on `obsidian-knowledge-graph`
- **ship-agent-context** plugin-bundled SessionStart hook — When installed via the plugin marketplace, the skill ships a `hooks/hooks.json` that auto-activates in any repo containing `docs/agent/MANIFEST.md`. Silent in repos without `docs/agent/`. Guarantees session-start activation without users editing `settings.json`.
- **CI validation workflow** — `.github/workflows/validate.yml` runs on every push to `main` and every PR. Six jobs: SKILL.md frontmatter + plugin layout + marketplace consistency + bundled hooks (`scripts/validate-skills.py`), relative-link integrity (`scripts/check-skill-links.py`), markdown lint, JSON validity, YAML validity, plus a summary gate. See `CONTRIBUTING.md` for the local-equivalent commands.

### Fixed

- Root `.claude-plugin/plugin.json` `skills` array now includes `./skills/ship-agent-context` (regression caught while writing the new validator).
