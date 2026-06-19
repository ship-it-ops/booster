# Vulnerability Fix Categories — Deep Rubric

For each of VF1–VF8: what it decides, antipatterns, and the apply-vs-advise boundary. Cross-references
to `reference.md`, the resolution files, and `ship-vuln-scan`'s `contract.md`.

---

## VF1 — UPGRADE-STRATEGY

Choose the target version. Prefer the **minimal fix** (lowest non-affected release ≥ installed) over
"latest" — smaller diff, lower breaking-change risk, easier to verify.

### Decision
- Minimal patch/minor with a clean changelog and green tests → **apply** candidate (still subject to
  the full gate).
- Only a major release fixes it, OR the changelog shows API/behavioral change → **advise** (breaking).

### Antipatterns
- Jumping to `latest` when a patch closes the CVE (imports unrelated breaking changes).
- Classifying risk from the version delta alone (rule 4) — a patch can break; a major can be trivial.

---

## VF2 — TRANSITIVE-RESOLUTION

When the vulnerable package is a *transitive* dep, you usually can't bump it directly. Use the
ecosystem's override mechanism — but keep manifest+lockfile consistent (see resolution files).

| Ecosystem | Mechanism |
|-----------|-----------|
| npm | `overrides` in package.json |
| yarn | `resolutions` |
| pnpm | `pnpm.overrides` |
| pip | constraints file (`-c constraints.txt`) |
| maven | `dependencyManagement` |
| go | `replace` directive |

### Antipatterns
- Force-pinning a transitive to a version the *direct* parent never tested against (peer-range
  violation) — this is a frequent silent breakage; the verify step's frozen install + tests must catch it.
- Editing only the lockfile or only the manifest → desync; the next clean `npm ci` regenerates/erros.

### Decision
An override that passes the frozen-install + tests + re-scan gate → apply. One that violates a peer
range or fails the frozen install → advise (needs a coordinated direct bump or a human).

---

## VF3 — BREAKING-CHANGE

Read the changelog/migration notes between installed and fixed version. This clause is what separates a
mechanical bump from a risky one.

### Decision
- No breaking/behavioral change documented + tests green → apply candidate.
- Breaking change, deprecation that affects used APIs, or no readable changelog → advise, with the
  migration steps surfaced.

### Antipatterns
- Skipping the changelog read because "tests pass" — tests may not cover the changed behavior.
- Trusting a major-version bump as safe because CI is green on a thin suite.

---

## VF4 — MITIGATION (always advise)

When no fix version exists (or only a breaking one does), produce a mitigation instead of an edit:
config change, disable the vulnerable feature/codepath, network control (egress block, WAF rule), or a
vendored backport/patch. Never auto-applied — these are judgment calls.

---

## VF5 — VERIFICATION

See `reference.md` § Verify protocol. The load-bearing rules: same engine + replayed `db_snapshot_id`,
target-CVE-closed AND no-new-vuln-in-subtree, clean frozen install, full tests.

### Antipatterns
- Declaring closure from the edit without a re-scan.
- Re-scanning with a different/weaker engine or a drifted DB.
- An incremental install in the agent's env instead of a clean frozen install.

---

## VF6 — PRIORITIZE / BATCH

Order by KEV → EPSS → CVSS × reachability. Apply per-fix atomically (apply → verify → commit-or-revert).
Bound convergence: stop and advise if the re-scan delta stalls or oscillates.

### Antipatterns
- Batch-apply then batch-revert (strands good fixes / leaves partial lockfile).
- Greedy looping on a peer-dep conflict with no iteration cap.
- Spending the apply budget on low-EPSS dev-only CVEs before KEV-listed ones.

---

## VF7 — ACCEPTED-RISK / VEX

For a finding that won't be fixed (not exploitable, or accepted), emit a VEX "not-affected" /
"affected-but-mitigated" statement with a justification (e.g. confirmed-unreachable per the scan's
reachability verdict) and an **expiry date** so it gets re-reviewed. Feed it back so future scans
suppress it with provenance.

### Antipatterns
- A permanent suppression with no expiry (rots into an unreviewed exception).
- A VEX justification that contradicts the scan's reachability confidence (don't assert "unreachable"
  on a low-confidence verdict).

---

## VF8 — APPLY-DISCIPLINE

The six-clause gate + rollback discipline. This is the category that makes the skill safe; see SKILL.md
§ apply gate and `reference.md` § Per-fix atomic protocol.

### Antipatterns
- Any edit on a dirty tree.
- Reverting a lockfile without reinstalling.
- Auto-applying a fix whose package adds an install script.

---

## Cross-references
- The apply gate and verify protocol — [`reference.md`](reference.md).
- Ecosystem override mechanics — [`resolution-npm.md`](resolution-npm.md), [`resolution-pip.md`](resolution-pip.md).
- The findings artifact + coverage/provenance fields — `ship-vuln-scan/contract.md`.
