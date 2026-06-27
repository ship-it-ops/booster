---
name: ship-agent-context
description: >
  ALWAYS activate at session start in any repository to check for `docs/agent/`
  — the in-repo memory of plans, decisions, in-flight status, standing user
  instructions, open questions, patterns, and incident scars left by prior
  agents. Read `MANIFEST.md` and every file under `status/` and `instructions/`
  before answering, planning, deciding, implementing, debugging, investigating,
  refactoring, reviewing, or fixing code. Activate whenever the user says
  "what did we decide", "what's in flight", "what's the plan for X", "any known
  issues / scars / blockers", "is anyone working on Y", "pick up where the
  last agent left off", or mentions prior agents, handoffs, or past incidents.
  Also activate to capture new context after a decision is made, a plan is
  finalized, a root cause is identified, a workaround is chosen, a scar is
  earned, or the user gives a standing instruction ("don't push without
  asking", "always run tests first", "from now on X", "never X", "remember
  to X") — even when `docs/agent/` does not yet exist (offer to scaffold).
  Complements AGENTS.md / CLAUDE.md (static project rules curated by a
  maintainer) by holding dynamic, branch-tracked state and user-captured
  behavior rules. Standalone — no external vault or other skill required.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir -p *), Bash(mv docs/agent/*), Bash(gh pr view *), Bash(git ls-remote *), Bash(git merge-base *), Bash(git branch *)
---

## Purpose

You are an AI agent walking into a repository. Code, `git log`, and any static `AGENTS.md`/`CLAUDE.md` tell you *what exists* and *what the rules are*. They do not tell you:

- What plans the previous agent left half-finished.
- What decisions were made by other agents and *why* — including which approaches were rejected.
- What other agents are working on right now in parallel branches.
- Which questions are blocking forward progress.
- Which paths have burned the team before (incident scars).

This skill manages `docs/agent/` inside the repo as the **dynamic, team-shared handoff layer** for AI agents. It complements — never replaces — `AGENTS.md`/`CLAUDE.md`, which hold static project rules.

The folder is committed to git. Every agent on every branch sees the same context.

---

## Auto-Activation

When installed via the booster plugin marketplace (`/plugin install ship-agent-context@booster`), this skill ships a bundled SessionStart hook at `hooks/hooks.json`. The hook fires at the start of every Claude Code session and:

- Checks for `docs/agent/MANIFEST.md` in the current working directory.
- If present, injects a system reminder telling the model to read MANIFEST + every file under `docs/agent/status/` and `docs/agent/instructions/`, **reconcile each status entry against its `## Done when` anchor** (archiving completed work, flagging the unverifiable), and use this skill to capture new context.
- If absent, the hook is silent — installing the plugin imposes ~no cost in repos that don't use `docs/agent/`.

This guarantees activation in repos that need it, independent of description matching. To disable, disable the plugin via `/plugin`. For users who installed the skill manually (npx / cp / symlink) rather than via the plugin marketplace, the hook is not present — anchor the skill in the repo's `AGENTS.md` or `CLAUDE.md` (see `examples/initialization-example.md`) for similar reliability.

---

## CRITICAL: Always Check `docs/agent/`

**At session start — before doing ANY work:**
1. `Glob: docs/agent/MANIFEST.md` to check if the repo has been initialized.
2. If yes: Read `MANIFEST.md`, then read every file under `docs/agent/status/` (small, ephemeral, always relevant), then read any `importance: core` decisions.
3. If no: do not auto-create. Note the absence; offer to scaffold only if the user's request would benefit (a decision is being made, a plan needs writing, etc.).
4. Only then begin working on the user's request.

**Before making decisions during a session:**
- Choosing a library, pattern, or architecture? → Check `docs/agent/decisions/` and `docs/agent/patterns/`.
- Debugging a bug? → Check `docs/agent/investigations/` and `docs/agent/scars/` for prior root causes and tripwires.
- About to commit, push, deploy, or take any irreversible action? → Check `docs/agent/instructions/` for a standing rule the user already gave.
- Starting work in an area? → Check `docs/agent/status/` — a sibling agent may already be in that area.
- Hitting an unknown? → Check `docs/agent/open-questions/` — it may already be tracked.
- User states a behavior preference that should outlive this session ("don't push without asking", "always run tests first")? → Capture it in `docs/agent/instructions/` (see [Auto-Capturing User Instructions](#auto-capturing-user-instructions)). Static project rules curated by a maintainer ("use pnpm", "tests live in `__tests__/`") still belong in `AGENTS.md` / `CLAUDE.md`.

**If you skip the check, you risk:**
- Repeating work another agent completed last week.
- Contradicting a decision that has explicit rationale.
- Stomping on a sibling agent's in-flight branch.
- Re-stepping on an incident the team has already scarred over.

---

## Setup & Scaffolding

`docs/agent/` lives at a deterministic path inside the repo. No discovery is needed. The skill only needs to create it once.

### When to scaffold

Scaffold only when the user's current task will produce content worth capturing — a decision, a plan, an investigation root cause, a scar. Do not create empty folders just because the skill activated.

Before creating anything, confirm with the user:

> "I'd like to set up `docs/agent/` in this repo — a committed folder where agents leave plans, decisions, and in-flight status for future agents. Sound good?"

If the user declines: do not activate again this session.

### Scaffold layout

```
docs/agent/
  MANIFEST.md              ← the index you read first, every session
  decisions/               ← architecture, library, configuration choices
  plans/                   ← implementation plans, active and historical
  investigations/          ← bug hunts, root cause analyses
  patterns/                ← codebase conventions discovered by agents
  status/                  ← IN-FLIGHT work (cleared on completion)
  instructions/            ← STANDING USER INSTRUCTIONS, read every session
  open-questions/          ← blockers awaiting human/maintainer answer
  scars/                   ← incidents and tripwires ("don't do X because Y")
  archive/                 ← superseded/deprecated content
```

Create with: `mkdir -p docs/agent/{decisions,plans,investigations,patterns,status,instructions,open-questions,scars,archive}`

Then write `docs/agent/MANIFEST.md` with the starter content shown in the [MANIFEST.md Format](#manifestmd-format) section. Also write a seed decision at `docs/agent/decisions/agent-context-initialized.md` documenting that this folder was set up and why (this becomes the first MANIFEST entry, proving the system works).

### Permissions

The folder is inside the repo, so no global permission setup is needed. Standard project file-write permissions apply.

---

## Read Protocol

When you need context, follow this order. Stop as soon as you have enough.

### Step 1 — Read MANIFEST
Read `docs/agent/MANIFEST.md`. It indexes every note: slug, type, status, importance, date, 8-word summary. Scan for entries relevant to your task.

### Step 2 — Read AND reconcile all of `status/`
Always read every file in `docs/agent/status/`. It is bounded in size (typically <5 entries) and is the single most important signal: it tells you what other agents are doing *right now*. Skipping this is how parallel agents collide.

Then **reconcile each entry against ground truth before you trust it** — see [Reconciliation — Self-Healing Status](#reconciliation--self-healing-status). `status/` is the only always-read surface that rots *silently* (PRs merge and branches get deleted on the remote with no session running), so a one-command check per entry is what keeps it honest. Auto-archive the ones that are demonstrably complete; flag the ones you cannot verify.

### Step 2.5 — Read all of `instructions/`
Always read every file in `docs/agent/instructions/`. These are standing user instructions captured in prior sessions — behavior rules the user gave Claude that must persist across sessions, branches, and agents (e.g., "don't push without asking", "always run the linter before opening a PR"). Like `status/`, the folder is bounded in size and every file is opened. Any `importance: core` instruction must be acknowledged in your opening response to the user so they can see the rule was loaded.

### Step 3 — Read `core` decisions
For any note with `importance: core` in the MANIFEST, read the full file. These are foundational — you should know them by default.

### Step 4 — Read task-relevant notes
Open the 1–3 notes that most directly match your task. Read them fully. Stay focused — follow at most one hop of `## Related` links.

### Step 5 — Scan `open-questions/`
If a question is open in your task area, surface it to the user. Don't silently re-derive an answer; the team may already be waiting on a specific person to answer it.

### Step 6 — Search fallback
If the MANIFEST didn't surface what you need, Grep `docs/agent/` for keywords. Try synonyms (auth/authentication/login/token). This is the expensive path — most reads should resolve at Step 1.

### Rules
- **NEVER** glob-read every file in `docs/agent/`. Use the MANIFEST.
- **ALWAYS** check `status` before trusting a note. Skip `deprecated`. Treat `superseded` as a pointer to its replacement.
- **VERIFY BEFORE YOU REPORT.** Never relay a note's *transient* claim — "PR is open", "X is in progress", "still on the todo list", "pending merge" — to the user as current fact without re-checking it when the check is cheap (a `gh`/`git`/file-system call). A note records what was true when it was written; only ground truth tells you what is true now. If you cannot verify, say so explicitly ("the note says X, unverified") rather than asserting it. See [Reconciliation — Self-Healing Status](#reconciliation--self-healing-status).
- **ALWAYS** apply every `active` instruction in `instructions/` for the duration of the session. They are not advisory — they are standing orders from the user.
- **DO NOT** read `archive/` at session start — it's intentionally cold storage.
- **READ AGENTS.md and CLAUDE.md normally** — they hold static rules, not agent state. This skill does not duplicate them.

---

## Reconciliation — Self-Healing Status

`status/` is the only always-read surface that goes stale **silently**. The events that complete a status entry — a PR merging, a branch being deleted, a commit landing on the default branch — happen on the remote, asynchronously, with no agent session running. Nothing inside the repo changes when they happen, so an `active` entry can keep describing work that shipped days ago. A future agent then reads it and reports it as in-flight *with full confidence*. This is the single biggest cause of context rot — and the reason a user has to keep pushing back with "are you sure that's still true?"

The fix: verify each status entry against ground truth at session start, and self-heal the ones that are demonstrably done. Stale `status/` should correct itself, not accumulate.

### Every status note carries a completion anchor

So reconciliation is a cheap deterministic check and not a guess, every `status/` note MUST include a `## Done when` section naming a **machine-checkable** condition. Pick the one you can verify in a single command:

| Anchor | Check | Complete when |
|---|---|---|
| `PR #123 merged` | `gh pr view 123 --json state -q .state` | prints `MERGED` |
| `branch feature/x deleted on remote` | `git ls-remote --exit-code --heads origin feature/x` | exits non-zero |
| `commit <sha> on <default-branch>` | `git merge-base --is-ancestor <sha> origin/main` | exits zero |

Prefer the **PR-merged** check — it stays correct even when a merged branch lingers locally (exactly the trap that produced the ship-vuln staleness: branch still present, PR long merged).

### At session start, reconcile before trusting

For each file in `status/`, immediately after reading it:

1. Run its `## Done when` check — one `gh`/`git` command.
2. **Hard evidence of completion** (PR `MERGED`, branch gone, sha is an ancestor of the default branch) → **self-heal, no prompt:**
   - set `status: completed`, bump `updated`;
   - `mv` the file from `status/` to `archive/`;
   - remove its line from the MANIFEST `## Status` section (decrement `Total notes`);
   - tell the user in one line: *"Reconciled: `ship-vuln-skills` shipped (PR #7 merged) — moved to archive."*
3. **No evidence, or not checkable** (offline, no anchor, inconclusive result) → **do NOT modify the file.** Flag it inline — *"`status/foo` may be stale (couldn't verify its Done-when) — verify before trusting it"* — and treat its claims as unverified for the rest of the session.

This is bounded work: `status/` holds <5 entries, so it is at most a handful of cheap commands. Never skip it — it is what keeps the always-read surface honest. Only **hard evidence** triggers the silent archive; absence of evidence is a flag, never a deletion.

---

## Write Protocol

**Write incrementally, not at the end.** After each significant milestone — a decision made, a plan finalized, a root cause confirmed, a scar earned — evaluate whether it's worth persisting. Apply the **5-minute re-discovery threshold**: only write what would take more than 5 minutes for a future agent to reconstruct.

### What to write

- **Decisions** — architecture, library, or process choices with rationale.
- **Plans** — implementation plans you produced (the user's `/plan` output, an ExitPlanMode plan, a multi-step strategy).
- **Investigations** — bug root causes, especially non-obvious ones.
- **Patterns** — codebase conventions you discovered while reading code.
- **Status** — short-lived "I am working on X on branch Y" entries, cleared on completion.
- **Instructions** — standing behavior rules the user gave you in conversation ("don't push without asking", "always run the linter first"). Auto-captured when the user uses persistent-intent phrasing — see [Auto-Capturing User Instructions](#auto-capturing-user-instructions) for the trigger rules.
- **Open questions** — blockers you can't resolve and the person/source that could.
- **Scars** — incidents that produced a lesson. Must name the tripwire ("if you see X, stop").

### What NOT to write

- Routine code changes (`git log` captures those).
- Obvious facts derivable from reading the code.
- Ephemeral todos (use the in-conversation task list).
- Anything already documented in `AGENTS.md`, `CLAUDE.md`, or `README.md` — link to those instead.
- Per-session journals — the user has explicitly excluded these.

### 5-Step Write Flow

**Step 1 — Search MANIFEST**: Scan for an existing note on this topic. Look for the same slug or an overlapping summary.

**Step 2 — Decide update vs. create**:
- **Same topic, exists, `active`**: edit the existing file. Bump `updated`.
- **Same topic, exists, `deprecated`**: create a new file. Set the old file's status to `superseded`. Add a pointer between them.
- **No match**: create a new file.

**Step 3 — Write the file** to `docs/agent/{folder}/{slug}.md` using the right template (see Content Types below). Before writing, run `mkdir -p docs/agent/{folder}` defensively — the subfolder may be missing if `docs/agent/` was hand-edited. Folder follows the type:

| Type | Folder |
|---|---|
| `decision` | `decisions/` |
| `plan` | `plans/` |
| `investigation` | `investigations/` |
| `pattern` | `patterns/` |
| `status` | `status/` |
| `instruction` | `instructions/` |
| `open-question` | `open-questions/` |
| `scar` | `scars/` |

Slug rules: lowercase, hyphens for spaces, no special characters, max 60 chars. No project prefix (repo-scoped).

**Step 4 — Update MANIFEST**: Add or update the entry under the right section. Format:
```
- [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
```
Bump `Last updated` and `Total notes`.

**Step 5 — Add `## Related` links** (3–5 max) to other notes that share a causal or dependency relationship. Use relative links: `[slug](../decisions/slug.md)`.

---

## Content Types & Templates

All notes share this base frontmatter:

```yaml
---
type: decision | plan | investigation | pattern | status | open-question | scar
status: active | completed | superseded | deprecated | blocked
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: <agent-id, claude-session-id, or human handle>
tags: [list, of, tags]
importance: core | standard | minor   # optional, defaults to standard
---
```

### Decision

For architecture, library, configuration, or process choices.

```markdown
# {Descriptive Title}

## Context
What situation prompted this decision?

## Decision
What was decided.

## Alternatives Considered
- **Option A**: rejected because…
- **Option B**: rejected because…

## Consequences
What does this enable, prevent, or commit us to?

## Revisit Triggers
Concrete conditions that should reopen this decision (e.g., "if request volume exceeds 10k/min").

## Related
- [other-note](../decisions/other-note.md) — why it's related
```

### Plan

For implementation plans produced by an agent. Captures plans that would otherwise be lost when the session ends.

```markdown
# {Plan Title}

## Goal
What this plan accomplishes.

## Approach
Step-by-step strategy.

## Files to Touch
- `path/to/file` — what changes

## Status
What's done, what's next, what's blocked.

## Related
- [decision-this-followed](../decisions/x.md)
```

`status` in the frontmatter is `active` while in flight, `completed` when shipped, `superseded` if replaced.

### Investigation

For bug hunts and root cause analyses.

```markdown
# {Bug or Issue Title}

## Symptoms
What was observed.

## Root Cause
What was actually wrong. Be specific — file, line, mechanism.

## Fix
What solved it.

## Prevention
How to avoid recurrence.

## Related
- [scar-if-incident-grade](../scars/x.md)
```

### Pattern

For recurring codebase conventions discovered while reading code.

```markdown
# {Pattern Name}

## When to Use
Situations that call for this pattern.

## Implementation
How it's implemented in this codebase. Key files, functions.

## Examples
Brief code references showing the pattern in action.

## Gotchas
Common mistakes when applying it.
```

### Status (in-flight)

Short-lived entry that signals "an agent is working on this right now". Extra required fields:

```yaml
type: status
status: active | blocked | completed
branch: feature/x
agent: claude-session-2026-05-19-1430   # any stable identifier
```

```markdown
# {What you're doing, in one line}

## Scope
Files or areas being touched.

## Why
Link to the decision, plan, or issue driving this.

## Done when
The one machine-checkable condition that means this work has shipped — `PR #123 merged`,
`branch feature/x deleted on remote`, or `commit <sha> on main`. REQUIRED. This is the anchor
the next session's reconciliation runs to auto-archive this entry. No anchor → it can never
self-heal and will rot. See [Reconciliation](#reconciliation--self-healing-status).

## Blocked on
(only if status: blocked) — what needs to resolve.
```

**Lifecycle**: this entry is self-healing. The next agent to start a session runs its `## Done when` check and, on hard evidence of completion (PR merged, branch gone, sha on the default branch), auto-flips `status` to `completed` and moves the file to `archive/` — see [Reconciliation — Self-Healing Status](#reconciliation--self-healing-status). You don't have to rely on someone remembering to clean it up. If *you* are the one who finishes or abandons the work in-session, complete and archive it yourself rather than waiting. `status/` should rarely hold more than 3–5 active entries at once.

### Instruction

A standing behavior rule the user gave Claude in conversation that should persist across sessions, branches, and agents. Distinct from `decisions/` (which capture *why* a choice was made) — instructions capture *what the user told the agent to do or not do*.

Extra required fields:

```yaml
type: instruction
status: active | superseded | revoked
source: user-instruction           # always — distinguishes from agent-authored notes
scope: always | when-X | branch:feature/y | until:YYYY-MM-DD
```

```markdown
# {The rule, phrased as a sentence}

## Instruction
Verbatim or near-verbatim what the user said.

## Why
(Optional — reason the user gave, if any. Captures intent so future agents can judge edge cases.)

## How to apply
Concrete: when does this kick in, what does the agent do differently.

## Source
- Session: <session-id or date>
- Captured from: "<short paraphrase of the user's exact words>"

## To revoke
The phrasing the user can use to turn this off (e.g., "forget the push rule", "you can commit without asking now").
```

**Lifecycle**:
- `active` → in force.
- `superseded` → replaced by another instruction on the same topic; the new file links back via `## Related`.
- `revoked` → the user turned it off. Move the file from `instructions/` to `archive/`. Keep the history; do not delete.

#### Auto-Capturing User Instructions

When the user uses persistent-intent phrasing in conversation, capture it as an instruction **without asking first**. This is the explicit design — confirm prompts add friction that defeats the purpose of remembering across sessions.

**Triggers (capture)** — phrasings that signal a persistent rule:

- "never X" / "don't ever X" / "stop X-ing"
- "always X" / "from now on X" / "going forward X"
- "remember to X" / "remember that X"
- "ask before X" / "X without asking" (paired with a recurring action like commit, push, deploy)
- "for this repo X" / "in this codebase X" / "in this project X"
- "I want you to X" / "I need you to X" (when X is a behavior, not a one-off task)

**Anti-triggers (do not capture; treat as one-off)** — phrasings that look similar but are scoped to the current turn:

- "just this time X" / "for this turn X" / "for now X" / "this once X" / "in this case X"
- Imperatives plainly tied to the current task with no temporal/scope marker — e.g., "don't use ESM here" while editing a CJS-only file. That's a momentary correction, not a standing rule.

When uncertain whether a phrase is a standing rule or a one-off, **default to NOT capturing** and continue with the task. Over-capturing pollutes the always-read surface; under-capturing just means the user re-states the rule (and likely uses stronger persistent-intent language the second time).

**Behavior when a trigger fires:**

1. Write the file immediately — no confirm prompt. Slug from the rule, not the user's verbatim words. Put it at `docs/agent/instructions/{slug}.md`.
2. Update `MANIFEST.md` under the `## Instructions` section (positioned right after `## Status`).
3. In the same response, tell the user in one line where the file lives and how to revoke it. Example:
   > "Saved as a standing instruction: `docs/agent/instructions/dont-push-without-asking.md`. Say 'forget the push rule' anytime to revoke."

   This single line is mandatory — it is the safety net that makes silent auto-capture acceptable. Without it the user has no signal that a file was created on their behalf.
4. **Cap at one auto-capture per user turn.** If multiple triggers fire in the same message, write the most explicit one and surface the others as one-line candidates: "I also heard 'always run tests before push' — want me to save that too?" Prevents runaway captures from a single message.

**Revocation:** when the user says "forget X" / "you can X without asking now" / "ignore that rule":
1. Find the matching `instructions/` file.
2. Set `status: revoked`, bump `updated`.
3. Move the file from `instructions/` to `archive/` (preserves what was asked-then-rescinded).
4. Remove the entry from `## Instructions` in MANIFEST.
5. Confirm in one line.

**Conflict with `AGENTS.md`/`CLAUDE.md`:** if an active instruction contradicts a rule in `AGENTS.md` or `CLAUDE.md`, **do not** silently overwrite either side. Surface the conflict and ask the user which wins. The user's in-session instruction is typically more current, but `AGENTS.md` may carry team-wide weight the user didn't intend to override.

**Promotion:** when an instruction has been `active` for ~30+ days and the repo has an `AGENTS.md`, suggest copying the rule there as a permanent project rule. The skill never edits `AGENTS.md` itself — that's a deliberate human-curation boundary.

### Open Question

A blocker awaiting an answer. Extra required fields:

```yaml
type: open-question
status: active | answered | abandoned
opened: YYYY-MM-DD
answer-source: docs | maintainer | experiment | unknown
```

```markdown
# {The question, phrased as a question}

## Context
What we know so far, and why we need an answer.

## Tried
What we attempted to resolve it ourselves.

## Who Can Answer
Name, role, or "needs experiment".
```

Flag any `active` open question older than 30 days for review.

### Scar

A lesson from a real incident. Extra required fields:

```yaml
type: scar
status: active
incident-date: YYYY-MM-DD
tripwire: "if you see X, stop and check Y"
```

```markdown
# {Short title — the lesson, not the bug}

## What Happened
Brief incident summary.

## Tripwire
The one-line condition that should make a future agent stop.

## Why It Hurt
What broke, who paid, how bad.

## Don't Do This
Specific action to avoid.

## Related
- [investigation-of-incident](../investigations/x.md)
```

Scars are immutable. Update them only to refine the tripwire. Never set `status: deprecated` on a scar — once the team has been burned, the lesson stands.

---

## MANIFEST.md Format

```markdown
# Agent Context
Last updated: YYYY-MM-DD | Total notes: N

<!--
  This file is the index for `docs/agent/`. Agents read it at session start.
  Format: - [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
-->

## Status (in-flight)
<!-- always-read at session start -->

## Instructions
<!-- standing user instructions — always-read at session start -->

## Decisions
## Plans
## Investigations
## Patterns
## Open Questions
## Scars
```

Sections appear only when they have entries. Order is fixed — `Status` always first, `Instructions` second (both are always-read at session start).

When the file exceeds ~100 entries, split per-section into `MANIFEST-decisions.md`, `MANIFEST-plans.md`, etc. Keep `MANIFEST.md` as the entrypoint with the 10 most recent per section plus all `core` importance entries.

---

## Relationship to AGENTS.md and CLAUDE.md

This skill **does not modify or duplicate** `AGENTS.md` or `CLAUDE.md`.

| Layer | What it holds | Curated by | Lifetime |
|---|---|---|---|
| `AGENTS.md` / `CLAUDE.md` | **Static project rules** ("use pnpm", "tests live in `__tests__/`", "never commit without running lint") | A maintainer, deliberately | Until manually edited |
| `docs/agent/instructions/` | **User-captured behavior rules** the user said in conversation ("don't push without asking", "always run linter first") | Auto-captured by the agent, on the fly | Until the user revokes |
| `docs/agent/{decisions,plans,…}` | **Dynamic agent state** — decisions made, plans in flight, scars earned | The agent, during work | Until superseded |

The boundary between `instructions/` and `AGENTS.md` is friction and authority. `instructions/` is the *low-friction* surface — the user states a rule in conversation and it sticks immediately, no editing required. `AGENTS.md` is the *high-authority* surface — once a rule is stable and clearly project-wide, the skill should suggest promoting it to `AGENTS.md` so it carries the weight of a maintainer-curated rule.

Two promotion paths:

- **From a decision** — if a `decisions/` note concludes "we now standardize on pnpm," that rule belongs in `AGENTS.md`. The skill should suggest the update, not perform it silently. The decision note links to the rule; the rule links back to the decision.
- **From an instruction** — if an `instructions/` note has been `active` for ~30+ days and the repo has `AGENTS.md`, suggest copying the rule there as a permanent project rule. The skill never edits `AGENTS.md` itself — that boundary is intentional.

---

## Multi-Agent Coordination

Parallel agents (different terminal sessions, different branches) coordinate through `status/`.

**Before starting work in an area:**
1. Read all `status/` entries.
2. If an entry overlaps your scope and is `active`, surface it: "Another agent is on branch X touching these files. Want me to pause, coordinate, or work elsewhere?"
3. If your work proceeds, create your own `status/` entry within the first 5 minutes — don't wait until done.

**While working:**
- Update your `status/` entry when scope changes or you become blocked.
- Don't create new `decisions/` or `plans/` entries that contradict another agent's `status/` without coordinating first.

**Concurrent writes to MANIFEST.md** can conflict. For repos that frequently run multiple agents in parallel, use the ledger pattern documented in `reference.md` — each agent writes its MANIFEST entries to `docs/agent/ledger/{session-id}.md`, and the next agent to start merges them.

---

## Anti-Bloat Rules

The folder must not become a dumping ground. Apply these filters every time you consider writing:

1. **5-minute rule**: If a future agent could re-derive this in under 5 minutes from code or `git log`, don't write it.
2. **No duplication**: If it's in `AGENTS.md`, `CLAUDE.md`, `README.md`, or a code comment, link to it instead.
3. **No routine logging**: Code changes are in `git log`. Tasks are in your tool's task list. Neither belongs here.
4. **One topic, one note**: Update the existing note instead of creating a near-duplicate. For `instructions/` specifically: if a new user instruction overlaps an existing one, edit the existing file (bump `updated`) instead of creating a sibling.
5. **Status entries self-heal, then expire**: reconcile every `status/` entry against its `## Done when` anchor at session start and auto-archive the completed ones ([Reconciliation](#reconciliation--self-healing-status)). For any that survive reconciliation but have sat untouched >14 days, flag them to the user. Stale `status/` is the #1 failure mode — reconciliation is the primary defense, the age check is the backstop.
6. **Open questions age out**: 30 days `active` → ask the user if it's still open.
7. **Tags are search keys**: 3–5 tags per note. Reuse tags from existing notes — consistency makes search work.
8. **Revoked instructions are archived, not deleted**: when the user revokes an instruction, move the file to `archive/` rather than deleting it. Preserves the history of what was asked-then-rescinded, which is itself useful context.
9. **Summaries state durable facts, not transient state**: a MANIFEST 8-word summary and a status body must describe what is *durably* true, anchored to something checkable — not a point-in-time snapshot that rots. Write `"detect→fix CVE skills; shipped in PR #7"`, not `"BUILT (branch); pending PR/merge"`. The first stays meaningful forever and is verifiable; the second is wrong the moment the PR merges and tempts the next agent to relay it. If you must record current state, reference its anchor (a PR number, a commit) so live status is always re-derivable rather than asserted.

---

## Session Lifecycle

### Start of Session (mandatory, before any work)
1. `Glob: docs/agent/MANIFEST.md`. If missing, note and skip to user's request (do not auto-scaffold).
2. Read `MANIFEST.md`.
3. Read every file in `docs/agent/status/`.
4. **Reconcile** each `status/` entry against its `## Done when` anchor ([Reconciliation](#reconciliation--self-healing-status)): silently archive the demonstrably-complete ones (one-line note to the user each), flag the unverifiable ones as stale. Do this *before* you rely on any status entry.
5. Read every file in `docs/agent/instructions/`. Acknowledge any `importance: core` instruction in your opening response so the user can see the rule was loaded.
6. Read every `importance: core` note.
7. Scan `open-questions/` for anything matching the user's request.
8. Begin work — and apply every `active` instruction for the rest of the session.

### During Work
9. Before each major decision: check `decisions/` and `patterns/` for prior art.
10. Before debugging: check `investigations/` and `scars/`.
11. Within 5 minutes of starting non-trivial work: create a `status/` entry.
12. On every milestone (decision made, root cause found, plan finalized, scar earned): apply the Write Protocol immediately. Don't defer to end-of-session.
13. When the user uses persistent-intent phrasing (see [Auto-Capturing User Instructions](#auto-capturing-user-instructions)): silently write the instruction, then announce the file path and revocation phrase in one line.
14. Reference captured knowledge in responses — tell the user what you found.

### End of Session
15. Review: any decision, plan, root cause, scar, or standing user instruction uncaptured? Write it.
16. Update your `status/` entry: complete it (and archive), or update its current state.
17. If you flagged stale notes during the session, summarize them for the user before finishing.

---

## What This Is NOT

- **Not a task tracker.** Use the in-conversation task list or an issue tracker for todos.
- **Not a replacement for `AGENTS.md` / `CLAUDE.md`.** Those hold static rules; this holds dynamic state.
- **Not a replacement for documentation.** Public-facing docs, READMEs, API references belong in their normal locations.
- **Not a journal.** Per-session chronological logs are excluded by design — `git log` covers that.
- **Not cross-repo.** This is repo-local. For knowledge that crosses repos, pair with `obsidian-knowledge-graph` (separate skill, optional).
- **Not unlimited.** Designed for ~100–300 notes. Beyond that, split MANIFEST per section.

For extended patterns — team mode, multi-instance ledger, scaling, staleness heuristics, MCP integration — see `reference.md`.
