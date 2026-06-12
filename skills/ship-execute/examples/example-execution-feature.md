# Example — executing a feature plan with `/ship-execute`

Walks the 5 stages on the per-tenant rate-limiting plan from the `ship-better-plans` feature example. Shows the gate, the per-step evidence, final vetting, and the handoff.

---

**Stage 1 — Pre-flight**

```
Loaded docs/agent/plans/per-tenant-rate-limiting.md
DAG: T1→T2→{T3,T4} (T3,T4 independent)   critical path: T1→T2→T4
ship-code: available   plan mode: no
Branch: feat/per-tenant-rate-limiting   status entry written.

Execute per-tenant-rate-limiting: 4 tasks (2 parallelizable), mode dag.
Will write code and run commands (build/tests/git) in feat/per-tenant-rate-limiting.
Estimated ~80k tokens. Proceed? (yes / dry-run / cancel)
> yes
```

**Stage 2–3 — DAG execution with per-step gates**

```
T1 token-bucket lib (critical path, sequential)
  implement (TDD: wrote rl.test.ts → red → green)
  run: `npm run build && npm test -- rl.test.ts` → 12 passing ✓
  review: ship-clean-code → P3 naming nit fixed
  → DONE (evidence: npm test rl.test.ts, 12 passing)

T2 wire into auth middleware (sequential)
  run: `npm test -- middleware` → green ✓ ; acceptance AC for FR-1/3 checked
  review: ship-secure-code (auth path) → no Tier-1 → DONE

{T3 metrics, T4 load test} — independent ready-set → Workflow fan-out (2 worktrees)
  task:T3 → DONE  (evidence: metrics exported, `npm test -- metrics` green)
  task:T4 → DONE  (evidence: load test: tenant capped, others unaffected — AC-1 met)
  integration-merge gate: merge T3, re-test → green; merge T4, re-test → green
```

**Stage 4 — Final vetting**

```
full suite: `npm test` → 247 passing ✓
acceptance: FR-1✓ FR-2✓ FR-3✓ (each mapped + checked)
ship-reviewed-prs on BASE..HEAD → APPROVE (SE/SC/IN, no blockers)
→ rubber-stamped.
```

**Stage 5 — Handoff**

```
Evidence summary:
  4/4 tasks done · full suite 247✓ · 3/3 acceptance criteria met
  ship-reviewed-prs: APPROVE · diff: 7 files, +318 −12

Next:
  [1] Review locally   [2] Open a PR (needs your ok)   [3] Keep branch   [4] Discard
> 2
Open a PR for feat/per-tenant-rate-limiting? This will push to origin. (yes/no)
> yes
Pushed · PR #214 opened. Plan status → completed; status entry archived.
```
