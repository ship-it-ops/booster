export const meta = {
  name: 'ship-better-plans-audit',
  description: 'Multi-persona plan audit: parallel persona review, adversarial refute pass, keep only confirmed findings. Ultra mode loops until dry.',
  phases: [
    { title: 'Review', detail: 'each persona reviews the full plan in parallel' },
    { title: 'Verify', detail: 'adversarially try to refute each finding; keep the unrefuted' },
  ],
}

// args (passed by the skill):
//   { planText: string,
//     mode: 'standard' | 'ultra',
//     personas: [{ key, prompt }],   // core + context-adaptive, chosen by the skill
//     dryRounds?: number }           // ultra: consecutive empty rounds before stopping (default 2)

const PLAN = (args && args.planText) || ''
const MODE = (args && args.mode) || 'standard'
const PERSONAS = (args && args.personas) || [
  { key: 'adversarial', prompt: 'Try to break this plan. Find false assumptions, missing edge cases, unstated dependencies, and steps that will fail in practice.' },
  { key: 'pragmatist', prompt: 'Find over-engineering, YAGNI violations, premature abstraction, and scope creep. What can be cut without losing a success criterion?' },
  { key: 'production', prompt: 'Review for security, infra, observability, rollback, and compliance gaps. What breaks in production that looks fine on paper?' },
]
const DRY_ROUNDS = (args && args.dryRounds) || 2

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
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          detail: { type: 'string' },
          section: { type: 'string' },
        },
        required: ['id', 'title', 'severity', 'detail'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
    reasoning: { type: 'string' },
  },
  required: ['refuted', 'confidence', 'reasoning'],
}

const keyOf = (f) => `${(f.title || '').toLowerCase().trim()}::${f.section || ''}`

// One find->verify round, deduped against `seen`. Returns newly confirmed findings.
async function round(roundIdx, seen) {
  const reviews = await parallel(
    PERSONAS.map((p, i) => () =>
      agent(`${p.prompt}\n\nReturn findings with stable ids prefixed "${p.key}-".\n\nPLAN:\n${PLAN}`, {
        phase: 'Review',
        label: `review:${p.key}:r${roundIdx}`,
        schema: FINDINGS_SCHEMA,
      })
    )
  )

  // parallel() yields null for any thrown thunk — filter before flatMap (audit C1).
  const fresh = reviews
    .filter(Boolean)
    .flatMap((r) => r.findings || [])
    .filter((f) => !seen.has(keyOf(f)))

  if (fresh.length === 0) return []
  fresh.forEach((f) => seen.add(keyOf(f)))

  const verified = await pipeline(fresh, (f) =>
    agent(
      `Adversarially try to REFUTE this plan finding. Default refuted=true if uncertain.\n\nFinding: ${f.title}\nDetail: ${f.detail}\n\nPLAN:\n${PLAN}`,
      { phase: 'Verify', label: `verify:${f.id}`, schema: VERDICT_SCHEMA }
    ).then((v) => (v ? { ...f, verdict: v } : null))
  )

  return verified.filter(Boolean).filter((x) => !x.verdict.refuted)
}

const confirmed = []
const seen = new Set()

if (MODE === 'ultra') {
  let dry = 0
  let r = 0
  while (dry < DRY_ROUNDS) {
    const got = await round(r, seen)
    if (got.length === 0) {
      dry++
    } else {
      dry = 0
      confirmed.push(...got)
    }
    log(`ultra round ${r}: +${got.length} confirmed (${confirmed.length} total, dry ${dry}/${DRY_ROUNDS})`)
    r++
  }
} else {
  confirmed.push(...(await round(0, seen)))
  log(`standard audit: ${confirmed.length} confirmed findings`)
}

return {
  mode: MODE,
  personaCount: PERSONAS.length,
  confirmed,
  blockers: confirmed.filter((f) => f.severity === 'blocker'),
}
