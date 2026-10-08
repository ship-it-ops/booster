# Scanners: the invocation that only reads, and what to watch for

Flags and output change between versions, and several of these tools were restructured recently. Run the tool's own `--version` first; read its `--help` when it rejects a flag given here, and where they disagree, the tool is right. `OUT` below stands for a file in the session's scratch or temp directory, never in the repository.

For every tool: a non-zero exit can mean "found something" or "failed". Write JSON to `OUT` and run `vuln_scan.py summarise OUT`; if it refuses the file, the run was an error and the target is not checked.

## osv-scanner (lock files and manifests, many ecosystems)

- Reads lock files and asks api.osv.dev; no project code runs. Needs the network unless an offline database was downloaded beforehand.
- Version 2: `osv-scanner scan source -r --format json --output OUT DIR`. Version 1: `osv-scanner -r --format json --output OUT DIR`. One file: `--lockfile PATH`.
- **The repository's ignore file is `osv-scanner.toml`,** read from the directory of each scanned file. It can ignore advisories by id and whole packages. To scan without it, pass `--config` pointing at an empty file you created in the scratch directory. When entries were applied the scanner says how many results it filtered.
- Exit status: 0 nothing found, 1 vulnerabilities found, higher values for errors (no lock files found is an error, not a clean result).
- It lists a source only when it found something there. The summary it prints (how many packages from which files) is how you know what was scanned: quote it. An output with an empty `results` list and nothing else is refused by `summarise` for this reason.
- Options that analyse or resolve more than the lock file can run build tooling. Call analysis is one, and for Go it is on unless switched off: on code that is not the user's own pass the flag that disables it (`--no-call-analysis=all` in version 1, `--call-analysis=none` or the equivalent your version's help names), and do not ask it to resolve a manifest that has no lock file.

## trivy and grype (file trees and images)

- `trivy fs --scanners vuln --format json --output OUT DIR`; `grype dir:DIR -o json --file OUT`. Both download a vulnerability database on first use and refresh it: that is a network download, and without it they fail or use a stale copy. The database's date is in `trivy version` and `grype db status`: report it.
- **Ignore files:** `.trivyignore` and `.trivyignore.yaml` (switched off with `--ignorefile` pointed at an empty file), `trivy.yaml` (switched off with `--config` pointed at an empty file: it can set severities, skip paths and name an ignore file), and `.grype.yaml` (switched off with `--config` pointed at an empty file).
- trivy leaves npm development dependencies out unless given `--include-dev-deps`: pass it, or say they were not scanned.
- By default trivy exits 0 even with findings; `--exit-code` changes that. Both hide nothing by severity unless a flag or config says so: look for `--severity`, `--ignore-unfixed`, `--only-fixed`, `--fail-on` in CI commands.
- **Images:** `trivy image NAME` and `grype NAME` will pull an image that is not already local. Check it is local first; do not pull.
- `trivy config DIR` is a policy check of infrastructure code, not a vulnerability scan. Report it separately.

## npm, pnpm and yarn audit

- `npm audit --json > OUT` reads the lock file and sends the dependency tree to the registry the project is configured for (which may be a private one, with the user's credentials). It needs a lock file and the network; with neither it prints an error, in JSON when `--json` is given: `summarise` refuses it.
- It exits non-zero when it finds anything at or above the audit level. `--omit=dev` and `--audit-level` narrow what is reported: note them when a CI command uses them.
- `npm audit fix` changes files. It is not a scan, and it is not yours to run.
- `pnpm audit --json` is the equivalent, and `summarise` reads it. `yarn npm audit --json --recursive` (yarn 2 and later; without `--recursive` only direct dependencies are checked) and `yarn audit --json` (yarn 1) print one JSON object per line, which `summarise` does not read: use `vuln_scan.py osv yarn.lock` instead.
- All three run in the project directory and so read its `.npmrc` or `.yarnrc.yml`: the audit goes to whatever registry that names, with whatever token it holds, and yarn 2 runs the plug-ins and `yarnPath` the repository names. That is why they are not run on work that is not the user's own.
- `npm ls NAME` and `npm explain NAME` say how a package gets in. They read `node_modules` and the lock file and change nothing.

## pip-audit

- `pip-audit` with no arguments audits the packages installed in whichever Python environment is active, and changes nothing. That is the project only when the project's own virtual environment is the active one: say which environment it was, or do not use this form.
- `pip-audit -r requirements.txt` **resolves the file first**, which downloads packages and can build them, running their build scripts. For a fully pinned file use `pip-audit -r requirements.txt --no-deps --disable-pip -f json -o OUT`, which only looks the pins up; say that dependencies not listed in the file were not checked. For anything else, use `osv-scanner` or `vuln_scan.py osv` on the lock file.

## gitleaks and trufflehog (secrets)

- gitleaks 8.19 and later: `gitleaks git --redact --report-format json --report-path OUT DIR` for history, `gitleaks dir --redact ...` for the files as they are. Earlier 8.x: `gitleaks detect --redact ...`, with `--no-git` for files only. **Always `--redact`:** without it the secret is printed to the terminal and written to the report.
- Ignore files: `.gitleaksignore` (fingerprints) and allowlists in `.gitleaks.toml`. `--gitleaks-ignore-path` pointed at an empty directory scans without the first.
- trufflehog **verifies what it finds against the live service by default**, and updates itself when it starts: always pass `--no-verification --no-update`. `trufflehog git file://DIR --no-verification --no-update --json > OUT`. It has no redaction: the output holds each secret in full, so it goes to the file and never to the terminal.
- Read either report with `vuln_scan.py secrets OUT`, which prints file, line, rule and commit and never the value. Do not open the report yourself.
- With neither tool installed, a search of the tree for key-shaped strings covers the current files only, finds only the obvious, and prints what it matches: search for the names of variables (`KEY`, `TOKEN`, `SECRET`, `PASSWORD`) and report locations, not lines.

## checkov

- `checkov -d DIR -o json --output-file-path SCRATCHDIR`. A policy scanner for infrastructure code. It reads `.checkov.yaml` from the repository, which can skip checks and point at extra check code: on a tree that is not the user's own, do not run it.
- Inline `checkov:skip=` comments suppress individual checks: `inventory` counts them.

## When nothing is installed

`vuln_scan.py osv package-lock.json requirements.txt ...` reads the lock files itself and asks api.osv.dev. It covers npm (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`), Python (`requirements*.txt` with `==` pins, `poetry.lock`, `uv.lock`, `Pipfile.lock`), Go (`go.mod`), Rust (`Cargo.lock`) and PHP (`composer.lock`). It says how many packages it asked about and lists what it could not check (unpinned lines, packages installed from git or a path). Packages that come from a registry other than the public one are held back and listed, not sent: the script reads that from the lock file where the format records it, and otherwise from the `.npmrc` or `.yarnrc.yml` beside it; a requirements file that names a private index is not sent at all. `--include-private` sends them, once the user has agreed. `--dry-run --names` shows exactly what would go. It is a version match against the lock file: it does not see what is actually installed, vendored code, or an image.

With no scanner and no network, there is no result. Say so, list what is pinned (the inventory), and give the user the one command that would answer the question.
