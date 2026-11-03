# Package managers: one package, scripts off

For each manager: the command that changes one package in the lock file, the install that runs no scripts, the frozen install that proves the manifest and the lock file agree, how a transitive version is forced, and how to see why a package is there. Flags change between major versions: run the tool's own `--version` and `--help` first, and where they disagree with this page, the tool is right. Use the manager and version the project uses (`preflight` says which); do not switch.

What "scripts off" does not cover: it stops install-time scripts. The package's code still runs when the tests import it, and a package that compiles or downloads something at install will be missing that part until its script is run on purpose. "Lock file only" is not "runs nothing" either:

- Python resolvers (`pip-compile`, `uv lock`, `poetry lock`) may download a source distribution and run its build to learn its dependencies. Prefer wheels where the tool has a switch for it (`--only-binary :all:`, `--no-build`), and say when a package had no wheel.
- A dependency taken from git is fetched and may be built by the package manager.
- The repository's own package-manager code runs on every command: `.pnpmfile.cjs`, yarn's `yarnPath` and plug-ins, a `preinstall` script in the root `package.json` when scripts are on. `preflight` names them. On a tree that is not the user's own, that is a reason not to run the package manager at all.

**How old is a version:** `npm view <name> time --json`, `pip index versions <name>` together with the release date on the index's page, `cargo info <name>`. A fix published in the last few days deserves a line in the answer; respect a minimum release age the project configures.

## npm

- **Lock file only, within the allowed range:** `npm update <name> --package-lock-only --ignore-scripts`. Works for a transitive package too: it moves to the newest version its parents' ranges allow.
- **Raise a direct dependency:** `npm install <name>@<version> --package-lock-only --ignore-scripts` (changes the range in `package.json` and the lock file; drop `--package-lock-only` to also update `node_modules`, still with `--ignore-scripts`).
- **Install what moved, scripts off:** `npm install --ignore-scripts`, with the lock file already updated. It changes only the packages whose versions moved and leaves the rest of `node_modules`, built parts included, alone. Afterwards the manifest and the lock file must be as they were before the command: if npm rewrote either, they disagreed.
- `npm ci --ignore-scripts` is the frozen install, and it fails when `package.json` and the lock file disagree. It also deletes `node_modules` first, so with scripts off every package that builds on install is left unbuilt. Use it only in a fresh checkout or when `preflight` lists no package with an install script.
- **Force a transitive version:** an `overrides` entry in `package.json` (npm 8.3 and later), then `npm install --package-lock-only --ignore-scripts`. Only in the root package of a workspace.
- **Why is it here:** `npm explain <name>`; `npm view <name>@<version> scripts dependencies` shows a version's install scripts and dependencies without installing it.
- `npm audit fix --package-lock-only --ignore-scripts` updates everything it can inside the ranges the manifest allows, in the lock file only. `npm audit fix --dry-run --json` says what a run would change. `--force` also crosses major versions and rewrites `package.json`; plain `npm audit fix` installs and runs scripts.
- Workspaces: run from the root; there is one lock file.

## pnpm

- **Update one package:** `pnpm update <name> --lockfile-only --ignore-scripts` (add `--recursive` in a workspace; a transitive package needs `--depth Infinity`). If your version rejects a flag on `update`, its help says which it takes.
- **Raise a direct dependency:** `pnpm add <name>@<version> --ignore-scripts`.
- **Frozen, script-free install:** `pnpm install --frozen-lockfile --ignore-scripts`.
- **Force a transitive version:** `pnpm.overrides` in the root `package.json`, or `overrides` in `pnpm-workspace.yaml` on recent versions.
- **Why:** `pnpm why <name>`.
- pnpm 10 does not run dependencies' install scripts unless the project lists them as allowed; an addition to that list in a change is something to report.

## yarn

- Yarn 1: `yarn upgrade <name>@<version> --ignore-scripts`. It has no lock-file-only mode, so this installs, and it rewrites the range in `package.json`; a transitive package inside its range needs its lock entry removed and `yarn install --ignore-scripts`. Frozen install: `yarn install --frozen-lockfile --ignore-scripts`, which does not fail reliably in a workspace. Transitive versions through `resolutions` in `package.json`.
- Yarn 2 and later: `yarn up <name>@<version> --mode=skip-build`; a transitive package inside its range: `yarn up -R <name> --mode=skip-build`; frozen install `yarn install --immutable --mode=skip-build`; `resolutions` as before.
- **Why:** `yarn why <name>`.

## pip, with requirements files

- A pinned `requirements.txt` is the lock file: change the one pin. If the file is generated (a header says by what, or it carries `--hash` lines), change the input file and regenerate with the same tool and only that package: `pip-compile --upgrade-package <name>==<version>`, `uv pip compile --upgrade-package <name>==<version>`.
- **Installing can run code:** a source distribution is built on install, running its build script. In a virtual environment the project already uses, `pip install --only-binary :all: -r requirements.txt` installs wheels only and fails where there is none; say which packages that leaves out.
- **Frozen install:** `pip install --require-hashes -r requirements.txt` for hashed files; otherwise `pip check` after installing.
- **Force a transitive version:** a constraints file (`-c constraints.txt`), or add the pin to the requirements input.
- Never install into the system interpreter. If the project has no virtual environment, say so and stop at the file change.

## poetry and uv

- poetry: `poetry update <name> --lock` (lock file only); raise a direct one with `poetry add <name>@<version> --lock`; check with `poetry check --lock`; install with `poetry sync` or `poetry install --sync`.
- uv: `uv lock --upgrade-package <name>` (optionally `<name>==<version>`); check with `uv lock --check`; install with `uv sync --locked` (it fails when the lock file is out of date; `--frozen` does not check), adding `--no-build` to refuse anything that would be built from source.
- **Why:** `poetry show --tree`, `uv tree --invert --package <name>`.

## Go

- `go get <module>@<version>` then `go mod tidy`; `go mod verify`. Fetching and building run no install scripts. A `replace` directive is the override, and it applies only in the main module.
- `go mod why -m <module>` says why it is there. `govulncheck ./...`, if installed, says whether the vulnerable symbol is called.

## Cargo

- `cargo update -p <name> --precise <version>` changes the lock file only. `cargo build` and `cargo test` run build scripts (`build.rs`) of every dependency: read `lockdiff` first.
- **Why:** `cargo tree -i <name>`.

## Maven and Gradle

- The version is in the build file or a parent; `dependencyManagement` (Maven) or a constraint (Gradle) forces a transitive version. `mvn dependency:tree -Dincludes=<group>:<artifact>` and `gradle dependencyInsight --dependency <name>` say why. Builds run plugins: a changed plugin version is code that will run.

## Reading a changelog honestly

After a script-free install the new version's files are on disk: its changelog, and its manifest with any scripts. Read the entries between the old version and the new one, and search this project for the functions they mention. If there is no changelog and no way to see what changed, say that you could not see it; do not write "no breaking changes".
