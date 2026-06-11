export const meta = {
  name: 'ship-execute-fanout',
  description: 'Run one independent ready-set of plan tasks in parallel, each in an isolated worktree: implement (TDD where specced), run the task verification, self-review. Returns a TASK_RESULT per task. DAG ordering + integration merges stay in the main skill loop.',
  phases: [
    { title: 'Implement', detail: 'one worktree-isolated agent per independent task' },
  ],
}

// args (passed by the skill for ONE ready-set of mutually-independent tasks):
//   { tasks: [{ id, prompt, acceptance, verifyCmd, paths }],
//     reworkMax?: number }   // bounded rework attempts per task (default 3)
//
// The caller (ship-execute main loop) is responsible for: computing ready-sets
// from the DAG, merging each returned branch into the integration branch one at
// a time, and re-running tests after each merge (the integration-merge gate).

const TASKS = (args && args.tasks) || []
const REWORK_MAX = (args && args.reworkMax) || 3

const TASK_RESULT_SCHEMA = {
  type: 'object',
  properties: {
    taskId: { type: 'string' },
    status: { type: 'string', enum: ['DONE', 'DONE_WITH_CONCERNS', 'NEEDS_CONTEXT', 'BLOCKED'] },
    evidence: { type: 'string' },
    concerns: { type: 'array', items: { type: 'string' } },
    filesTouched: { type: 'array', items: { type: 'string' } },
  },
  required: ['taskId', 'status', 'evidence'],
}

function taskPrompt(t) {
  return [
    `Implement this plan task in your isolated worktree. Make real, working changes.`,
    ``,
    `TASK ${t.id}: ${t.prompt}`,
    t.acceptance ? `\nACCEPTANCE CRITERIA:\n${t.acceptance}` : ``,
    t.paths ? `\nLIKELY FILES: ${(t.paths || []).join(', ')}` : ``,
    ``,
    `Discipline:`,
    `- If the task specifies tests, write the failing test first, watch it fail, then make it pass (TDD).`,
    `- After implementing, RUN the verification and read the real output — do not assume:`,
    `    ${t.verifyCmd || '(build + this task\'s tests + acceptance checks)'}`,
    `- It must be green before you report DONE. If it is red after up to ${REWORK_MAX} rework attempts,`,
    `  apply root-cause debugging; if still red, report BLOCKED with the evidence.`,
    `- If you are missing a decision or context you cannot safely assume, report NEEDS_CONTEXT.`,
    ``,
    `Return a TASK_RESULT. 'evidence' MUST be the exact command(s) you ran and their result.`,
  ].filter(Boolean).join('\n')
}

// One worktree-isolated agent per independent task — they touch the repo in
// parallel, so isolation:'worktree' is required to avoid collisions.
const results = await parallel(
  TASKS.map((t) => () =>
    agent(taskPrompt(t), {
      label: `task:${t.id}`,
      phase: 'Implement',
      schema: TASK_RESULT_SCHEMA,
      isolation: 'worktree',
    })
  )
)

// parallel() yields null for any thrown thunk — treat those as BLOCKED so the
// caller never mistakes a crashed task for a completed one.
const normalized = TASKS.map((t, i) => {
  const r = results[i]
  if (!r) return { taskId: t.id, status: 'BLOCKED', evidence: 'agent crashed or was skipped', concerns: [] }
  return r
})

const blocked = normalized.filter((r) => r.status === 'BLOCKED')
const needsContext = normalized.filter((r) => r.status === 'NEEDS_CONTEXT')
log(`fan-out: ${normalized.length} tasks → ${blocked.length} blocked, ${needsContext.length} need context`)

return {
  results: normalized,
  allGreen: blocked.length === 0 && needsContext.length === 0,
  blocked,
  needsContext,
}
