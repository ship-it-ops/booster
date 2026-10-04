export const meta = {
  name: 'ship-execute-wave',
  description: 'Run one wave of independent plan tasks in parallel, each in its own git worktree: implement, verify, commit, and report the commit so the caller can bring it onto the execution branch',
  phases: [{ title: 'Implement', detail: 'one agent per task, each in an isolated worktree' }],
}

// args: the JSON printed by `plan_tasks.py <plan> wave`, passed as an object:
//   { startCommit: string,              // short sha of the execution branch tip the wave starts from
//     tasks: [{ id, briefPath, noCommit? }] }   // briefPath = a briefing file written by plan_tasks.py
// A task may carry the briefing text itself as `brief` in place of `briefPath`.
//
// Each agent runs in a fresh worktree cut from the commit that is checked out in the main
// checkout, on its own throwaway branch. Nothing reaches the execution branch from here:
// the caller cherry-picks each returned commit, re-runs the task's verification itself,
// and removes the worktree and branch afterwards.
//
// A task with a gate must never be in a wave: gated tasks run alone, after the user says yes.

let A = args
if (typeof A === 'string') {
  try {
    A = JSON.parse(A)
  } catch (e) {
    return { error: 'args arrived as a string that is not JSON; pass an object.' }
  }
}
const TASKS = (A && Array.isArray(A.tasks) && A.tasks) || []
const START = (A && A.startCommit) || ''

if (TASKS.length === 0) return { error: 'No tasks: pass { tasks: [{ id, brief }], startCommit }.' }
const bad = TASKS.filter((t) => !t || !t.id || !(t.brief || t.briefPath))
if (bad.length) return { error: 'Every task needs an id and a briefPath (or brief). Use the output of `plan_tasks.py <plan> wave`.' }
const gated = TASKS.filter((t) => t.gated || /^GATE\b/m.test(t.brief || ''))
if (gated.length) {
  return { error: `Gated tasks cannot run in a parallel wave: ${gated.map((t) => t.id).join(', ')}. Ask the user, then run each alone.` }
}

const TASK_RESULT_SCHEMA = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['done', 'needs-decision', 'blocked'] },
    commit: { type: 'string' },
    branch: { type: 'string' },
    worktree: { type: 'string' },
    startedFrom: { type: 'string' },
    answer: { type: 'string' },
    verifyCommand: { type: 'string' },
    verifyExitCode: { type: 'integer' },
    verifyOutputTail: { type: 'string' },
    filesChanged: { type: 'array', items: { type: 'string' } },
    deviations: { type: 'string' },
    question: { type: 'string' },
  },
  required: ['status', 'branch', 'startedFrom', 'filesChanged'],
}

function prompt(t) {
  return `You are implementing one task of an implementation plan, in your own git worktree. Other agents are doing other tasks at the same time in other worktrees, so stay inside yours.
${START ? `\nYour worktree should start at commit ${START}. Check with \`git rev-parse --short HEAD\`. If it shows something else, do not do the task: return status "blocked" and say what it showed.\n` : ''}
${t.brief ? t.brief : `Your briefing is the file ${t.briefPath}. Read it in full before doing anything; it is everything you need and everything you are allowed to rely on.`}

If the briefing has a line beginning "GATE", do not do the task: return status "blocked" and say that a gated task was sent to a parallel wave.

In your result, startedFrom is the short sha you started at, with nothing else, and worktree is the output of \`pwd\`. Leave commit empty if you did not commit.`
}

const results = await parallel(
  TASKS.map((t) => () =>
    agent(prompt(t), { label: `task:${t.id}`, phase: 'Implement', schema: TASK_RESULT_SCHEMA, isolation: 'worktree' })
  )
)

// A crashed or skipped agent is reported as blocked, never as done, and a "done" without a
// commit is not done: there would be nothing for the caller to bring onto the execution branch.
const tasks = TASKS.map((t, i) => {
  const r = results[i]
  if (!r) return { id: t.id, status: 'blocked', commit: '', deviations: 'The agent crashed or was skipped; no result was returned.' }
  if (r.status === 'done' && START && r.startedFrom && !r.startedFrom.startsWith(START) && !START.startsWith(r.startedFrom)) {
    return { id: t.id, ...r, status: 'blocked', deviations: `Started from ${r.startedFrom}, not ${START}. ${r.deviations || ''}`.trim() }
  }
  if (r.status === 'done' && !r.commit && !t.noCommit) {
    return { id: t.id, ...r, status: 'blocked', deviations: `Reported done without a commit. ${r.deviations || ''}`.trim() }
  }
  return { id: t.id, ...r }
})

const count = (s) => tasks.filter((t) => t.status === s).length
log(`wave: ${count('done')} done, ${count('needs-decision')} need a decision, ${count('blocked')} blocked`)

return {
  startCommit: START,
  tasks,
  next: 'First record each task\'s branch and worktree in the ledger. Then, for each task marked done, one at a time: run plan_tasks.py check on its commit, cherry-pick it onto the execution branch, run the task verification yourself there, and mark it done with the new sha. Remove a worktree and its branch only after its task is done in the ledger.',
}
