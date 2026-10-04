export const meta = {
  name: 'ship-better-plans-refresh-eval',
  description: 'Six-persona audit of the ship-better-plans skill, plus the skill planning two real scenarios in this repo with each plan judged by a cold-read executor and a grounding checker',
  phases: [
    { title: 'Persona audit', detail: 'six independent reviewers read the skill through different lenses' },
    { title: 'Plan scenarios', detail: 'the skill under test plans two real scenarios in this repo' },
    { title: 'Judge plans', detail: 'cold-read executor and grounding checker per plan' },
  ],
}

const A = args || {}
const REPO = '/path/to/booster'
const SCRATCH = '/path/to/scratch'
const RUN = A.run || ['personas', 'plans']
const VARIANT = A.variant || 'old'
const SKILL_DIR = A.skillDir || `${SCRATCH}/old-skill`
const EVAL_DIR = `${SCRATCH}/eval/${VARIANT}`

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          title: { type: 'string' },
          severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
          evidence: { type: 'string' },
          impact: { type: 'string' },
          recommendation: { type: 'string' },
        },
        required: ['id', 'title', 'severity', 'evidence', 'impact', 'recommendation'],
      },
    },
    keep: { type: 'array', items: { type: 'string' } },
    topThree: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'keep', 'topThree'],
}

const SKILL_FILES = [
  `${REPO}/skills/ship-better-plans/SKILL.md`,
  `${REPO}/skills/ship-better-plans/reference.md`,
  `${REPO}/skills/ship-better-plans/workflows/audit.workflow.js`,
  `${REPO}/skills/ship-better-plans/templates/plan.md`,
  `${REPO}/skills/ship-better-plans/examples/example-plan-feature.md`,
  `${REPO}/skills/ship-better-plans/examples/example-plan-refactor.md`,
  `${REPO}/plugins/ship-better-plans/commands/ship-plan.md`,
  ...(A.rewrite ? [`${REPO}/skills/ship-better-plans/scripts/lint_plan.py`, `${REPO}/skills/ship-better-plans/examples/example-plan-small.md`] : []),
].join('\n  ')

const EXEC_FILES = [
  `${REPO}/skills/ship-execute/SKILL.md`,
  `${REPO}/skills/ship-execute/reference.md`,
  `${REPO}/skills/ship-execute/workflows/execute.workflow.js`,
].join('\n  ')

const COMMON = `You are one of several independent reviewers auditing a Claude Code skill named ship-better-plans. A skill is a set of instructions an AI coding agent loads and follows. This skill's job is to make the agent produce the best possible implementation plan for non-trivial development work; a separate skill, ship-execute, then builds from that plan using fresh subagents. ${A.rewrite ? 'The skill has just been rewritten from scratch for current models and the current harness, and this is the review before it ships. Your review decides what gets fixed first.' : 'The skill was written months ago for older models and an older harness, and it is getting a full refresh. Your review decides what changes.'}

Read these files in full before judging:
  ${SKILL_FILES}

The downstream executor, for reference when you need it:
  ${EXEC_FILES}

Report concrete findings. For each: what is wrong or weak, the evidence (file plus line number or a short quote), how it leads to a worse plan or a worse experience, and the specific change you recommend. Severity: critical means plans produced will often be wrong, unexecutable, or the skill breaks; major means a real and recurring quality or usability loss; minor means polish. Report honestly: if something works, list it under keep rather than inventing a problem, and do not pad the list. In topThree, give the three changes that would most improve the plans this skill produces, most important first. Prefix finding ids with your persona key.

Your lens:
`

const PERSONAS = [
  {
    key: 'prompt',
    lens: `You are an expert at writing instructions for current frontier models (the Claude 5 family), which follow instructions closely and literally. Judge how a capable model will actually read and act on this text. Look at: whether the frontmatter description does its job of triggering at the right moments, and whether it summarizes the procedure in a way the model could follow instead of reading the body; instructions duplicated or contradicting each other across SKILL.md, reference.md and the command file; instructions that are ambiguous, impossible to follow, or that refer to context the running agent will not have; emphatic or rigid wording that would make a responsive model over-apply a rule; rules given without their reason; what gets loaded when, and the token cost of that against its value.`,
  },
  {
    key: 'coldstart',
    lens: `Simulate being the agent that has just had this skill loaded. Walk through it literally, step by step, for the request "add per-tenant rate limiting to our Express API" in a mid-size TypeScript monorepo, three times: in normal mode, in Claude Code plan mode, and running headless with no user available to answer questions. The session running this audit has these tools: Read, Write, Edit, Bash, Agent (subagent dispatch; there is no tool named Task), AskUserQuestion (1 to 4 questions per call, each with 2 to 4 options), Workflow, Skill, EnterPlanMode and ExitPlanMode; there is no TodoWrite. At each step note what exactly you would do, and where the instruction is ambiguous, contradictory, impossible with those tools, or would make you stall, pad a section with filler, or guess. Count the user round trips before the user sees any value.`,
  },
  {
    key: 'executor',
    lens: `You are the downstream consumer. Read the ship-execute files first, then the plan template and both example plans. If you were handed a plan in exactly this format and had to execute it with fresh subagents that each see only their own task brief, what is missing or ambiguous? Check the contract field by field: execute.workflow.js needs, per task, an id, a prompt, acceptance criteria, a verify command and likely file paths. Check how the dependency graph is represented and whether it can be read unambiguously, whether tasks marked parallel could collide on files, whether verification is concrete enough to run, and whether every requirement traces to a task and every task to a requirement.`,
  },
  {
    key: 'staff',
    lens: `You are a staff engineer who has written and reviewed hundreds of implementation plans and design docs and has seen which ones survive contact with execution. Judge whether following this process reliably yields the optimal plan rather than a merely plausible one. Evaluate intake, discovery, how options are generated and scored, risk handling, the specification, task decomposition and sequencing, and the verification strategy. Which proven planning practices are absent? Which steps are ceremony that adds length without improving outcomes? Where would this process produce plans that look rigorous but are wrong, for example claims about the codebase nobody checked, or alternatives that exist only to be rejected?`,
  },
  {
    key: 'auditharness',
    lens: `Focus on the audit phase: workflows/audit.workflow.js, the persona prompts, and what the skill does with the results. Check the script against the Workflow runtime it runs on, the convergence behaviour of ultra mode, deduplication, the false-negative and false-positive dynamics of the refute pass, what the reviewers can and cannot see or verify, how personas are chosen and how good their prompts are, whether the cost can actually be estimated as the skill promises, and how findings get folded back into the plan.

Workflow runtime facts: scripts are plain JavaScript and start with a pure-literal export const meta. agent(prompt, opts) spawns a subagent that has the session's normal tools (it can read the repository); opts are label, phase, schema (JSON Schema, forces a validated structured result), model, effort (low, medium, high, xhigh, max), isolation, agentType. agent() returns null if the agent is skipped or dies. parallel(thunks) is a barrier that awaits all thunks and yields null for any that throw. pipeline(items, stage1, stage2, ...) runs each item through the stages independently; a stage receives (prevResult, originalItem, index); a throwing stage drops the item to null. log(msg) shows progress. args is the caller's input verbatim. budget exposes total, spent() and remaining() for a user-set token target (total is null when none is set). Roughly 10 to 16 agents run concurrently; a workflow may spawn at most 1000 agents in total. Date.now, Math.random and argless new Date throw. There is no filesystem access from the script itself.`,
  },
  {
    key: 'dx',
    lens: `You are a senior developer who uses Claude Code every day and is deciding whether to keep this plugin installed. Judge the experience across a whole session: time to first value, number of questions and round trips, confirmation gates, token cost, how it behaves on mid-sized tasks that are neither trivial nor huge, how it interacts with Claude Code's built-in plan mode and with other planning skills, how it behaves when nobody is there to answer, and the point at which you would abandon it and just ask the model to plan. What would make you trust the plans and keep using it?`,
  },
]

const SCENARIOS = [
  {
    key: 'cmd-validation',
    request: `CI should catch broken plugin slash commands. scripts/validate-skills.py checks SKILL.md files and the plugin layout, but nothing validates plugins/*/commands/*.md, and we have been burned by that before. Add that validation, wire it into CI, and document it.`,
    answers: `Success means: a command file with missing or malformed frontmatter, or without a description, makes python3 scripts/validate-skills.py exit non-zero, and therefore fails CI. Python standard library only, no new dependencies. Existing checks and their output format keep working. No change to how plugins install. Not in scope: validating hook scripts or the content of skills. I am the only approver. Effort: small to medium, ideally a single PR.`,
  },
  {
    key: 'symlink-migration',
    request: `The per-file symlinks under plugins/*/skills/* keep biting us (Windows checkouts, and some installers do not follow symlinks). I want to move to generated copies: a sync script that copies skills/<name>/ into plugins/<name>/skills/<name>/, plus CI that fails if they drift. Plan the migration.`,
    answers: `Success means: a fresh git clone on Windows followed by a plugin install works, with no symlinks left in the repo; skills/ stays the single source of truth that humans edit; CI fails when a copy is stale. main must stay installable at every commit, because people install straight from main. Not in scope: renaming plugins or changing the version scheme. Python standard library only. I am the only approver. Several PRs are fine if that is safer.`,
  },
]

const PLAN_RUN_SCHEMA = {
  type: 'object',
  properties: {
    planPath: { type: 'string' },
    otherFiles: { type: 'array', items: { type: 'string' } },
    phasesRun: { type: 'string' },
    questionsTheSkillWantedAsked: { type: 'array', items: { type: 'string' } },
    couldNotFollow: { type: 'array', items: { type: 'string' } },
  },
  required: ['planPath', 'phasesRun', 'couldNotFollow'],
}

const EXECUTOR_SCHEMA = {
  type: 'object',
  properties: {
    executabilityScore: { type: 'integer' },
    ambiguities: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          task: { type: 'string' },
          issue: { type: 'string' },
          severity: { type: 'string', enum: ['blocking', 'costly', 'minor'] },
        },
        required: ['task', 'issue', 'severity'],
      },
    },
    uncoveredRequirements: { type: 'array', items: { type: 'string' } },
    parallelConflicts: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['executabilityScore', 'ambiguities', 'uncoveredRequirements', 'parallelConflicts', 'summary'],
}

const GROUNDING_SCHEMA = {
  type: 'object',
  properties: {
    groundingScore: { type: 'integer' },
    claimsChecked: { type: 'integer' },
    falseClaims: {
      type: 'array',
      items: {
        type: 'object',
        properties: { claim: { type: 'string' }, reality: { type: 'string' } },
        required: ['claim', 'reality'],
      },
    },
    unverifiable: { type: 'array', items: { type: 'string' } },
    missedFacts: {
      type: 'array',
      items: {
        type: 'object',
        properties: { fact: { type: 'string' }, whyItMatters: { type: 'string' } },
        required: ['fact', 'whyItMatters'],
      },
    },
    approachAssessment: { type: 'string' },
    summary: { type: 'string' },
  },
  required: ['groundingScore', 'claimsChecked', 'falseClaims', 'missedFacts', 'approachAssessment', 'summary'],
}

function planPrompt(s) {
  const out = `${EVAL_DIR}/${s.key}`
  return `You are working as a Claude Code agent in the repository at ${REPO}. A planning skill has been loaded for you. Read ${SKILL_DIR}/SKILL.md and follow it as written. It refers to sibling files in the same directory (reference material, templates, examples, a workflow script); read whatever it tells you to read, when it tells you to.

The user's request:
"${s.request}"

Conditions for this run:
- The user is not available for live questions. Wherever the skill has you ask the user something, take the answer from "User answers" below. If the answer is not there, do whatever the skill says to do when information is missing, and record the question in your result.
- If the skill reaches a point where it asks the user whether to run its paid multi-agent audit, the user's answer is: no review, the linter only.
- You are not in plan mode.
- Do not create or change any file inside ${REPO}. Wherever the skill would write under docs/agent/, write under ${out}/docs-agent/ instead, keeping the same sub-paths. Reading the repository, including its docs/agent/ directory, is expected.
- If the skill tells you to dispatch subagents and you have no tool for that, do that work yourself.
- When the skill ends by offering the user a choice of what to do next, stop there.
- Where the skill text says \${CLAUDE_SKILL_DIR}, it means the directory that contains SKILL.md: ${SKILL_DIR}

User answers:
${s.answers}

Your result: the absolute path of the plan file you wrote, any other files you wrote, a one-paragraph account of which phases you ran and how, every question the skill wanted asked of the user, and every instruction in the skill you could not follow or found unclear.`
}

function executorPrompt(planPath) {
  return `You are an engineer agent who has been handed an implementation plan and will be asked to execute it. You can read the repository at ${REPO}, but you cannot reach the people who wrote the plan, and you must not change anything.

Read the plan at ${planPath}.

Execution will work like this: each task is given to a fresh subagent that sees only that task's own text plus whatever the plan says to hand it, not the whole plan. Independent tasks may run at the same time in separate git worktrees and are merged afterwards.

Go through the plan task by task and judge whether it can be executed as written. Report every point where an executor would have to guess, ask, or re-derive something: missing or vague file paths, missing commands, done-criteria that cannot be checked, unclear ordering or dependencies, tasks that would collide if run in parallel, requirements that no task delivers, tasks that serve no requirement. Check claims against the repository where that tells you whether a task is doable. Severity: blocking means the task cannot be completed correctly without outside input; costly means the executor will likely waste effort or build the wrong thing; minor is polish.

Give an executabilityScore from 1 (cannot be executed without rewriting the plan) to 10 (a fresh subagent per task could complete and prove every task with no questions).`
}

function groundingPrompt(planPath, s) {
  return `An implementation plan was written for the repository at ${REPO} in response to this request:
"${s.request}"

Read the plan at ${planPath}, then check it against the actual repository. Do not change anything.

1. Verify every factual claim the plan makes about the repository: file paths, function and variable names, existing behaviour, commands, CI jobs, constraints, earlier decisions. Count the claims you checked. List each one that is false, with what is actually true. List separately those you could not verify.
2. List facts in the repository that bear on this request and that the plan missed or ignored, where knowing them would change the plan. Look at the code involved, the CI workflows, and the notes under docs/agent/ (decisions, scars, patterns).
3. In approachAssessment, say whether the chosen approach is the one a senior engineer who knows this repository would choose, and whether the alternatives the plan weighed were real candidates.

Give a groundingScore from 1 (mostly ungrounded or wrong about the repository) to 10 (every claim checked out and nothing important was missed).`
}

const work = []

if (RUN.includes('personas')) {
  work.push(() =>
    parallel(
      PERSONAS.filter((p) => !A.only || A.only.includes(p.key)).map((p) => () =>
        agent(COMMON + p.lens, { phase: 'Persona audit', label: `persona:${p.key}`, schema: FINDINGS_SCHEMA }).then((r) =>
          r ? { persona: p.key, ...r } : null
        )
      )
    ).then((rs) => ({ personas: rs.filter(Boolean) }))
  )
}

if (RUN.includes('plans')) {
  work.push(() =>
    pipeline(
      SCENARIOS,
      (s) => agent(planPrompt(s), { phase: 'Plan scenarios', label: `plan:${VARIANT}:${s.key}`, schema: PLAN_RUN_SCHEMA }),
      (run, s) =>
        parallel([
          () => agent(executorPrompt(run.planPath), { phase: 'Judge plans', label: `executor:${VARIANT}:${s.key}`, schema: EXECUTOR_SCHEMA }),
          () => agent(groundingPrompt(run.planPath, s), { phase: 'Judge plans', label: `grounding:${VARIANT}:${s.key}`, schema: GROUNDING_SCHEMA }),
        ]).then(([executor, grounding]) => ({ scenario: s.key, variant: VARIANT, run, executor, grounding }))
    ).then((rs) => ({ plans: rs.filter(Boolean) }))
  )
}

const parts = await parallel(work)
const out = Object.assign({}, ...parts.filter(Boolean))
log(`done: ${(out.personas || []).length} persona reports, ${(out.plans || []).length} judged plans (${VARIANT})`)
return out
