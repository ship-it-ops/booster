# Agent context

<!-- Generated from the notes' frontmatter by ship-agent-context (`agent_context.py index`).
     Do not edit by hand; if this file conflicts in a merge, regenerate it. -->

## Unfinished work

- [ship-skills-refresh-handoff](status/ship-skills-refresh-handoff.md) — Skills refresh: 8 of 12 done, ship-debugged-code in progress; the method, what the user asked for, and what is next

## Instructions

- [no-claude-attribution-in-commits](instructions/no-claude-attribution-in-commits.md) — No Co-Authored-By or Claude-Session lines in commits
- [no-push-or-pull-request-without-being-asked](instructions/no-push-or-pull-request-without-being-asked.md) — Never push or open a pull request unless the user asks in this session; each push is approved one at a time

## Plans

- [ship-better-plans-design](plans/ship-better-plans-design.md) — SHIPPED (commit 47be8cc): audited plan-producing skill + plugin *(completed)*
- [ship-execute-design](plans/ship-execute-design.md) — SHIPPED (commit 0eeeba8): DAG-aware execution engine + plugin *(completed)*
- [ship-vuln-skills-design](plans/ship-vuln-skills-design.md) — SHIPPED (commit 536bee9): ship-vuln-scan + ship-vuln-fix CVE skills *(completed)*

## Decisions

- [add-user-instructions-to-skill](decisions/add-user-instructions-to-skill.md) — Add instructions/ content type for standing user rules
- [agent-context-initialized](decisions/agent-context-initialized.md) — Adopt docs/agent as in-repo agent memory
- [askuserquestion-denial-failsafe-to-submission](decisions/askuserquestion-denial-failsafe-to-submission.md) — AskUserQuestion denial at gate switches to CI submit
- [in-persona-delegates-to-ship-devops](decisions/in-persona-delegates-to-ship-devops.md) — IN persona depth target wired to ship-devops
- [merge-ship-code-into-booster](decisions/merge-ship-code-into-booster.md) — All 6 ship-code plugins migrated; booster is the single marketplace
- [plugin-name-matches-source-dir](decisions/plugin-name-matches-source-dir.md) — Marketplace plugin name matches source directory basename
- [pr-review-auto-resolves-own-threads](decisions/pr-review-auto-resolves-own-threads.md) — Auto-resolve bot-authored threads when finding no longer fires
- [pr-review-installs-plugin-from-pr-head](decisions/pr-review-installs-plugin-from-pr-head.md) — Dogfood workflow uses local checkout, not main URL
- [pr-review-table-driven-summary-format](decisions/pr-review-table-driven-summary-format.md) — Summary body adopts tables and LGTM-style verdict labels
- [relaxed-approve-decision-matrix](decisions/relaxed-approve-decision-matrix.md) — APPROVE allowed with suggestions and pending CI caveats
- [ship-agent-context-refresh](decisions/ship-agent-context-refresh.md) — ship-agent-context 1.3 rewrite: digest hook, notes as a colleague's notes, script-checked hand-offs, generated index (C1-C12)
- [ship-better-plans-architecture](decisions/ship-better-plans-architecture.md) — Parallel skill, Workflow audit, plan-mode + opt-in control flow (D1-D7)
- [ship-better-plans-v2-refresh](decisions/ship-better-plans-v2-refresh.md) — 2.0 rewrite: cards, linter, grounded review; revises D6/Q3
- [ship-clean-code-refresh](decisions/ship-clean-code-refresh.md) — ship-clean-code 1.2 rewrite: one test and three rules, severity by consequence, caller's format wins, restraint when writing (K1-K14)
- [ship-devops-12-category-catalog](decisions/ship-devops-12-category-catalog.md) — DEV1-DEV12 rubric for new ship-devops skill
- [ship-devops-refresh](decisions/ship-devops-refresh.md) — ship-devops 0.3 rewrite: what breaks when and for whom, run rules by what a command touches, writing guidance, no verdicts (V1-V12)
- [ship-execute-architecture](decisions/ship-execute-architecture.md) — Standalone DAG-aware executor; ship-code delegation (E1-E5)
- [ship-execute-v2-refresh](decisions/ship-execute-v2-refresh.md) — 2.0 rewrite: plan reader, git protocol, local review; revises E5
- [ship-reviewed-prs-refresh](decisions/ship-reviewed-prs-refresh.md) — 1.4 rewrite: review script, lenses, thread dispositions (R1-R13)
- [ship-secure-code-refresh](decisions/ship-secure-code-refresh.md) — ship-secure-code 1.1 rewrite: a finding is a traced path, no verdicts, nothing in the repo can switch a finding off, writing guidance (S1-S12)
- [ship-tested-code-refresh](decisions/ship-tested-code-refresh.md) — ship-tested-code 1.2 rewrite: would the test fail if the behaviour were wrong; integrity when writing tests (T1-T12)
- [ship-vuln-skills-architecture](decisions/ship-vuln-skills-architecture.md) — Two skills, hybrid exec, evidence-gated apply, recipe-first (V1-V10)

## Patterns

- [plugin-command-discovery](patterns/plugin-command-discovery.md) — Plugin slash commands live at commands/<name>.md namespaced
- [pr-review-summary-body-layout](patterns/pr-review-summary-body-layout.md) — Old summary layout; superseded by the ship-reviewed-prs rewrite *(superseded)*

## Investigations

- [ship-agent-context-refresh-audit](investigations/ship-agent-context-refresh-audit.md) — ship-agent-context audit: six reviewers, three judged scenarios (pick-up, capture, no folder), three rounds
- [ship-better-plans-design-audit](investigations/ship-better-plans-design-audit.md) — Audit found plan unbuildable as written; layout+control-flow fixes
- [ship-better-plans-refresh-audit](investigations/ship-better-plans-refresh-audit.md) — Six-persona audit plus before/after evaluation of ship-better-plans
- [ship-clean-code-refresh-audit](investigations/ship-clean-code-refresh-audit.md) — ship-clean-code audit: six reviewers, three judged scenarios, a no-skill control, three rounds
- [ship-devops-refresh-audit](investigations/ship-devops-refresh-audit.md) — ship-devops audit: six reviewers, three judged scenarios, four writing fixtures, a no-skill control, three rounds
- [ship-execute-refresh-audit](investigations/ship-execute-refresh-audit.md) — Six-persona audit, judged executions, live worktree tests
- [ship-reviewed-prs-refresh-audit](investigations/ship-reviewed-prs-refresh-audit.md) — Six-persona audit, judged reviews of seeded pull requests
- [ship-secure-code-refresh-audit](investigations/ship-secure-code-refresh-audit.md) — ship-secure-code audit: six reviewers, three judged scenarios, a no-skill control, three rounds
- [ship-tested-code-refresh-audit](investigations/ship-tested-code-refresh-audit.md) — ship-tested-code audit: six reviewers, three judged scenarios, a no-skill control, three rounds

## Open questions

- [v2-release-trigger](open-questions/v2-release-trigger.md) — Still open: rewrite shipped as 1.4.0, v2 held back

## Scars

- [bare-slash-command-unknown-in-action](scars/bare-slash-command-unknown-in-action.md) — Headless SDK needs /plugin:command form not bare
- [ci-mode-auto-detect-unreliable](scars/ci-mode-auto-detect-unreliable.md) — `CI=true` autodetect fails inside action; pass `--non-interactive` explicitly
- [hidden-output-blocks-debugging](scars/hidden-output-blocks-debugging.md) — show_full_output false hides Unknown-command and auth diagnostics
- [marketplace-local-path-needs-leading-slash](scars/marketplace-local-path-needs-leading-slash.md) — `plugin_marketplaces: '.'` rejected; needs `./` prefix
- [marketplace-pluginroot-silently-ignored](scars/marketplace-pluginroot-silently-ignored.md) — Claude Code installer ignores marketplace pluginRoot field
- [oauth-token-whitespace-silent-fail](scars/oauth-token-whitespace-silent-fail.md) — Whitespace in OAuth secret kills run silently
- [plugin-manifest-rejects-skills-field](scars/plugin-manifest-rejects-skills-field.md) — plugin.json skills field rejected by installer schema
- [plugin-without-commands-runs-silently](scars/plugin-without-commands-runs-silently.md) — Skill-only plugin runs 5 min posting nothing
- [tool-policy-guard-bypassable-by-omission](scars/tool-policy-guard-bypassable-by-omission.md) — Policy check that skips on missing field is bypassable
