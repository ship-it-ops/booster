# Remediation Recipes & Tools (VF1 recipe-first)

`ship-vuln-fix` prefers a **tested, proven remediation recipe/tool** over a hand-rolled edit when one
exists for the CVE + ecosystem, and falls back to the manual minimal-edit (`resolution-npm.md` /
`resolution-pip.md`) otherwise. This mirrors `ship-vuln-scan`'s hybrid scanner model: orchestrate a
real tool when present, degrade gracefully when absent.

**The recipe never bypasses the evidence gate** (SKILL.md § apply gate clause 6). It changes *how the
fix is produced*, not *whether it is proven*: a recipe-generated change still has to pass the clean
frozen install + full tests + re-scan closure, and is reverted on any red exactly like a manual fix.

---

## Two classes of tool

### A. Runnable locally (the skill invokes + verifies)

| Tool | Ecosystems | What it does | Trust as evidence |
|------|-----------|--------------|-------------------|
| **OpenRewrite / Moderne** | Java/Maven/Gradle (strongest); growing Node/Python | **AST-aware, tested, deterministic** recipes: `UpgradeDependencyVersion`, dependency-vulnerability recipes, and framework-migration recipes (e.g. Spring Boot upgrades) that carry the *breaking* API migration | **High — but only when pinned + sandboxed.** A recipe's purpose is a proven migration, yet the recipe *process is third-party code* (it downloads + executes plugins). Trust requires a pinned `group:artifact:version` + checksum AND offline/no-credential execution (§ OpenRewrite). Only then can it move a *breaking* upgrade from advise → apply-eligible (opt-in + coverage floor). |
| **`npm audit fix` / `pnpm audit --fix`** | npm/pnpm | Bumps deps to non-vulnerable versions per the npm advisory DB | Medium — blunt. **Run without `--force`** (`--force` does SemVer-major bumps AND runs lifecycle scripts → violates the gate; any `--force`-class change routes to advise). Verify gate still required. |
| **`pip-audit --fix`** | pip | Upgrades vulnerable packages to the nearest fixed version | Medium — pinned-requirements only; verify required. |
| **`snyk fix`** | multi | Vendor-suggested upgrades/patches | Medium — requires Snyk auth; treat suggestions as candidates, not authority. |

### B. Configure-for-CI (the skill recommends, does NOT run)

| Tool | What it gives | How the skill uses it |
|------|---------------|-----------------------|
| **Renovate** | Grouped, scheduled upgrade PRs; configurable automerge; broad ecosystem coverage | Emit/adjust `renovate.json` (e.g. a `vulnerabilityAlerts` group); surface as the durable, CI-side remediation path for the long tail. |
| **Dependabot** | Security-update PRs + a **compatibility score** (% of public CI runs that passed that upgrade) | Show the compatibility score as **non-gating context only** — it reflects *other repos'* CI, not your API usage, so it must never feed the apply decision (closure rests on *your* tests + re-scan). Emit/adjust `.github/dependabot.yml`. |

These are platform services, not interactive CLIs — running them ad hoc on a dev machine isn't their
model. The skill treats them as the *standing* remediation system and itself as the *interactive,
verified* one; they compose.

---

## Selection logic (VF1)

```
recipe = recipe/tool for (cve, ecosystem)?
  Java/Maven/Gradle, recipe coordinate on the PINNED allowlist  -> OpenRewrite, sandboxed (see below)
  npm/pip, mechanical bump available                            -> native fixer (NON-force) OR manual edit
  none runnable / not pinned                                    -> manual minimal edit; recommend Renovate/Dependabot
provenance.fix_source = "<tool>@<pinned-coordinate>" | "<native-fixer>" | "manual"
```

Prefer the **most-tested** source available for the ecosystem; fall back down the list. Always record
which source produced the change in the audit record (`fix_source`). A recipe coordinate that is not on
the pinned allowlist is **not** a trusted source — fall through to manual.

---

## OpenRewrite — the breaking-upgrade case

The one place a recipe changes the *risk tiering* (not just the mechanics): a trusted OpenRewrite
migration recipe can move a **breaking** upgrade from always-advise to **apply-eligible**, because it
performs the API migration a raw version bump cannot. ALL of these must hold (SKILL.md § Recipe-first
rules 2 & 4):

- **Pinned + verified, not self-declared.** The recipe coordinate `group:artifact:version` is on the
  project's `trusted_recipe_coordinates` allowlist with a checksum/signature the skill verifies *before*
  running. A free-text "catalog id" or a coordinate that merely *looks* like core (typosquat, poisoned
  mirror) is rejected — trust is verified, never asserted.
- **Sandboxed execution.** The recipe process is third-party code. Run it **offline (no network) and
  with no credential env** — it downloads/executes plugins with full privileges *before* any sandboxed
  install. If it cannot run sandboxed/offline, treat it like clause 4's install-script trigger → advise.
- **AST migration is the recipe's declared purpose** (a version-only recipe does not license a break).
- **Coverage/reachability floor** over the changed API surface — a green *thin* suite is not proof of
  behavioral equivalence. Below the floor → advise.
- **Clause 6** (full tests + re-scan closure + frozen install) passes.
- **Per-package/per-recipe opt-in** (`recipe_assisted_breaking` is scoped, not a global on-switch).
  Default is **advise**.
- **Source-write disclosure + total revert.** The recipe rewrites import/call sites (source, not just
  manifests). Stage the *entire* recipe output before verify so the snapshot revert is total, bound the
  run's scope (max packages/files), and re-scan **after each recipe step**.

Run shape (pinned coordinate, sandboxed, recorded, reverted on failure like any fix):
```bash
# Maven — pinned plugin + recipe version, offline, no creds
mvn -o -U org.openrewrite.maven:rewrite-maven-plugin:<pinned-ver>:run \
  -Drewrite.activeRecipes=org.openrewrite.java.dependencies.UpgradeDependencyVersion ...
# or the Moderne CLI
mod run . --recipe <pinned-recipe-id>
```

---

## Honesty / availability

- Availability is probed (`command -v mvn`/`gradle`/`mod`/`snyk`; `npm`/`pip` present). If no
  recipe/tool is available, the skill falls back to the manual edit and **says so** — it never claims a
  recipe ran that didn't.
- OpenRewrite is JVM-heavy and strongest for Java; for npm/pip the native fixers + manual edits carry
  most of the load today. This breadth gap is a known v0.2 limitation, surfaced rather than hidden.
- Recipe runs happen under the same `Bash` discipline as installs (SKILL.md § Tooling boundary): only
  the recipe runners here, never arbitrary commands — and, per rule 2, the recipe *code* is treated as
  untrusted (pinned coordinate + offline + no credentials), because a recipe plugin executes before any
  sandboxed install and could otherwise exfiltrate secrets or write outside the manifest.

## Related
- [`reference.md`](reference.md) — apply gate, verify protocol, audit record (`fix_source` field).
- [`resolution-npm.md`](resolution-npm.md), [`resolution-pip.md`](resolution-pip.md) — the manual fallback edits.
