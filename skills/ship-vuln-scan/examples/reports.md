# Two answers

These show tone and proportion when nobody asked for another format. When a caller asks for one, use theirs.

## A scan with a scanner, an ignore file and gaps

The request: "Scan this repo for known vulnerabilities before the release."

> One critical advisory is being hidden by the repository's own ignore file, and two more should be fixed before the release. Dependencies and secrets were scanned; the container image and the Terraform were **not**.
>
> **Checked:** `package-lock.json` and `requirements.txt` with osv-scanner 2.2.1 (live query, 8 October), with and without `osv-scanner.toml`; the files and full git history with gitleaks 8.21.2. **Not checked:** the image (`Dockerfile` builds from `node:22-bookworm-slim`; no image exists locally and no image scanner is installed); `terraform/` (no policy scanner installed); whether any of these is being exploited (the exploited list could not be fetched).
>
> **Hidden by `osv-scanner.toml`**
>
> - `yamlite` 2.1.0, GHSA-xxxx-xxxx-xxxx (critical), fixed in 2.1.3. The entry has no expiry and says "only parses our own files". `src/import.js:14` passes an uploaded file to `yamlite.load`, so that reason does not hold. It comes in through `configkit`; 2.1.3 is inside the range `configkit` asks for, so a lock-file update is enough.
>
> **Should be fixed**
>
> - `httpkit` 4.2.0, GHSA-yyyy-yyyy-yyyy (high, request smuggling), fixed in 4.2.6. Direct dependency, used for every outbound call. A patch bump.
> - `pdfgen` 1.9.0, GHSA-zzzz-zzzz-zzzz (high), fixed only in 2.0.0. Used in `reports/render.js`. A major upgrade: read its migration notes first.
>
> **Can wait:** `lintkit` 5.1.0 (moderate, development only), fixed in 5.1.2.
>
> **Secret:** `config/legacy.env:3`, a payments API key (rule `generic-api-key`), committed in `a1b2c3d`. Rotate it; removing the line leaves it in history.
>
> Commands: `osv-scanner scan source -r --format json .` (twice, the second with `--config` pointing at an empty file); `gitleaks git --redact --report-format json .`.

What to notice: the first lines say what is most serious, what was checked and what was not; the suppressed finding is shown with the reason the file gives and whether it holds; each finding says how it gets in and what kind of fix it is; the secret's value appears nowhere.

## No scanner and no network

The request: "Check our dependencies for known CVEs."

> I could not check: no scanner is installed here and the advisory service is not reachable, so I have no advisory data. That is not a clean result.
>
> What is pinned: `package-lock.json` has 212 packages (14 direct); `requirements.txt` pins 9. `osv-scanner.toml` tells osv-scanner to ignore one advisory, GHSA-xxxx-xxxx-xxxx, with no expiry.
>
> To get an answer, either run this where the network is available:
>
> `python3 <skill>/scripts/vuln_scan.py osv package-lock.json requirements.txt`
>
> or install `osv-scanner` and run `osv-scanner scan source -r .` (once more with `--config` pointing at an empty file, to see what the ignore file hides). `npm audit` failed with a network error, which is not a result either.

What to notice: "could not check" is the first sentence; nothing is recited from memory; the user gets the exact command.
