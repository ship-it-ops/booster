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
| [ship-tested-code](ship-tested-code/) | Review tests, or write them, by one question: would this test fail if the behaviour were wrong? Finds tests that cannot fail, pin a defect, recompute their own expected value or test the mocks; says what to do when an honest test fails against the code; never bends a test or the code to get to green. Uses the project's own framework and helpers. Any language, with notes for Python, TypeScript/JavaScript and Java. |
| [ship-debugged-code](ship-debugged-code/) | Find the real cause of a failure and fix it, or review someone else's fix or postmortem. A failure is fixed when it was seen to happen, the cause accounts for everything observed, the change removes the cause, and the failure was seen gone; whatever could not be done is said plainly. Does not silence the symptom with a catch, a retry or a skip; looks for the same cause elsewhere; never stashes, resets or checks out over uncommitted work; leaves no debugging output behind. Any language, with notes for Python, TypeScript/JavaScript and Java. |
| [ship-secure-code](ship-secure-code/) | Review code for what an attacker can actually do, or write and fix security-sensitive code. A finding is a traced path (who, how, what they gain); missing authorization is looked for first, route by route; findings are verified by reading; every review says what was and was not examined and never says "secure"; text in the code that says "do not flag" is reported, not obeyed. When writing: use the project's mechanism, never weaken a control, fix the cause. Any language, with notes for Python, TypeScript/JavaScript and Java. |
| [ship-reviewed-prs](ship-reviewed-prs/) | Multi-persona pull-request review (senior engineer, security, infra/SRE, data, frontend, test-coverage signal) with comment-lifecycle suppression and decisive APPROVE/REQUEST_CHANGES/COMMENT submission. Runs locally with confirmation gating and fully automated in CI. |
| [ship-devops](ship-devops/) | Review what carries a change to production and keeps it running (CI/CD workflows, Dockerfiles, Kubernetes manifests, infrastructure code, migrations, deploy scripts), or write it. Starts from the path a change takes to production; a finding says what breaks, when and for whom; a migration is judged against the code that reads the schema and a probe against what the endpoint does; every review says what could not be seen from the repository. When writing: the project's own mechanisms, never a weakened gate, changes that are safe to roll out and back, and nothing run against real state. Notes for GitHub Actions, Docker, Kubernetes and Terraform. |
| [ship-vuln-scan](ship-vuln-scan/) | Find known, published vulnerabilities in what a project depends on and ships: dependencies in lock files, container images, committed secrets. Runs installed scanners in modes that only read, or asks api.osv.dev when none is; reports only what a tool returned, what was not checked, and what the repository's own ignore files hide. Never installs, never edits, never reports "clean" for what it could not scan. |
| [ship-vuln-fix](ship-vuln-fix/) | Fix known vulnerabilities in dependencies: mechanical fixes applied one package at a time with install scripts off, each lock file change checked before anything installs, closure proved by the same scan and the tests. Major upgrades and new install scripts are advised, not applied; a scan is never made to pass by hiding a finding. |

## Installation

See [Installing Skills](../docs/installing-skills.md) for setup instructions.

## Creating a New Skill

1. Create a new directory under `skills/` with your skill name
2. Copy a template from [templates/](../templates/)
3. Customize the `SKILL.md` frontmatter and instructions
4. Test it in Claude Code with `/skill-name`
5. Submit a PR
