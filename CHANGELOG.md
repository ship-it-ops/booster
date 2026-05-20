# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Initial project structure with skills, agents, workflows, templates, and examples directories
- Contributing guidelines
- Starter templates for creating new skills, agents, and workflows
- **obsidian-knowledge-graph** skill — AI-managed knowledge graph in Obsidian vaults for persistent memory across coding sessions
- **ship-agent-context** skill — In-repo agent memory in `docs/agent/`. Captures plans, decisions, in-flight status, open questions, and incident scars so successive agents inherit context instead of starting blind. Standalone; pairs with but does not depend on `obsidian-knowledge-graph`
- **ship-agent-context** plugin-bundled SessionStart hook — When installed via the plugin marketplace, the skill ships a `hooks/hooks.json` that auto-activates in any repo containing `docs/agent/MANIFEST.md`. Silent in repos without `docs/agent/`. Guarantees session-start activation without users editing `settings.json`.
