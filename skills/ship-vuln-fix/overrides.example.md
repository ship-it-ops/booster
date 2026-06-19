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
