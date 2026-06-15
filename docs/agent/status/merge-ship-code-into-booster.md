---
type: status
status: active
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

Implementation complete; PR open: https://github.com/ship-it-ops/booster/pull/6 (commit ba9ce90). All local validation green. Remaining after merge: add `CLAUDE_CODE_OAUTH_TOKEN` repo secret, then decide ship-code repo deprecation. When the PR merges, complete this entry and move it to archive/.
