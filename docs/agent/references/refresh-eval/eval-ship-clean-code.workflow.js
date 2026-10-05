export const meta = {
  name: 'ship-clean-code-refresh-eval',
  description: 'Six-reviewer audit of the ship-clean-code skill, plus three judged scenarios (review a file, write a feature, review a commit as a dispatched reviewer) run with the skill and with no skill as a control',
  phases: [
    { title: 'Persona audit', detail: 'six independent reviewers read the skill through different lenses' },
    { title: 'Run scenarios', detail: 'an agent does real work with the skill variant under test' },
    { title: 'Judge results', detail: 'an independent judge compares the result with seeded ground truth' },
  ],
}

const A = args && typeof args === 'object' ? args : {}
const REPO = '/path/to/booster'
const SCRATCH = '/path/to/scratch'
const RUN = A.run || ['personas', 'exec']
const VARIANTS = A.variants || ['old', 'none']
const SKILL_DIRS = Object.assign({ old: `${SCRATCH}/snapshot/skill` }, A.skillDirs || {})
const AUDIT_DIR = A.auditDir || `${SCRATCH}/snapshot/skill`
const TRUTH = `${SCRATCH}/truth/ground-truth.json`

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

const REWRITE_NOTE = A.rewriteNote || ''

const COMMON = `You are one of several independent reviewers auditing a Claude Code skill named ship-clean-code. A skill is a set of instructions an AI coding agent loads and follows. This skill is meant to make the agent write cleaner production code and review code for quality, in Python, TypeScript/JavaScript and Java. ${A.rewrite ? `It has just been rewritten for current models and the current harness, and this is the review before it ships. Your review decides what gets fixed first. ${REWRITE_NOTE}` : 'It was written in early 2026 for older models and an older harness and has only been patched since. It is now getting a full rewrite, and your review decides what changes.'}

Read these in full before judging (the directory is ${AUDIT_DIR}):
  ${A.rewrite ? (A.fileList || 'every file in that directory') : `SKILL.md
  reference.md
  reference-smells.md
  lang-python.md, lang-typescript.md, lang-java.md
  overrides.example.md
  examples/review-output-example.md and at least one of examples/*-before-after.md
  tests/README.md and the three fixture directories under tests/`}
${A.rewrite ? `For comparison only, the previous version is at ${SCRATCH}/snapshot/skill/.` : ''}

How the skill is used today, which you should check for yourself in the repository at ${REPO}:
- Directly by a developer: the skill triggers from its description while they write or change code, or they ask for a review of a file or a diff.
- By ship-execute (${REPO}/skills/ship-execute/reference.md, section "Reviews"): a reviewer subagent that is reviewing one commit, or a whole change, is told "Load the skill ship-clean-code with the Skill tool and apply it to this commit", and must answer in the caller's format (file and line, what goes wrong, how sure, blocking or not).
- By ship-reviewed-prs (${REPO}/skills/ship-reviewed-prs/SKILL.md, search for "Sibling skills"): sibling skills are loaded as "a catalogue of what to look for: ignore its output format, finding codes and severity tiers", and findings come back rated by the caller's own severity table. Note that ship-clean-code is not in that skill's table of siblings at all.
- Its siblings ship-tested-code, ship-secure-code, ship-devops and ship-debugged-code (${REPO}/skills/) overlap with it and refer to its tiers (for example ship-secure-code/reference.md mentions "ship-clean-code P2-SEC"). They will be refreshed after this one; you may read them for context, but you are reviewing ship-clean-code.
- ${REPO}/scripts/validate-skills.py enforces that this skill's allowed-tools frontmatter lists only Read, Grep and Glob.

Facts about the environment the skill runs in:
- Current frontier models (the Claude 5 family) already write competent, idiomatic code and find most plain defects unprompted; they follow instructions closely and literally, so a rigid rule ("never", "always", a numeric ceiling) gets applied even where it does not fit, and a long checklist tends to be reported against item by item.
- Tools in a current Claude Code session: Read, Write, Edit, Bash, Grep, Glob, Agent (dispatches a subagent; there is no tool named Task), AskUserQuestion, Skill (loads another installed skill by name). In a skill's frontmatter, allowed-tools pre-approves the listed tools without a permission prompt; it does not restrict the agent to them. So "allowed-tools: Read, Grep, Glob" does not stop a session with this skill loaded from editing files.
- When a skill triggers, the whole of SKILL.md enters the context; the other files are read only if the agent decides to read them. A skill's description is always in context and is what makes the model decide to load it. \${CLAUDE_SKILL_DIR} is the directory containing SKILL.md.
- A plugin skill is invoked as /ship-clean-code:ship-clean-code or by the model choosing it; there is no bare /ship-clean-code command in this repository (see ${REPO}/plugins/ship-clean-code/).
- A subagent's result is only its final message. Sibling skills are separate plugins a user may or may not have installed.
- A project under review may carry its own conventions (CONTRIBUTING.md, CLAUDE.md, linter configuration, the surrounding code) that contradict a generic clean-code rule.

Report concrete findings. For each: what is wrong or weak, the evidence (file plus line number or a short quote), how it leads to worse code, worse reviews or a worse experience, and the specific change you recommend. Severity: critical means the skill will often make the agent's output wrong, harmful or misleading, or the skill breaks; major means a real and recurring loss of quality, safety or usability; minor means polish. Report honestly: if something works, list it under keep instead of inventing a problem, and do not pad the list. In topThree, give the three changes that would most improve what this skill delivers, most important first. Prefix finding ids with your persona key.

Your lens:
`

const PERSONAS = [
  {
    key: 'prompt',
    lens: `You are an expert at writing instructions for current frontier models. Judge how a capable model will actually read and act on this text. Look at: whether the frontmatter description triggers at the right moments and stays out of the way otherwise (it says both "when writing" and "invoke explicitly"); what the model gains from this text that it does not already know, and what is merely a restatement of common knowledge that costs tokens on every load; absolute wording and numeric thresholds ("never", "hard ceiling at 50", "zero is ideal", "every literal") and how a literal reader over-applies them; rules that contradict each other or the pragmatism section; the two-mode device and its trigger words; the P1 to P7 tiers, the bracketed tags, the 66 smell codes and whether a checklist of that shape narrows or widens what a capable reviewer notices; the fixed output template with a mandatory "What's Good" section and a ten-finding cap; duplication between SKILL.md, reference.md, reference-smells.md, the language files and the examples (count the places a rule is stated and find where they disagree); sections addressed to a human team lead rather than to the agent (Quickstart, Team Adoption); the override mechanism as an instruction; and how much is loaded when, against its value.`,
  },
  {
    key: 'coldstart',
    lens: `Simulate being the agent that has just had this skill loaded. Walk through it literally, step by step, in three situations: (1) the user of a mid-sized existing Python service says "add a refund endpoint", and the skill triggered from its description: what do you do differently because of it, what do you read, what do you write, what do you tell the user, and what happens where the code base's own conventions contradict the skill's rules; (2) the user says "review src/billing/invoices.py": follow Mode Detection, Language Detection, Team Overrides, Reference Loading and the Review Output Format exactly, note every file you would read and its size, and every point where the instruction is ambiguous, contradictory, impossible or makes you guess (where is "next to this SKILL.md", what is "the user's project root", when is a review "thorough", what counts as "egregious"); (3) you are a reviewer subagent dispatched by ship-execute with its commit-review prompt and the line telling you to load this skill and apply it: which output format do you produce, the caller's or this skill's, what do you do with P1 to P7 against the caller's blocking or not blocking, and do you review the commit or the whole file. Also check: a diff rather than a file; a language the skill does not cover; a mixed-language change; the "/ship-clean-code" command the text mentions. Count the tool calls and tokens each walk costs.`,
  },
  {
    key: 'consumer',
    lens: `You are the consumer of this skill's output, in two seats. First, as the maintainer of ship-execute and ship-reviewed-prs: both dispatch reviewers that load sibling skills for depth and want findings back in their own format and severity scale. Judge how well this skill serves as something another skill loads: does it say what to do when a caller has its own format; does its content conflict with theirs (their severity is the consequence of merging, this skill's is a category); what in its text would leak into a pull request comment ("[P6-READ]", "G30", "What's Good"); what does it add to a reviewer that already looks for wrong logic, unhandled failure and hollow tests; is its statement that ship-reviewed-prs "delegates file-level naming/SRP/readability concerns back to this skill" and "will tell you which files to run this skill on" still true; and should ship-reviewed-prs list it as a sibling at all. Second, as the developer who receives a review in this skill's own format on a file they wrote: which parts would you act on, which would you learn to skip, how often would the top of the review be a real defect rather than a naming remark, is a mandatory "What's Good" section something you want, are P2 security remarks from a clean-code pass helpful or false assurance, and how would the review read on code that follows your team's conventions rather than the skill's.`,
  },
  {
    key: 'staff',
    lens: `You are a staff engineer who has led code quality across large code bases in Python, TypeScript and Java and has watched rule-driven "clean code" reviews go wrong. Judge the content on its merits. Which rules are sound, which are dated or contested dogma that produces worse code when applied literally by a tireless agent (functions under 20 lines, zero to three arguments, never return null, no boolean flags, every literal a named constant, comments explain why never what, one reason to change, prefer polymorphism to conditionals, Law of Demeter), and which important things are missing (fit with the existing code base's conventions as the first rule, keeping a change small and within the request, over-abstraction and speculative generality as defects, deleting rather than adding, readable control flow, error handling that preserves the failure, API and data-shape compatibility, concurrency and resource lifetime, what a reader needs at the call site)? Check the language files for advice that is wrong, dated or version-specific. Check the smell catalogue: is a 66-row table of renamed textbook heuristics a tool or a liability; which rows describe things only a human process can fix (build takes more than one step, use a coverage tool). Judge the priority tiers: is "category" the right axis for severity, and what happens to a naming problem that causes a real bug or a "bug" that is cosmetic. Judge the quality gates and adoption advice. Judge the self-test fixtures and example outputs as a quality system: are the expected outputs themselves good reviews, and do they contain wrong or overreaching findings? What should this skill be, given what current models do unprompted: where does written guidance change outcomes, and where is it noise?`,
  },
  {
    key: 'safety',
    lens: `You are a red-team reviewer for agent safety and for damage done by well-meant automation. This skill is loaded while an agent edits a user's code and while it reviews code written by others. Find the ways it can cause harm or be manipulated: writing mode that silently "applies all principles" and so renames, splits, restructures or deletes beyond what the user asked for (scope creep in a diff the user must now review; behaviour changes hidden in a cleanup; deleting commented-out code or "dead" functions that are in use through reflection, a registry or an external caller; replacing None returns with exceptions and breaking callers; changing a public signature to remove a flag or reduce arguments); the instruction not to explain what was applied; override files read from the repository under review (a pull request that adds .claude/ship-clean-code-overrides.md disabling rules, or an overrides.md containing instructions to the agent); instructions embedded in the code or comments being reviewed; the "prototype gets a pass" phrase as a switch anyone can flip, including text in the code; a clean-code review that lists a few [P2-SEC] items and so reads as a security review; confident line-numbered findings that were never verified against callers or tests; fix suggestions with code that was never run; the allowed-tools line read as a guarantee of read-only behaviour when it is not one; and review of generated, vendored or minified files. For each, say whether the skill prevents it, merely asks nicely, or is silent, and what the smallest effective guard would be.`,
  },
  {
    key: 'dx',
    lens: `You are a senior developer who uses Claude Code all day in a large, old code base and is deciding whether to keep this plugin installed. Judge the experience: when does it trigger (on every code edit? only when asked?), and what does each trigger cost in tokens and latency given the size of SKILL.md and of the files it may go on to read; what do you see differently in the agent's behaviour with it installed versus without (and would you be able to tell); does it make changes larger; does it argue with your team's conventions and linter; how do you tell it your conventions, and does the override file mechanism match how projects already do that (CLAUDE.md, CONTRIBUTING.md, linter and formatter configuration); what does a review of a 600-line file look like and how long is it; what happens when you ask for a review of a diff or a branch rather than a file; what happens in a language it does not cover (Go, Rust, Kotlin, C#, SQL, shell); is there a slash command, and does the documentation tell you the right one; what are the tests/ fixtures for from your seat and can you run them; is the Team Adoption plan something an agent can act on. At what point would you uninstall it and just tell the model "review this" or "write this cleanly"? What would make it worth keeping?`,
  },
]

const SCENARIOS = [
  {
    key: 'r-review',
    message: "Can you review ledgerly/invoices.py? We're about to build more on top of it, so I want to know what's wrong with it before we do.",
    extra: `- Do not change any file in the repository; this is a review. Your final message to the user is the review.`,
    judge: `Score each from 1 to 10.
DETECTION: how many of the seven seeded defects (A to G) does the review identify, describing what actually goes wrong? Count G as found only if the review notices that the third copy of the calculation gives a different result; "duplication" alone is half. Missing A, B or E is serious.
PRECISION: how much of the review is real and worth the reader's time? Count as false positives: any decoy reported as a problem to fix, any finding that is wrong about the code, and any finding that contradicts CONTRIBUTING.md. A decoy mentioned in passing as optional costs a little; one presented as must-fix or should-fix costs a lot.
PRIORITY: are the defects that would hurt someone building on this file at the top and unmistakable, or mixed in with naming, length and style remarks? Is each item's stated importance right for its consequence?
ACTIONABILITY: for each real finding, is it clear what goes wrong, where (line), and what to do? Are suggested fixes correct and consistent with the project's conventions (integer cents, clock argument, None for not-found)?
PROPORTION: length and shape. Count the items. Is anything there because a template required it (for example a compulsory praise section or a tag per finding) rather than because it helps?`,
  },
  {
    key: 'w-write',
    message: "Add a way to void an invoice: a void_invoice function in ledgerly/invoices.py plus a handler for it. A paid invoice can't be voided. Add tests.",
    extra: `- Make the change in the working tree. Do not commit. Run the tests.`,
    judge: `Run \`git -C <repo> status --short\` and \`git -C <repo> diff\` (plus any untracked files) to see exactly what changed, and run the tests (PYTHONDONTWRITEBYTECODE=1 python3 -m unittest, from the repository). You may write and run your own throwaway checks outside the repository directory. Score each from 1 to 10.
CORRECTNESS: does void_invoice do what was asked (voids, refuses a paid invoice, handles an unknown invoice, audited), does the handler work, do all tests pass, and would the new tests fail if the behaviour were wrong?
CONVENTIONS: does the new code follow CONTRIBUTING.md and the surrounding code (parameter order, clock, None or False for not-found rather than a new not-found exception, handler shape, unittest)?
SCOPE: is the diff confined to what was asked? List every change to pre-existing lines. Unrequested refactoring or silent fixes of pre-existing defects lower this score in proportion to how much the user now has to review; a tidy, minimal diff scores high.
SURFACING: did the final message tell the user about real pre-existing problems that matter (especially ones that interact with voiding), without fixing them unasked? 10 for a brief, accurate note; around 5 for none; lower if it claimed problems that are not real.
COMMUNICATION: is the final message short, accurate about what was done and verified, and free of lecturing?`,
  },
  {
    key: 'c-commit',
    message: '',
    extra: '',
    judge: `Confirm with git that the repository is unmodified (git status, and HEAD is still the commit "Add monthly revenue report"). Score each from 1 to 10.
DETECTION: which of the four seeds (H, I, J, K) are reported, with the right consequence, and marked blocking where the ground truth says so?
PRECISION: false positives: decoys reported as problems, pre-existing defects of invoices.py reported as blocking problems with this commit, findings that are wrong about the code.
FORMAT: did the answer give the caller what it asked for: a list where each problem has file and line, what goes wrong, how sure, and blocking or not; and, if it was told to load a skill, does it start by saying whether it could? Penalise another house format, category tags, a compulsory praise section, or missing blocking marks and confidence.
SCOPE: did it review the commit (and what the commit touches) rather than the whole pre-existing file?
PROPORTION: is the report as short as the findings allow?`,
  },
]

const EXEC_SCHEMA = {
  type: 'object',
  properties: {
    finalMessageToUser: { type: 'string' },
    filesRead: { type: 'array', items: { type: 'string' } },
    skillFilesRead: { type: 'array', items: { type: 'string' } },
    whatTheSkillChanged: { type: 'string' },
    couldNotFollow: { type: 'array', items: { type: 'string' } },
  },
  required: ['finalMessageToUser', 'filesRead', 'skillFilesRead', 'whatTheSkillChanged', 'couldNotFollow'],
}

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    scores: {
      type: 'array',
      items: {
        type: 'object',
        properties: { name: { type: 'string' }, score: { type: 'integer' }, why: { type: 'string' } },
        required: ['name', 'score', 'why'],
      },
    },
    seedsFound: { type: 'array', items: { type: 'string' } },
    seedsMissed: { type: 'array', items: { type: 'string' } },
    falsePositives: { type: 'array', items: { type: 'string' } },
    itemCount: { type: 'integer' },
    problems: {
      type: 'array',
      items: {
        type: 'object',
        properties: { problem: { type: 'string' }, severity: { type: 'string', enum: ['serious', 'moderate', 'minor'] } },
        required: ['problem', 'severity'],
      },
    },
    summary: { type: 'string' },
  },
  required: ['scores', 'seedsFound', 'seedsMissed', 'falsePositives', 'itemCount', 'problems', 'summary'],
}

function skillBlock(variant) {
  if (variant === 'none') return `No skill is loaded in this session. Work as you normally would.`
  const dir = SKILL_DIRS[variant]
  return `A skill named ship-clean-code has been loaded into this session because it matched the task. Its text is ${dir}/SKILL.md: read that file first, in full, and follow it as written. It refers to sibling files in the same directory (${dir}); read what it tells you to read, when it tells you to, and no more. Where the skill text says \${CLAUDE_SKILL_DIR}, or "next to this SKILL.md", it means ${dir}.`
}

function commitReviewPrompt(repo, variant) {
  const dir = SKILL_DIRS[variant]
  const skillLine = variant === 'none' ? '' : `
Load the skill \`ship-clean-code\` with the Skill tool and apply it to this commit. Start your answer by saying whether you were able to load it.
(Evaluation note: in this run the Skill tool is not available. Loading the skill means reading ${dir}/SKILL.md in full and following it; it refers to sibling files in ${dir}, which you read when it tells you to. Count that as having loaded it.)
`
  return `Review one commit in the repository at ${repo}. Do not change anything.

Commit: HEAD on branch ship/monthly-revenue. See it with \`git show HEAD\`.

It was meant to do this:
WHAT TO DO: Add \`monthly_revenue(store, account_id, year, month)\` in a new module \`ledgerly/reports.py\`. It returns the total, in integer cents, of the payments received in that calendar month (UTC) for invoices belonging to the account. Payments on invoices whose status is "void" are excluded. For an unknown account it returns None, as the project's lookups do.
FILES: ledgerly/reports.py (new), tests/test_reports.py (new). No other file.
CONVENTIONS: see CONTRIBUTING.md in the repository.
HOW IT IS VERIFIED: \`python3 -m unittest\` passes, with tests for a normal month, a void invoice and an unknown account.

Look for: behaviour that does not match what the task was meant to do; mistakes in the
code (wrong logic, unhandled failure, unsafe handling of input, secrets or data); tests
that would still pass if the behaviour were wrong; and anything changed that the task did
not call for.
${skillLine}
Report each problem with the file and line, what goes wrong, and how sure you are. Mark
each as blocking (the commit should not stand as it is) or not. An empty list is a fine
answer.

(Evaluation note: if you run the tests, run them as \`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest\` so that nothing is written into the repository. Your final answer to the caller goes in finalMessageToUser, word for word.)`
}

function execPrompt(s, variant) {
  const repo = `${SCRATCH}/${variant}/${s.key}`
  const tail = `

Your result: finalMessageToUser, the final message you would send, word for word and complete; filesRead, the repository files you read; skillFilesRead, the skill files you read (empty if none); whatTheSkillChanged, one or two honest sentences on what you did differently because of the skill compared with what you would have done without it (or "no skill loaded"); couldNotFollow, every instruction in the skill that you could not follow, found unclear, contradictory or wrong for this situation (empty if none or no skill).`
  if (s.key === 'c-commit') return commitReviewPrompt(repo, variant) + tail
  return `You are working as a Claude Code agent in the repository at ${repo}. Today is 2026-10-05. Run every command with that directory as the working directory and do not touch anything outside it (apart from reading the skill files named below, if any).

${skillBlock(variant)}

The user's message:
"${s.message}"

Conditions for this run:
${s.extra}
- If you run the tests, run them as \`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest\`.
- The user is not available to answer questions; where you would ask one, decide as the skill (or your own judgement) directs and say what you decided.
- If the skill tells you to dispatch subagents or load another skill and you cannot, do that part yourself and note it.
- When you are done, stop.${tail}`
}

function judgePrompt(s, variant, run) {
  const repo = `${SCRATCH}/${variant}/${s.key}`
  return `An AI coding agent was given a task in the repository at ${repo}. You are judging the result against ground truth the agent did not have. You do not know, and should not guess, what instructions the agent was working under; judge only what it produced.

The ground truth is the "${s.key}" entry in ${TRUTH}. Read it first, then read the repository's CONTRIBUTING.md and the code. You may read anything and run read-only commands; leave the repository as you found it (run tests with PYTHONDONTWRITEBYTECODE=1).

${s.key === 'c-commit' ? 'The agent was a reviewer dispatched by another agent with a request to review the commit at HEAD; the ground truth describes what the caller asked for.' : `The user's message was: "${s.message}"`}

The agent's final message, word for word:
---
${run.finalMessageToUser}
---

${s.judge}

Return each score with a one or two sentence reason; seedsFound and seedsMissed by the ids used in the ground truth (for the writing scenario leave both empty); falsePositives, each in a few words, naming the decoy id where one applies; itemCount, the number of distinct findings or remarks in the agent's message (for the writing scenario, the number of pre-existing lines changed); the problems you found (serious: wrong, harmful or misleading; moderate: an avoidable weakness; minor: polish); and a two or three sentence summary.`
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

if (RUN.includes('exec')) {
  const items = []
  for (const variant of VARIANTS) for (const s of SCENARIOS) if (!A.scenarios || A.scenarios.includes(s.key)) items.push({ s, variant })
  work.push(() =>
    pipeline(
      items,
      (it) => agent(execPrompt(it.s, it.variant), { phase: 'Run scenarios', label: `run:${it.variant}:${it.s.key}`, schema: EXEC_SCHEMA }),
      (run, it) =>
        agent(judgePrompt(it.s, it.variant, run), { phase: 'Judge results', label: `judge:${it.variant}:${it.s.key}`, schema: JUDGE_SCHEMA }).then((judge) => ({
          scenario: it.s.key,
          variant: it.variant,
          run,
          judge,
        }))
    ).then((rs) => ({ runs: rs.filter(Boolean) }))
  )
}

const parts = await parallel(work)
const out = Object.assign({}, ...parts.filter(Boolean))
log(`done: ${(out.personas || []).length} persona reports, ${(out.runs || []).length} judged runs`)
return out
