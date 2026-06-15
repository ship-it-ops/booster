---
type: decision
status: active
created: 2026-06-12
updated: 2026-06-12
author: claude-fable-5
tags: [marketplace, migration, plugins, ship-code]
importance: core
---

# All 6 ship-code plugins migrated into booster; booster is the single marketplace

## Context

The team maintained two plugin marketplace repos with identical architecture: booster (knowledge/planning skills) and ship-code (code-quality skills: ship-clean-code, ship-tested-code, ship-debugged-code, ship-secure-code, ship-reviewed-prs, ship-devops). Two marketplaces meant duplicated CI, validators, docs, and install instructions. User decided 2026-06-11 to consolidate into booster.

## Decision

Migrate all 6 ship-code plugins (skills + plugin wrappers with their 57 per-file symlinks) into booster, keeping versions as-is (ship-clean-code 1.1.0, ship-tested-code 1.1.0, ship-debugged-code 1.0.0, ship-secure-code 1.0.0, ship-reviewed-prs 1.3.1, ship-devops 0.2.0). Booster's tooling wins where the repos diverged:

- **Validator**: kept booster's `scripts/validate-skills.py`; ported from ship-code the plugin file-parity check, `validate_no_skill_dir_leakage`, `validate_fixture_parity`, and the hard plugin.json-name == dir-basename check. Did NOT port ship-code's 500-line SKILL.md cap (booster's 800 is deliberate) or its root-plugin.json `skills`-array requirement (contradicts [plugin-manifest-rejects-skills-field](../scars/plugin-manifest-rejects-skills-field.md)).
- **ship-code's root `.claude-plugin/plugin.json` and `marketplace.json` did not migrate** — the former carries the forbidden `skills` field, the latter relies on the ignored `pluginRoot`.
- **CI**: added the `plugin-symlinks` job to validate.yml; copied pr-review.yml (dogfood workflow) with `ship-reviewed-prs@booster`. Requires `CLAUDE_CODE_OAUTH_TOKEN` repo secret.
- **markdownlint**: added the `skills/*/tests/**/*.md` ignore (fixtures are deliberately malformed).
- **docs/agent**: ship-code's decisions/patterns/scars/open-questions migrated here (they document the migrating skills); its stale pr-4 status entry went to archive/.

## Alternatives Considered

- **Keep two marketplaces**: rejected — duplicate maintenance was the problem being solved.
- **Merge ship-code's validator instead**: rejected — booster's is a superset (hooks validation, marketplace-source checks born from scars).

## Consequences

- Users install everything from `@booster`; `<plugin>@ship-code` installs are superseded.
- The ship-code repo is left untouched for now; deprecating/archiving it is a follow-up user decision.
- ship-execute's delegation to "the ship-code skills" now resolves within the same marketplace.

## Revisit Triggers

- When the ship-code repo is archived, update any external docs pointing at `ship-it-ops/ship-code`.
- If ship-reviewed-prs v2.0.0 ships (see [v2-release-trigger](../open-questions/v2-release-trigger.md)), release it from booster.

## Related

- [marketplace-pluginroot-silently-ignored](../scars/marketplace-pluginroot-silently-ignored.md) — why marketplace.json sources stay inlined
- [plugin-manifest-rejects-skills-field](../scars/plugin-manifest-rejects-skills-field.md) — why ship-code's root plugin.json didn't migrate
- [plugin-name-matches-source-dir](plugin-name-matches-source-dir.md) — naming rule now enforced by the validator
- [pr-review-installs-plugin-from-pr-head](pr-review-installs-plugin-from-pr-head.md) — trust model of the migrated dogfood workflow
