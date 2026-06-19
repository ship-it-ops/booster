# ship-vuln-fix — Project Overrides (example)

Copy to `.ship-vuln-fix.overrides.md` (or your team's skill-config location) and edit. The skill reads
these to match team policy instead of guessing.

## Apply autonomy ceiling
Cap what the skill may auto-apply (default: the full evidence-gated tier):
```
# never auto-apply; advise everything (most conservative — mirrors ship-secure-code's stance)
apply_ceiling: advise-only
# or: allow direct-bump auto-apply but advise all transitive overrides
apply_ceiling: direct-only
```

## Test command (used by the verify gate)
The skill must run your real suite to prove a fix is safe:
```
build_cmd: npm run build
test_cmd:  npm test
# python:
# test_cmd: pytest -q
```

## Install discipline
```
install_scripts: disabled        # disabled (default) | sandboxed
frozen_install_cmd: npm ci --ignore-scripts
```

## Recipe-first (VF1 — see ecosystem-recipes.md)
```
# preferred recipe/tool per ecosystem (the skill probes availability and falls back to manual)
recipes:
  java:   openrewrite           # mvn rewrite:run / mod CLI (non-force native fixers for npm/pip)
  npm:    npm-audit-fix         # NON-force only; or: manual
  python: pip-audit-fix         # or: manual
# PINNED recipe coordinates the skill will verify (group:artifact:version + checksum) and run sandboxed.
# A coordinate not on this list is NOT trusted — the skill falls through to a manual edit.
trusted_recipe_coordinates:
  - "org.openrewrite.recipe:rewrite-java-dependencies:1.x.y"   # + sha256 in your lockfile/checksum store
# run recipe tools offline with no credentials (recipe code is third-party — default true; do not relax)
recipe_sandbox: { network: off, credentials: off }
# allow a PINNED recipe to auto-apply a BREAKING upgrade. Default off → advise. Scoped PER PACKAGE,
# not a global switch; only honored when AST-migration + coverage floor + clause 6 all pass.
recipe_assisted_breaking:
  enabled_for: []               # e.g. ["org.springframework.boot:spring-boot-starter"]
  coverage_floor: 0.8           # min coverage over the CHANGED API surface; below → advise
  max_changed_files: 50         # bound a single recipe run's blast radius; over → advise
```

## Convergence bound
```
max_fix_iterations: 10           # stop + advise if the apply loop exceeds this
require_monotonic_decrease: true # stop if a fix re-opens another CVE
```

## Audit log location
```
audit_dir: docs/security/vuln-remediation   # NOT docs/agent/ (owned by ship-agent-context)
```

## VEX defaults (VF7)
```
vex_default_expiry_days: 90      # accepted-risk statements expire and get re-reviewed
```

## Commit / PR policy
```
commit_per_fix: true             # one atomic commit per applied fix (default)
open_pr: never                   # never | ask ; the skill never pushes without explicit permission
```
