---
type: status
status: completed
created: 2026-06-12
updated: 2026-06-12
author: claude-fable-5
branch: merge-repos
agent: claude-session-2026-06-12
tags: [marketplace, migration, plugins]
---

# Migrating all 6 ship-code plugins into booster (single marketplace)

## Scope

`skills/` + `plugins/` (6 new each: ship-clean-code, ship-tested-code, ship-debugged-code, ship-secure-code, ship-reviewed-prs, ship-devops), `.claude-plugin/marketplace.json`, `scripts/validate-skills.py`, `scripts/check-skill-links.py`, `.markdownlint-cli2.yaml`, `.github/workflows/` (validate.yml + new pr-review.yml), `docs/agent/` (ship-code knowledge merge), READMEs/CHANGELOG.

## Why

User decision 2026-06-11: consolidate the two marketplaces into booster. Decision note: `../decisions/merge-ship-code-into-booster.md`.

## Current state

COMPLETED — PR #6 merged as commit 5b40712 (main). Archived 2026-06-18. Follow-ups still open outside this entry: add `CLAUDE_CODE_OAUTH_TOKEN` repo secret; decide ship-code repo deprecation.
