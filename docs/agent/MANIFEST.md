# Agent Context
Last updated: 2026-06-18 | Total notes: 31

<!--
  This file is the index for `docs/agent/`. Agents read it at session start.
  Format: - [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
-->

## Instructions
<!-- standing user instructions — always-read at session start -->

(none yet — the agent will auto-capture entries here when the user uses persistent-intent phrasing like "always X", "never X", "ask before X")

## Status
<!-- in-flight work and handoffs — always-read at session start -->

- [ship-vuln-skills](status/ship-vuln-skills.md) | status | active | standard | 2026-06-19 | Both ship-vuln-scan + ship-vuln-fix BUILT (branch); pending PR/merge

## Plans

- [ship-vuln-skills-design](plans/ship-vuln-skills-design.md) | plan | completed | core | 2026-06-19 | BUILT: ship-vuln-scan + ship-vuln-fix (branch, APPROVE)
- [ship-better-plans-design](plans/ship-better-plans-design.md) | plan | completed | core | 2026-06-10 | SHIPPED (commit 47be8cc): audited plan-producing skill + plugin
- [ship-execute-design](plans/ship-execute-design.md) | plan | completed | core | 2026-06-11 | SHIPPED (commit 0eeeba8): DAG-aware execution engine + plugin

## Decisions

- [ship-vuln-skills-architecture](decisions/ship-vuln-skills-architecture.md) | decision | active | core | 2026-06-19 | Two skills, hybrid exec, evidence-gated apply, recipe-first (V1-V10)
- [agent-context-initialized](decisions/agent-context-initialized.md) | decision | active | core | 2026-05-20 | Adopt docs/agent as in-repo agent memory
- [plugin-name-matches-source-dir](decisions/plugin-name-matches-source-dir.md) | decision | active | standard | 2026-05-20 | Marketplace plugin name matches source directory basename
- [add-user-instructions-to-skill](decisions/add-user-instructions-to-skill.md) | decision | active | core | 2026-06-02 | Add instructions/ content type for standing user rules
- [ship-better-plans-architecture](decisions/ship-better-plans-architecture.md) | decision | active | core | 2026-06-10 | Parallel skill, Workflow audit, plan-mode + opt-in control flow (D1-D7)
- [ship-execute-architecture](decisions/ship-execute-architecture.md) | decision | active | core | 2026-06-11 | Standalone DAG-aware executor; ship-code delegation (E1-E5)
- [merge-ship-code-into-booster](decisions/merge-ship-code-into-booster.md) | decision | active | core | 2026-06-12 | All 6 ship-code plugins migrated; booster is the single marketplace
- [pr-review-installs-plugin-from-pr-head](decisions/pr-review-installs-plugin-from-pr-head.md) | decision | active | core | 2026-05-25 | Dogfood workflow uses local checkout, not main URL
- [relaxed-approve-decision-matrix](decisions/relaxed-approve-decision-matrix.md) | decision | active | core | 2026-05-25 | APPROVE allowed with suggestions and pending CI caveats
- [pr-review-table-driven-summary-format](decisions/pr-review-table-driven-summary-format.md) | decision | active | core | 2026-05-26 | Summary body adopts tables and LGTM-style verdict labels
- [pr-review-auto-resolves-own-threads](decisions/pr-review-auto-resolves-own-threads.md) | decision | active | core | 2026-05-28 | Auto-resolve bot-authored threads when finding no longer fires
- [ship-devops-12-category-catalog](decisions/ship-devops-12-category-catalog.md) | decision | active | core | 2026-06-02 | DEV1-DEV12 rubric for new ship-devops skill
- [in-persona-delegates-to-ship-devops](decisions/in-persona-delegates-to-ship-devops.md) | decision | active | core | 2026-06-02 | IN persona depth target wired to ship-devops
- [askuserquestion-denial-failsafe-to-submission](decisions/askuserquestion-denial-failsafe-to-submission.md) | decision | active | core | 2026-06-07 | AskUserQuestion denial at gate switches to CI submit

## Patterns

- [plugin-command-discovery](patterns/plugin-command-discovery.md) | pattern | active | core | 2026-05-25 | Plugin slash commands live at commands/<name>.md namespaced
- [pr-review-summary-body-layout](patterns/pr-review-summary-body-layout.md) | pattern | active | core | 2026-05-26 | Canonical layout: Verdict + three tables + conditional sections

## Investigations

- [ship-better-plans-design-audit](investigations/ship-better-plans-design-audit.md) | investigation | active | core | 2026-06-09 | Audit found plan unbuildable as written; layout+control-flow fixes

## Open Questions

- [v2-release-trigger](open-questions/v2-release-trigger.md) | open-question | active | standard | 2026-05-25 | When do we cut ship-reviewed-prs v2.0.0 release

## Scars

- [tool-policy-guard-bypassable-by-omission](scars/tool-policy-guard-bypassable-by-omission.md) | scar | active | standard | 2026-06-18 | Policy check that skips on missing field is bypassable
- [marketplace-pluginroot-silently-ignored](scars/marketplace-pluginroot-silently-ignored.md) | scar | active | core | 2026-05-20 | Claude Code installer ignores marketplace pluginRoot field
- [plugin-manifest-rejects-skills-field](scars/plugin-manifest-rejects-skills-field.md) | scar | active | core | 2026-05-20 | plugin.json skills field rejected by installer schema
- [plugin-without-commands-runs-silently](scars/plugin-without-commands-runs-silently.md) | scar | active | core | 2026-05-25 | Skill-only plugin runs 5 min posting nothing
- [bare-slash-command-unknown-in-action](scars/bare-slash-command-unknown-in-action.md) | scar | active | core | 2026-05-25 | Headless SDK needs /plugin:command form not bare
- [oauth-token-whitespace-silent-fail](scars/oauth-token-whitespace-silent-fail.md) | scar | active | standard | 2026-05-25 | Whitespace in OAuth secret kills run silently
- [hidden-output-blocks-debugging](scars/hidden-output-blocks-debugging.md) | scar | active | core | 2026-05-25 | show_full_output false hides Unknown-command and auth diagnostics
- [marketplace-local-path-needs-leading-slash](scars/marketplace-local-path-needs-leading-slash.md) | scar | active | core | 2026-05-26 | `plugin_marketplaces: '.'` rejected; needs `./` prefix
- [ci-mode-auto-detect-unreliable](scars/ci-mode-auto-detect-unreliable.md) | scar | active | core | 2026-05-26 | `CI=true` autodetect fails inside action; pass `--non-interactive` explicitly
