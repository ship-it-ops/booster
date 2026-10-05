# Skills

Ready-to-use AI skills for supercharging development. Each skill follows the [Skills 2.0 format](../docs/writing-skills.md) with a `SKILL.md` entry point.

Skills live at `skills/<skill-name>/` — one flat directory per skill, no nested subfolders.

## Available Skills

| Skill | Description |
|-------|-------------|
| [obsidian-knowledge-graph](obsidian-knowledge-graph/) | Turn Obsidian into an AI-managed knowledge graph. Captures architecture decisions, bug investigations, and codebase patterns as persistent memory across coding sessions. |
| [ship-agent-context](ship-agent-context/) | In-repo memory for AI agents. Manages `docs/agent/` — committed plans, decisions, in-flight status, open questions, and incident scars — so the next agent (or human) walks into context, not a blank slate. Standalone; complements `AGENTS.md`/`CLAUDE.md`. |
| [ship-better-plans](ship-better-plans/) | Write implementation plans that survive execution: codebase discovery before questions, one checkpoint with the user, self-contained task cards, a plan linter (traceability, dependency graph, parallel safety), and an independent multi-reviewer audit with verified findings. Built by `ship-execute`. |
| [ship-execute](ship-execute/) | Build an approved plan: one fresh agent and one commit per task, parallel worktrees for independent tasks, every check re-run on the execution branch, gates on irreversible steps, a resumable run ledger, an independent review, and an honest report. Never pushes without your say-so. |
| [ship-clean-code](ship-clean-code/) | Review code for quality, or clean it up, the way this project would: the project's conventions outrank generic rules, findings are rated by consequence and verified before they are reported, a change stays inside the request, and "nothing needs changing" is a valid review. Any language, with notes for Python, TypeScript/JavaScript and Java. |
| [ship-tested-code](ship-tested-code/) | Apply testing best practices when writing or reviewing tests for Python, TypeScript/JavaScript, or Java code. Covers test design, TDD, test strategy, mocking, integration testing, flaky test management, and 49 cataloged test smells. |
| [ship-debugged-code](ship-debugged-code/) | Apply systematic debugging practices when investigating, isolating, or fixing bugs. Covers reproduction, hypothesis-driven investigation, bisection, root-cause analysis, observability, regression-test design, and postmortems. |
| [ship-secure-code](ship-secure-code/) | Application-security review (SEC1–SEC12: auth, input validation, injection, XSS, CSRF/origin, crypto, secrets, supply chain, PII/logging, resource exhaustion, path traversal, deserialization/SSRF) for Python, TypeScript/JavaScript, and Java. |
| [ship-reviewed-prs](ship-reviewed-prs/) | Multi-persona pull-request review (senior engineer, security, infra/SRE, data, frontend, test-coverage signal) with comment-lifecycle suppression and decisive APPROVE/REQUEST_CHANGES/COMMENT submission. Runs locally with confirmation gating and fully automated in CI. |
| [ship-devops](ship-devops/) | DevOps and CI/CD review (DEV1–DEV12: CI pipelines, deployment safety, IaC, containers, secrets/config, observability, releases, migrations, health/readiness, SLO/performance, incident hygiene, flow) for Terraform, Kubernetes, Docker, and GitHub Actions. |

## Installation

See [Installing Skills](../docs/installing-skills.md) for setup instructions.

## Creating a New Skill

1. Create a new directory under `skills/` with your skill name
2. Copy a template from [templates/](../templates/)
3. Customize the `SKILL.md` frontmatter and instructions
4. Test it in Claude Code with `/skill-name`
5. Submit a PR
