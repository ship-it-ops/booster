# Resolution — pip / poetry / uv (VF1 / VF2)

How to remediate Python dependency CVEs while keeping the resolved environment consistent. General gate
is in [`reference.md`](reference.md).

## Direct dependency (VF1)
Pin the fixed version and re-resolve under a clean install:
```bash
# requirements.txt: Jinja2==2.10.1
pip install --require-hashes -r requirements.txt    # or: pip-compile then pip-sync
# poetry:
poetry add "jinja2@^2.10.1" --lock                  # updates poetry.lock
poetry install --sync
# uv:
uv lock --upgrade-package jinja2 && uv sync
```
Verify (tests + re-scan) before committing.

## Transitive dependency (VF2)
The vulnerable package is pulled by another dependency. Constrain it:

| Tool | Mechanism | Example |
|------|-----------|---------|
| pip | constraints file | `pip install -c constraints.txt -r requirements.txt` with `urllib3>=1.26.18` |
| poetry | explicit dep + range | add the transitive to `[tool.poetry.dependencies]` with a fixed range |
| uv | `constraint-dependencies` / explicit pin | pin in `pyproject.toml`/`uv.lock` |

A constraint pins the resolved version without making it a first-class dependency; the resolver still
has to satisfy the parent's range.

## Consistency & risk (what the gate catches)
- **Resolver conflict:** if the constraint is incompatible with a parent's declared range, the install
  fails (or poetry/uv reports an unsolvable graph) → advise (needs a parent bump or a human).
- **Name normalization (PEP 503):** `Jinja2` / `jinja2` normalize the same — match before pinning.
- **Hashes:** prefer `--require-hashes` so the frozen install validates integrity; a hash mismatch
  after a pin → advise.
- **Environment markers:** a transitive may only install on some interpreters; verify against the
  environment the app actually runs in.

## Build-script trap (gate clause 4)
A package whose new version runs code at install (`setup.py` build, PEP 517 build hooks) is an
execution surface. In the apply loop, install with build isolation and without running project scripts
where possible; if the fixed version introduces a new build/install hook → **advise**.

## Verify
After the pin, run the project's test suite and re-scan with the same engine + replayed snapshot
(`reference.md` § Verify protocol). Closure = target CVE gone AND no new finding in the changed subtree.
