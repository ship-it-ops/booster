# ship-vuln-fix — Reference

Full remediation procedure, the apply-gate decision in detail, the verify protocol, and rollback
discipline. `SKILL.md` is the lean dispatcher; read this before the first run. Per-category depth is in
[`reference-categories.md`](reference-categories.md); ecosystem resolution mechanics in
[`resolution-npm.md`](resolution-npm.md) and [`resolution-pip.md`](resolution-pip.md).

---

## Procedure (detail)

1. **Load findings.** Read a `ship-vuln-scan` artifact (`ship-vuln-scan/contract.md` shape). If none
   exists, run `ship-vuln-scan` first. Read `coverage[]` BEFORE anything — refuse to remediate any
   finding whose surface is `degraded`/`not-scanned` (you cannot prove closure on it).
2. **Prioritize** (VF6): order findings KEV → EPSS → CVSS × reachability. Respect the reachability
   confidence floor (don't deprioritize a Tier-1 on a low-confidence "unreachable").
3. **Tier each finding** apply-safe vs advise-risky against the six-clause gate (SKILL.md § apply gate).
4. **Confirm.** Present the apply set + the advise set to the user and get a go before editing.
5. **Apply-safe set:** run the per-fix atomic protocol (below), one finding at a time.
6. **Advise-risky set:** produce exact diffs + verification steps; for no-fix, a mitigation or a VEX
   with expiry (VF7).
7. **Report:** what was applied (with audit records), what was advised, what was skipped and why, and
   the residual risk.

---

## Apply-gate decision (the six clauses, in order)

Evaluate top-down; the first failing clause routes the finding to ADVISE.

| # | Clause | Fail → |
|---|--------|--------|
| 1 | Working tree clean | refuse the whole run (not just this finding) |
| 2 | Fix is a version bump or transitive override (mechanical, not a code edit) | advise |
| 3 | Changelog between installed and fixed version readable, no breaking/behavioral change | advise |
| 4 | Fixed version adds no new install/build script | advise (untrusted-code-execution surface) |
| 5 | Originating scan surface coverage == `full` | advise |
| 6 | Post-edit verification passes (VF5) | revert + advise |

Clause 1 is global: a dirty tree aborts the apply phase entirely, because per-fix revert is only
well-defined from a clean baseline.

---

## Verify protocol (VF5) — proving closure

After each edit, before the commit:

```bash
# a) consistency: the manifest+lockfile pair survives a clean, frozen, script-disabled install
npm ci --ignore-scripts                      # or: pip install --require-hashes -r requirements.txt
                                             #     yarn install --immutable
                                             #     go mod verify && go build ./...
# b) build + full test suite green (read the real output — never assume)
<project build> && <project test>
# c) re-scan closure: SAME engine, REPLAYED db_snapshot_id from the original finding
ship-vuln-scan  (target advisory ids closed?  AND  no NEW finding in the changed dependency subtree?)
```

Three traps the protocol closes:
- **DB drift.** Replay the original `db_snapshot_id` so closure reflects the *bump*, not an advisory
  the feed withdrew/added between scans. Compare only the targeted `advisory_ids` for closure.
- **New vuln in the bump.** A bump can pull a newer transitive with its own CVE. Closure requires *no
  new finding in the changed subtree*, not just the original CVE gone.
- **Blind verify.** If the verify re-scan used a weaker/absent engine than the original scan, it cannot
  prove closure → revert + advise.

---

## Per-fix atomic protocol & rollback (VF6 / VF8)

One finding at a time:

```
snapshot = HEAD                       # clean tree guaranteed by clause 1
apply minimal edit (Edit: lockfile/manifest only)
install --ignore-scripts
verify (VF5)
  green → git commit  (single fix)  +  append audit record
  red   → git checkout -- . ; git reset --hard snapshot ; reinstall   # restore tree AND installed state
          record finding as "attempted → failed → advise"
```

- **Never batch-then-revert.** Reverting a 5-fix batch either nukes the good fixes or strands a
  partially-applied lockfile. Atomic per-fix keeps each fix independently revertible.
- **Reinstall after revert.** Reverting the lockfile file alone leaves `node_modules`/`site-packages`
  inconsistent — the next build is nondeterministic. Always reinstall after a revert.
- **Convergence bound:** track the re-scan finding-count after each fix. If it is not monotonically
  decreasing (a fix re-opened another CVE via a peer-dep conflict), STOP and advise the remainder —
  the dependency tree needs a global solver or a human, not more greedy per-fix attempts.

---

## Remediation audit record (schema)

Appended to `docs/security/vuln-remediation/<date>-<cve>.json` on every auto-apply (timestamps are
supplied by the caller — the skill does not invent them):

```json
{
  "cve": "CVE-2021-23337",
  "advisory_ids": ["GHSA-35jh-r3h4-6jhm"],
  "scanner": { "engine": "osv-scanner", "version": "1.9.2", "db_snapshot_id": "osv-2026-06-18" },
  "change": { "ecosystem": "npm", "package": "lodash", "from": "4.17.11", "to": "4.17.21",
              "mechanism": "direct-bump | override" },
  "evidence": {
    "changelog_reviewed": true,
    "breaking_change": false,
    "new_install_scripts": false,
    "frozen_install_consistent": true,
    "tests": { "ran": true, "passed": true },
    "rescan": { "engine": "osv-scanner", "target_closed": true, "new_findings_in_subtree": 0 }
  },
  "approved_by": "<user/gate>",
  "applied_at": "<ISO-8601 from caller>"
}
```

---

## Advise output (for risky / no-fix findings)

Each advised finding produces:
- the exact diff or override snippet that *would* fix it (so a human can apply it),
- why it was not auto-applied (which gate clause failed),
- the verification steps to run after a manual apply,
- for no-fix-available: a mitigation (config/feature-disable/network) OR a VEX "not-affected"
  statement with a justification (e.g. confirmed-unreachable) and an expiry date (VF7).

---

## Anti-patterns (do not do)

- Auto-applying on "it's just a patch" without the evidence clauses.
- Editing on a dirty working tree.
- Batching fixes then reverting the batch.
- Claiming closure from the edit instead of a re-scan.
- Reverting a lockfile without reinstalling.
- Writing the audit log into `docs/agent/` (that namespace belongs to `ship-agent-context`).
- Opening a PR / pushing without explicit user permission.

---

## Related
- [`reference-categories.md`](reference-categories.md) — VF1–VF8 deep rubric.
- [`resolution-npm.md`](resolution-npm.md), [`resolution-pip.md`](resolution-pip.md) — transitive resolution mechanics.
- `ship-vuln-scan/contract.md` — the findings artifact this consumes.
