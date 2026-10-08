#!/usr/bin/env python3
"""Mechanics for ship-vuln-scan: what is there to scan, what a scan said, and what changed.

    vuln_scan.py inventory [DIR] [--json]
    vuln_scan.py summarise RESULT.json [--json]
    vuln_scan.py compare BASE.json HEAD.json
    vuln_scan.py osv LOCKFILE... [--out RESULT.json] [--dry-run]
    vuln_scan.py exploited (--from RESULT.json | CVE-ID...)
    vuln_scan.py secrets REPORT
    vuln_scan.py lockdiff OLD NEW

`inventory` lists manifests, lock files, images and infrastructure code, and every file or
flag that makes a scanner leave findings out. `summarise` reads the JSON a scanner wrote
(osv-scanner, npm audit, pip-audit, trivy, grype, or this script's `osv`) and prints one
line per advisory; it refuses anything that is not a scan result, so an error is never
read as "clean". `compare` says which advisories a change introduced. `osv` is the route
when no scanner is installed: it reads lock files and asks api.osv.dev, which means it
sends package names and versions there (packages from private registries are held back
unless asked for). `exploited` looks advisories up in CISA's Known Exploited
Vulnerabilities list and in EPSS. `secrets` reads a secret scanner's report and prints
where each hit is, never its value. `lockdiff` compares two versions of a lock file and
flags what a change brought in that no advisory describes: a gained install script, another
source, the same version with different content, a breaking-range version.

Standard library only. Nothing here installs, builds, resolves or edits anything.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

OSV_API = os.environ.get("SHIP_VULN_OSV_API", "https://api.osv.dev")
# CISA publishes the catalogue on cisa.gov and mirrors it on GitHub; the first refuses some clients.
KEV_URLS = [u for u in os.environ.get("SHIP_VULN_KEV_URL", "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json "
                                      "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json").split() if u]
LABEL_RANK = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "MEDIUM": 2, "LOW": 1}
EPSS_API = os.environ.get("SHIP_VULN_EPSS_API", "https://api.first.org/data/v1/epss")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".terraform", "dist", "build", ".tox", ".mypy_cache"}
FLAGGED = 1
NOT_A_RESULT = 2
NO_NETWORK = 3

LOCKFILES = {
    "package-lock.json": "npm", "npm-shrinkwrap.json": "npm", "yarn.lock": "npm", "pnpm-lock.yaml": "npm",
    "poetry.lock": "PyPI", "uv.lock": "PyPI", "Pipfile.lock": "PyPI",
    "go.mod": "Go", "Cargo.lock": "crates.io", "composer.lock": "Packagist", "Gemfile.lock": "RubyGems",
    "gradle.lockfile": "Maven",
}
MANIFESTS = {
    "package.json": ("npm", ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml")),
    "pyproject.toml": ("PyPI", ("poetry.lock", "uv.lock", "requirements.txt")),
    "Pipfile": ("PyPI", ("Pipfile.lock",)),
    "Cargo.toml": ("crates.io", ("Cargo.lock",)),
    "composer.json": ("Packagist", ("composer.lock",)),
    "Gemfile": ("RubyGems", ("Gemfile.lock",)),
    "pom.xml": ("Maven", ()),
    "build.gradle": ("Maven", ("gradle.lockfile",)),
    "build.gradle.kts": ("Maven", ("gradle.lockfile",)),
}
# Files a scanner reads on its own and that can remove findings from its output.
SUPPRESSION_FILES = {
    "osv-scanner.toml": "osv-scanner", ".trivyignore": "trivy", ".trivyignore.yaml": "trivy", "trivy.yaml": "trivy",
    ".grype.yaml": "grype", "grype.yaml": "grype", ".gitleaksignore": "gitleaks", ".gitleaks.toml": "gitleaks", ".checkov.yaml": "checkov",
    ".checkov.yml": "checkov", ".nsprc": "npm audit wrappers", "audit-ci.json": "audit-ci", "audit-ci.jsonc": "audit-ci",
    ".snyk": "snyk", "audit-resolve.json": "npm audit wrappers", "deny.toml": "cargo-deny", "audit.toml": "cargo-audit",
}
# Keys inside ordinary configuration files that narrow an audit.
SUPPRESSION_KEYS = {"package.json": ("auditConfig", "ignoreCves", "ignoreGhsas"), "pnpm-workspace.yaml": ("auditConfig", "ignoreCves", "ignoreGhsas"),
                    ".yarnrc.yml": ("npmAuditIgnoreAdvisories", "npmAuditExcludePackages")}
LEGACY_OVERRIDES = ("ship-vuln-scan.overrides.md", ".ship-vuln-scan.overrides.md", "ship-vuln-scan-overrides.md")
PUBLIC_HOSTS = ("registry.npmjs.org", "registry.yarnpkg.com", "registry.npmmirror.com", "pypi.org", "files.pythonhosted.org", "pypi.python.org",
                "index.crates.io", "static.crates.io", "github.com/rust-lang/crates.io-index", "packagist.org", "repo.packagist.org")
# Inputs of scanner actions and environment variables that narrow a scan without a command-line flag.
NARROWING_INPUTS = re.compile(r"^\s*-?\s*(severity|ignore-unfixed|trivyignores|skip-dirs|skip-files|vuln-type|scanners|only-fixed|fail-build|severity-cutoff|audit-level|"
                              r"TRIVY_[A-Z_]+|GRYPE_[A-Z_]+|OSV_SCANNER_[A-Z_]+)\s*[:=]\s*(\S.*)$")
INLINE_MARKERS = ("checkov:skip", "trivy:ignore", "gitleaks:allow", "tfsec:ignore", "nosemgrep", "kics-scan ignore")
NARROWING_FLAGS = ("--ignore-vuln", "--ignore-unfixed", "--severity", "--audit-level", "--omit", "--skip-dirs", "--skip-files",
                   "--ignorefile", "--only-fixed", "--fail-on", "--exclude", "--baseline", "--ignore-policy", "--vex", "--config")
ID_PATTERN = re.compile(r"\b(CVE-\d{4}-\d{4,}|GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}|PYSEC-\d{4}-\d+|RUSTSEC-\d{4}-\d+|GO-\d{4}-\d+|MAL-\d{4}-\d+)\b")


def fail(code, message):
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(code)


def read_text(path, limit=400_000):
    """The file's text, or "" for a file that cannot be read or is a symlink (a link can point outside the tree)."""
    if os.path.islink(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


# ------------------------------------------------------------------ inventory
NOT_WALKED = []


def walk(root):
    for base, dirs, files in os.walk(root):
        NOT_WALKED.extend(os.path.relpath(os.path.join(base, d), root) for d in dirs if d in SKIP_DIRS and d != ".git")
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not os.path.islink(os.path.join(base, d)))
        for name in sorted(files):
            yield base, name


def suppression_entries(path, name):
    """The advisory ids and patterns a suppression file names, as (what, detail) pairs."""
    text = read_text(path)
    entries = []
    if name == "osv-scanner.toml":
        blocks = None
        if tomllib is not None:
            try:
                data = tomllib.loads(text)
                blocks = [("IgnoredVulns", b) for b in data.get("IgnoredVulns", [])] + [("PackageOverrides", b) for b in data.get("PackageOverrides", [])]
            except (tomllib.TOMLDecodeError, AttributeError, TypeError):
                blocks = None
        if blocks is None:
            blocks = []
            for block in re.split(r"(?m)^\s*\[\[", text)[1:]:
                kind = block.split("]]", 1)[0].strip()
                fields = {k: v.strip().strip("\"'") for k, v in re.findall(r"(?m)^\s*(\w+)\s*=\s*(.+?)\s*$", block)}
                blocks.append((kind, fields))
        for kind, fields in blocks:
            if not isinstance(fields, dict):
                continue
            what = fields.get("id") or (f"package {fields.get('name')}" if fields.get("name") else None)
            if what is None:
                entries.append((f"an entry in [[{kind}]] that could not be read", "open the file"))
                continue
            until = fields.get("ignoreUntil") or fields.get("effectiveUntil")
            detail = [] if kind == "IgnoredVulns" else [kind + (" (ignores the package)" if fields.get("ignore") else "")]
            detail.append(f"until {until}" if until else "no expiry")
            if fields.get("reason"):
                detail.append(f'reason given: "{fields["reason"]}"')
            entries.append((str(what), "; ".join(detail)))
        if not entries and text.strip() and re.search(r"(?m)^\s*\[", text):
            entries.append(("entries could not be read", "open the file"))
        return entries
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ids = ID_PATTERN.findall(stripped)
        if ids:
            rest = ID_PATTERN.sub("", stripped).strip(" :-")
            entries.extend((i, f"line {number}" + (f"; {rest[:60]}" if rest else "")) for i in ids)
        elif name == ".gitleaksignore":
            entries.append((":".join(stripped.split(":")[-3:])[:80], f"line {number} (a finding's fingerprint)"))
        elif re.search(r"skip[-_]check|skip[-_]path|allowlist|ignore|exclude|severity|vex|db[-_]repository|server|paths|regexes|stopwords", stripped, re.I):
            entries.append((re.sub(r"(://)[^/@\s]+@", r"\1<hidden>@", stripped)[:80], f"line {number}"))
    return entries


def inventory(root):
    root = os.path.abspath(root)
    inv = {"root": root, "lockfiles": [], "manifests_without_lock": [], "requirements": [], "images": [], "infrastructure": [],
           "suppressions": [], "inline_suppressions": [], "narrowing_flags": [], "vendored": [], "symlinks": [], "legacy_overrides": [], "package_manager_config": []}
    seen_dirs = {}
    del NOT_WALKED[:]
    for base, name in walk(root):
        rel = os.path.relpath(os.path.join(base, name), root)
        seen_dirs.setdefault(base, set()).add(name)
        if name in LOCKFILES:
            inv["lockfiles"].append({"path": rel, "ecosystem": LOCKFILES[name]})
        elif re.fullmatch(r"requirements.*\.(txt|in)", name) or name == "constraints.txt":
            text = read_text(os.path.join(base, name))
            lines = [l for l in text.splitlines() if l.strip() and not l.strip().startswith(("#", "-"))]
            pinned = sum(1 for l in lines if re.match(r"\s*[A-Za-z0-9_.\-\[\]]+\s*==", l))
            inv["requirements"].append({"path": rel, "ecosystem": "PyPI", "lines": len(lines), "pinned": pinned, "hashed": "--hash=" in text})
        elif name == "Dockerfile" or name.startswith("Dockerfile.") or name.endswith(".Dockerfile") or name == "Containerfile":
            bases = re.findall(r"(?mi)^\s*FROM\s+(?:--platform=\S+\s+)?(\S+)", read_text(os.path.join(base, name)))
            inv["images"].append({"path": rel, "base_images": bases})
        elif re.fullmatch(r"(docker-)?compose.*\.ya?ml", name):
            inv["images"].append({"path": rel, "base_images": re.findall(r"(?m)^\s*image:\s*['\"]?([^'\"\s]+)", read_text(os.path.join(base, name)))})
        elif name.endswith((".tf", ".tf.json")) or name in ("Chart.yaml", "kustomization.yaml", "serverless.yml", "template.yaml"):
            inv["infrastructure"].append(rel)
        if os.path.islink(os.path.join(base, name)):
            inv["symlinks"].append(rel)
            continue
        if name in LEGACY_OVERRIDES:
            inv["legacy_overrides"].append(rel)
        if name in SUPPRESSION_KEYS:
            text = read_text(os.path.join(base, name))
            keys = [k for k in SUPPRESSION_KEYS[name] if re.search(r"[\"']?%s[\"']?\s*:" % k, text)]
            if keys:
                ids = sorted(set(ID_PATTERN.findall(text)))
                inv["suppressions"].append({"path": rel, "read_by": "the package manager's audit", "entries": [{"what": i, "detail": "listed under " + "/".join(keys)} for i in ids] or [{"what": "/".join(keys), "detail": "open the file"}]})
        if name in (".npmrc", ".yarnrc.yml", ".yarnrc", "pip.conf", ".pnpmfile.cjs") or (name == "config.toml" and os.path.basename(base) == ".cargo"):
            text = read_text(os.path.join(base, name), 100_000)
            notes = []
            if name == ".pnpmfile.cjs":
                notes.append("code that runs on every pnpm command")
            for line in text.splitlines():
                line = line.strip()
                m = re.search(r"https?://([^/@\s]+@)?([^/\s\"']+)", line)
                if m and re.search(r"registry|index-url|npmRegistryServer|\[registries|\[source", line + text[:0], re.I):
                    notes.append("packages come from " + m.group(2))
                if re.match(r"(yarnPath|plugins)\b", line):
                    notes.append(line.split(":")[0] + ": code from the repository that every yarn command runs")
                if re.search(r"audit-level|omit\s*=", line):
                    notes.append("narrows npm audit: " + line[:60])
            if notes:
                inv["package_manager_config"].append({"path": rel, "notes": sorted(set(notes))})
        if name in SUPPRESSION_FILES and (name != "audit.toml" or os.path.basename(base) == ".cargo"):
            entries = suppression_entries(os.path.join(base, name), name)
            inv["suppressions"].append({"path": rel, "read_by": SUPPRESSION_FILES[name], "entries": [{"what": w, "detail": d} for w, d in entries]})
        elif name == "config.yaml" and os.path.basename(base) == ".grype":
            entries = suppression_entries(os.path.join(base, name), ".grype.yaml")
            inv["suppressions"].append({"path": rel, "read_by": "grype", "entries": [{"what": w, "detail": d} for w, d in entries]})
        if os.path.basename(base) in ("vendor", "third_party", "vendored") and os.path.relpath(base, root) not in inv["vendored"]:
            inv["vendored"].append(os.path.relpath(base, root))
        is_ci = ".github" in rel.split(os.sep) or name in (".gitlab-ci.yml", "Makefile", "Jenkinsfile", "azure-pipelines.yml") or rel.startswith(".circleci") or name.endswith(".sh")
        small_text = name.endswith((".yml", ".yaml", ".tf", ".sh", ".py", ".js", ".ts", ".toml", ".json", ".env")) or name in ("Dockerfile", "Makefile")
        if is_ci or small_text:
            text = read_text(os.path.join(base, name), 200_000)
            for marker in INLINE_MARKERS:
                count = text.count(marker)
                if count:
                    inv["inline_suppressions"].append({"path": rel, "marker": marker, "count": count})
            if is_ci or name == "package.json":
                names_scanner = re.search(r"osv-scanner|trivy|grype|gitleaks|checkov|pip-audit|npm audit|pnpm audit|yarn (npm )?audit|snyk|audit-ci", text)
                for number, line in enumerate(text.splitlines(), 1):
                    if names_scanner and is_ci and NARROWING_INPUTS.match(line):
                        inv["narrowing_flags"].append({"path": rel, "line": number, "flags": [NARROWING_INPUTS.match(line).group(1)], "text": line.strip()[:160]})
                    elif re.search(r"osv-scanner|trivy|grype|gitleaks|checkov|pip-audit|npm audit|pnpm audit|yarn (npm )?audit|snyk|audit-ci", line):
                        flags = [f for f in NARROWING_FLAGS if f in line]
                        if flags:
                            inv["narrowing_flags"].append({"path": rel, "line": number, "flags": flags, "text": line.strip()[:160]})
    for base, names in seen_dirs.items():
        for manifest, (ecosystem, locks) in MANIFESTS.items():
            if manifest in names and not any(l in names for l in locks):
                if manifest == "pyproject.toml" and any(re.fullmatch(r"requirements.*\.txt", n) for n in names):
                    continue
                parent_has_lock = any(l in seen_dirs.get(os.path.dirname(base), set()) for l in locks) or any(l in seen_dirs.get(root, set()) for l in locks)
                inv["manifests_without_lock"].append({"path": os.path.relpath(os.path.join(base, manifest), root), "ecosystem": ecosystem,
                                                      "note": "a lock file higher up may cover it (workspace)" if parent_has_lock and base != root else "no lock file beside it: resolved versions are unknown"})
    gitdir = os.path.join(root, ".git")
    if os.path.isfile(gitdir):  # a worktree or submodule: .git is a file that points at the real directory
        m = re.match(r"gitdir:\s*(.+)", read_text(gitdir))
        gitdir = os.path.normpath(os.path.join(root, m.group(1).strip())) if m else gitdir
        common = read_text(os.path.join(gitdir, "commondir")).strip()
        shallow = os.path.isfile(os.path.join(os.path.normpath(os.path.join(gitdir, common)) if common else gitdir, "shallow"))
        inv["git"] = {"repository": True, "shallow": shallow}
    else:
        inv["git"] = {"repository": os.path.isdir(gitdir), "shallow": os.path.isfile(os.path.join(gitdir, "shallow"))}
    inv["not_walked"] = sorted(set(NOT_WALKED))
    return inv


def print_inventory(inv):
    def section(title, rows, empty):
        print(f"\n{title}")
        if not rows:
            print(f"  {empty}")
        for row in rows:
            print(f"  {row}")
    print(f"Inventory of {inv['root']}")
    section("Lock files and pinned manifests (what a dependency scan reads):", [f"{l['path']}  [{l['ecosystem']}]" for l in inv["lockfiles"]], "none")
    section("Requirements files:", [f"{r['path']}  {r['pinned']} of {r['lines']} lines pinned with ==" + ("; hashed" if r["hashed"] else "") for r in inv["requirements"]], "none")
    section("Manifests with no lock file beside them:", [f"{m['path']}  [{m['ecosystem']}]  {m['note']}" for m in inv["manifests_without_lock"]], "none")
    section("Images (a Dockerfile says what is built, not what is in the image):", [f"{i['path']}  from {', '.join(i['base_images']) or '?'}" for i in inv["images"]], "none")
    section("Infrastructure code:", inv["infrastructure"][:40] + ([f"... and {len(inv['infrastructure']) - 40} more"] if len(inv["infrastructure"]) > 40 else []), "none")
    section("Vendored code (copied in, not in any lock file):", inv["vendored"], "none")
    print("\nFiles that make a scanner leave findings out (each entry hides something; report them):")
    if not inv["suppressions"]:
        print("  none found among: " + ", ".join(sorted(SUPPRESSION_FILES)) + "; audit keys in package.json, pnpm-workspace.yaml, .yarnrc.yml. An ignore file under "
              "another name, passed by a flag or an action input, is not found here: open each CI step that runs a scanner.")
    for s in inv["suppressions"]:
        print(f"  {s['path']}  (read by {s['read_by']}), {len(s['entries'])} entr{'y' if len(s['entries']) == 1 else 'ies'}")
        for e in s["entries"][:30]:
            print(f"    - {e['what']}  ({e['detail']})")
        if len(s["entries"]) > 30:
            print(f"    ... and {len(s['entries']) - 30} more")
    if inv["legacy_overrides"]:
        print("\nLegacy ship-vuln-scan overrides file (it has no effect; say so once): " + ", ".join(inv["legacy_overrides"]))
    section("Package-manager configuration that steers an audit or runs code:", [f"{c['path']}  " + "; ".join(c["notes"]) for c in inv["package_manager_config"]], "none found")
    if inv["symlinks"]:
        print("\nSymbolic links (not followed or read; a link in a change under review is worth a line): " + ", ".join(inv["symlinks"][:20]))
    section("Inline suppressions:", [f"{i['path']}  {i['marker']} x{i['count']}" for i in inv["inline_suppressions"]], "none found")
    section("Scanner commands in CI or scripts with flags, inputs or variables that narrow the scan:", [f"{n['path']}:{n['line']}  {' '.join(n['flags'])}  |  {n['text']}" for n in inv["narrowing_flags"]],
            "none recognised (this matches known flag and input names on lines near a scanner's name; it is not proof that nothing narrows a scan)")
    if inv.get("not_walked"):
        print("\nDirectories not walked, so nothing in them is listed above: " + ", ".join(inv["not_walked"][:20]) + (" ..." if len(inv["not_walked"]) > 20 else ""))
    git = inv["git"]
    print(f"\nGit: {'a repository' if git['repository'] else 'not a repository'}{'; SHALLOW clone, history is incomplete' if git['shallow'] else ''}")


# --------------------------------------------------------- reading scan results
def score_of(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def finding(vid, aliases, package, version, ecosystem, fixed, score, label, source, summary):
    ids = [vid] + [a for a in aliases if a != vid]
    return {"id": vid, "aliases": sorted(set(ids) - {vid}), "package": package, "version": version, "ecosystem": ecosystem,
            "fixed": fixed, "score": score, "label": (label or "").upper() or None, "source": source, "summary": (summary or "").strip()[:140]}


def norm_name(name, ecosystem=None):
    name = name or ""
    return re.sub(r"[-_.]+", "-", name).lower() if (ecosystem or "").lower() == "pypi" else name


def version_key(version):
    return tuple(int(x) if x.isdigit() else x for x in re.findall(r"\d+|[A-Za-z]+", version or ""))


def fixed_from_osv(vuln, package, ecosystem=None):
    """Fixed versions from ranges that give versions (not git commits), for this package where the advisory names it."""
    fixes, any_package = [], []
    for affected in vuln.get("affected", []):
        named = (affected.get("package") or {}).get("name")
        for rng in affected.get("ranges", []):
            if rng.get("type") == "GIT":
                continue
            found = [e["fixed"] for e in rng.get("events", []) if "fixed" in e]
            any_package += found
            if named is None or norm_name(named, ecosystem) == norm_name(package, ecosystem):
                fixes += found
    chosen = sorted(set(fixes or any_package), key=version_key)
    return ", ".join(chosen) or None


def nearest_fix(installed, fixed):
    """The lowest fixed version above the installed one: with several maintained release lines, the highest named is not the fix for this install."""
    have = version_key(installed or "")
    options = sorted({v.strip() for v in str(fixed or "").split(",") if v.strip() and v.strip()[0].isdigit()}, key=version_key)
    try:
        above = [v for v in options if version_key(v) > have] if have and str(installed)[0].isdigit() else []
    except TypeError:
        above = []
    return above[0] if above else None


def parse_result(data):
    """Returns (tool, findings, scanned) or raises ValueError when this is not a scan result this script reads."""
    if not isinstance(data, dict):
        raise ValueError("the file is JSON but not an object a scanner writes")
    out = []
    if "results" in data and isinstance(data["results"], list) and "auditReportVersion" not in data:
        foreign = [k for k in ("errors", "paths", "metrics", "version", "skipped_rules", "runs") if k in data]
        shaped = all(isinstance(r, dict) and isinstance(r.get("source"), dict) and isinstance(r.get("packages"), list) for r in data["results"])
        if not data["results"] and not foreign and not ("experimental_config" in data or "ship_vuln_scan" in data):
            raise ValueError("an empty `results` list and nothing else: that cannot be told apart from a scan that read nothing. Check the scanner's own printed summary for the files and package counts it read")
        if foreign or not shaped:
            raise ValueError("it has a `results` list but not in osv-scanner's shape (each entry with `source` and `packages`); another tool's output, or an error")
        scanned = []
        for result in data["results"]:
            source = result["source"].get("path", "?")
            scanned.append(source)
            for pkg in result["packages"]:
                p = pkg.get("package", {})
                scores = {}
                for group in pkg.get("groups", []):
                    for i in group.get("ids", []) + group.get("aliases", []):
                        scores[i] = score_of(group.get("max_severity"))
                for vuln in pkg.get("vulnerabilities", []):
                    out.append(finding(vuln.get("id", "?"), vuln.get("aliases", []), p.get("name"), p.get("version"), p.get("ecosystem"),
                                       fixed_from_osv(vuln, p.get("name"), p.get("ecosystem")), scores.get(vuln.get("id")),
                                       (vuln.get("database_specific") or {}).get("severity"), source, vuln.get("summary")))
        queried = (data.get("ship_vuln_scan") or {}).get("sources")
        return "osv-scanner", out, (queried or scanned)
    if "auditReportVersion" in data and isinstance(data.get("vulnerabilities"), dict):
        for name, entry in data["vulnerabilities"].items():
            for via in entry.get("via", []):
                if isinstance(via, dict):
                    url = via.get("url", "")
                    vid = url.rsplit("/", 1)[-1] if "GHSA-" in url else str(via.get("source", "?"))
                    fix = entry.get("fixAvailable")
                    fixed = (f"by installing {fix.get('name')}@{fix.get('version')}" + (" (a major upgrade)" if fix.get("isSemVerMajor") else "")) if isinstance(fix, dict) else ("a fix is available (version not given)" if fix else None)
                    out.append(finding(vid, [], via.get("name", name), "affected range " + str(via.get("range")), "npm", fixed, score_of((via.get("cvss") or {}).get("score")) or None,
                                       via.get("severity"), "package-lock.json", via.get("title")))
        total = ((data.get("metadata") or {}).get("dependencies") or {}).get("total")
        if total == 0:
            raise ValueError("npm audit examined 0 dependencies: nothing was audited")
        return "npm audit", out, [f"npm audit of the lock file ({total if total is not None else '?'} dependencies examined)"]
    if isinstance(data.get("advisories"), dict) and isinstance(data.get("metadata"), dict):  # pnpm audit, npm 6
        for adv in data["advisories"].values():
            versions = sorted({f.get("version") for f in adv.get("findings", []) if f.get("version")}, key=version_key)
            aliases = list(adv.get("cves") or [])
            vid = adv.get("github_advisory_id") or (aliases[0] if aliases else str(adv.get("id", "?")))
            out.append(finding(vid, aliases, adv.get("module_name"), ", ".join(versions) or "affected range " + str(adv.get("vulnerable_versions")), "npm",
                               adv.get("patched_versions"), score_of((adv.get("cvss") or {}).get("score")) or None, adv.get("severity"), "lock file", adv.get("title")))
        total = data["metadata"].get("totalDependencies", data["metadata"].get("dependencies"))
        if total == 0:
            raise ValueError("the audit examined 0 dependencies: nothing was audited")
        return "pnpm audit", out, [f"audit of the lock file ({total if total is not None else '?'} dependencies examined)"]
    if isinstance(data.get("dependencies"), list) and all(isinstance(d, dict) and "name" in d for d in data["dependencies"]):
        skipped = [d for d in data["dependencies"] if d.get("skip_reason")]
        for dep in data["dependencies"]:
            for vuln in dep.get("vulns", []):
                out.append(finding(vuln.get("id", "?"), vuln.get("aliases", []), dep.get("name"), dep.get("version"), "PyPI",
                                   ", ".join(vuln.get("fix_versions", [])) or None, None, None, "pip-audit", vuln.get("description")))
        if len(data["dependencies"]) == len(skipped):
            raise ValueError("pip-audit audited 0 packages" + (f" ({len(skipped)} skipped)" if skipped else "") + ": nothing was checked")
        scanned = [f"pip-audit ({len(data['dependencies']) - len(skipped)} packages audited)"]
        if skipped:
            scanned.append("NOT AUDITED by pip-audit: " + ", ".join(f"{d['name']} ({d['skip_reason'][:50]})" for d in skipped[:10]))
        return "pip-audit", out, scanned
    if "Results" in data and ("SchemaVersion" in data or "ArtifactName" in data):
        scanned, other = [], 0
        for result in data.get("Results") or []:
            scanned.append(result.get("Target", "?"))
            other += len(result.get("Misconfigurations") or []) + len(result.get("Secrets") or [])
            for vuln in result.get("Vulnerabilities") or []:
                cvss = vuln.get("CVSS") or {}
                score = max([score_of(v.get("V3Score")) or 0 for v in cvss.values()] or [0]) or None
                out.append(finding(vuln.get("VulnerabilityID", "?"), [], vuln.get("PkgName"), vuln.get("InstalledVersion"), result.get("Type"),
                                   vuln.get("FixedVersion") or None, score, vuln.get("Severity"), result.get("Target", "?"), vuln.get("Title")))
        if other:
            scanned.append(f"({other} misconfiguration or secret entries in this file are not read here)")
        if not scanned:
            raise ValueError("trivy lists no targets (`Results` is empty): it found nothing it could scan, which is not a clean result")
        return "trivy", out, scanned
    if "matches" in data and isinstance(data["matches"], list) and ("descriptor" in data or "source" in data):
        for match in data["matches"]:
            v, a = match.get("vulnerability", {}), match.get("artifact", {})
            scores = [score_of((c.get("metrics") or {}).get("baseScore")) or 0 for c in v.get("cvss", [])]
            related = [r.get("id") for r in match.get("relatedVulnerabilities", []) if r.get("id")]
            target = (data.get("source") or {}).get("target")
            out.append(finding(v.get("id", "?"), related, a.get("name"), a.get("version"), a.get("type"),
                               ", ".join((v.get("fix") or {}).get("versions", [])) or None, max(scores or [0]) or None, v.get("severity"),
                               target.get("userInput", "?") if isinstance(target, dict) else str(target or "?"), v.get("description")))
        scanned = ["grype's target (grype does not list the files it read: confirm from its own printed summary that it catalogued packages)"]
        if data.get("ignoredMatches"):
            scanned.append(f"({len(data['ignoredMatches'])} matches were suppressed by grype's ignore rules)")
        return "grype", out, scanned
    raise ValueError("valid JSON, but not a result from osv-scanner, npm audit, pnpm audit, pip-audit, trivy, grype or this script: an error object, or a format this script does not read")


def load_result(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError as e:
        fail(NOT_A_RESULT, f"{path}: cannot be read ({e.strerror}). Not a scan result: treat the target as NOT CHECKED.")
    if not raw.strip():
        fail(NOT_A_RESULT, f"{path}: empty. The scanner wrote nothing, which is an error, not a clean result: treat the target as NOT CHECKED.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        fail(NOT_A_RESULT, f"{path}: not JSON (first line: {raw.strip().splitlines()[0][:120]!r}). Treat the target as NOT CHECKED.")
    try:
        return parse_result(data)
    except ValueError as e:
        fail(NOT_A_RESULT, f"{path}: {e}. If it is an error, the target is NOT CHECKED. If it is another tool's valid output, read it yourself and say that you did.")


def key(f):
    return (f["package"], tuple(sorted([f["id"]] + f["aliases"])))


def rank(row):
    if str(row["id"]).startswith("MAL-") or any(str(a).startswith("MAL-") for a in row["aliases"]):
        return 99.0
    return row["score"] if row["score"] is not None else LABEL_RANK.get(row["label"] or "", 0) * 2.4


def merged(findings):
    """One row per advisory per package: the same advisory under two ids or in two lock files is one finding."""
    rows = []
    for f in findings:
        ids = set([f["id"]] + f["aliases"])
        for row in rows:
            if row["package"] == f["package"] and row["version"] == f["version"] and ids & set([row["id"]] + row["aliases"]):
                row["aliases"] = sorted((set(row["aliases"]) | ids) - {row["id"]})
                if f["source"] not in row["sources"]:
                    row["sources"].append(f["source"])
                row["score"] = max(x for x in (row["score"], f["score"], 0) if x is not None) or None
                for field in ("fixed", "label", "summary"):
                    row[field] = row[field] or f[field]
                break
        else:
            row = dict(f)
            row["sources"] = [row.pop("source")]
            rows.append(row)
    for row in rows:
        if rank(row) == 99.0:
            row["label"] = "MALICIOUS PACKAGE"
    return sorted(rows, key=lambda r: (-rank(r), r["package"] or "", r["id"]))


def short(path):
    try:
        rel = os.path.relpath(path)
    except ValueError:
        return path
    return rel if os.path.isabs(str(path)) and not rel.startswith("..") else path


def shown_ids(row, limit=2):
    """The id and the aliases a reader would look up; vendor mirrors of the same advisory are left to --json."""
    aliases = [a for a in row["aliases"] if not a.startswith(("BIT-", "SNYK-"))]
    return row["id"] + (" (" + ", ".join(aliases[:limit]) + ")" if aliases else "")


def print_summary(tool, rows, scanned):
    scanned = [short(s) for s in scanned]
    print(f"Result from: {tool}")
    print(f"Sources ({len(scanned)}): " + ("; ".join(scanned[:12]) or "none listed") + (" ..." if len(scanned) > 12 else ""))
    if tool == "osv-scanner":
        print("Note: osv-scanner lists a source only when it found something in it. Its own printed summary (which files, how many packages) is what says the rest were scanned.")
    packages = {}
    for r in rows:
        packages.setdefault((r["package"], r["version"], r["ecosystem"]), []).append(r)
    print(f"Advisories: {len(rows)} in {len(packages)} package(s), after merging aliases and duplicates\n")
    if not rows:
        print("No advisories in this result. That is a statement about the sources above and the scanner's configuration only.")
        return
    for (package, version, ecosystem), group in sorted(packages.items(), key=lambda kv: -max(rank(r) for r in kv[1])):
        nearest = [nearest_fix(version, r["fixed"]) for r in group]
        try:
            clears = f"; lowest version that clears all of them: {max(nearest, key=version_key)}" if nearest and all(nearest) else ""
        except TypeError:
            clears = ""
        print(f"- {package} {version}  [{ecosystem}]  {len(group)} advisor{'y' if len(group) == 1 else 'ies'}{clears}  (in: {', '.join(sorted({short(x) for r in group for x in r['sources']}))})")
        for r in group[:4]:
            severity = " ".join(x for x in (f"{r['score']:.1f}" if r["score"] is not None else "", r["label"] or "") if x) or "NO SEVERITY IN THIS RESULT (rate it as high until a tool says otherwise; never from memory)"
            print(f"    {shown_ids(r)}: {severity}; fixed in: {r['fixed'] or 'no fixed version in result'}" + (f"; {r['summary']}" if r["summary"] else ""))
        if len(group) > 4:
            print(f"    ... and {len(group) - 4} more for this package (`--json` lists them)")
    print("\nSeverity is the advisory's own rating as this result gives it: not exploitability, and not whether this code reaches the flaw.")


def compare(base_path, head_path):
    base_tool, base, _ = load_result(base_path)
    head_tool, head, _ = load_result(head_path)
    base_rows, head_rows = merged(base), merged(head)

    def same(a, b):
        return a["package"] == b["package"] and set([a["id"]] + a["aliases"]) & set([b["id"]] + b["aliases"])
    introduced = [h for h in head_rows if not any(same(h, b) for b in base_rows)]
    gone = [b for b in base_rows if not any(same(b, h) for h in head_rows)]
    kept = [h for h in head_rows if any(same(h, b) for b in base_rows)]
    for title, rows in (("Introduced (in HEAD, not in BASE)", introduced), ("No longer reported (in BASE, not in HEAD)", gone), ("In both", kept)):
        if title.startswith("Introduced") and base_tool != head_tool:
            print(f"WARNING: the two results come from different tools ({base_tool}, {head_tool}); differences may be the tools, not the change.")
        print(f"{title}: {len(rows)}")
        for r in rows:
            score = f"{r['score']:.1f}" if r["score"] is not None else "no score"
            print(f"  - {r['package']} {r['version']}  {shown_ids(r)}  {score}  fixed in: {r['fixed'] or '?'}")
    print("\nThis means something only when both results come from the same scanner and the same target, and the one intended difference is the change or the ignore configuration.")
    return 0


# ------------------------------------------------------------ lock file parsing
def toml_packages(text):
    """The [[package]] tables of a lock file, with tomllib when there is one and a small reader when there is not."""
    if tomllib is not None:
        return tomllib.loads(text).get("package", [])
    packages = []
    for block in re.split(r"(?m)^\[\[package\]\]\s*$", text)[1:]:
        head = re.split(r"(?m)^\[\[?(?!package\.source)", block)[0]
        fields = dict(re.findall(r'(?m)^(name|version|source)\s*=\s*"([^"]*)"', head))
        src = re.search(r"(?ms)^\[package\.source\]\s*$(.*?)(?=^\[|\Z)", block)
        if src:
            fields["source"] = dict(re.findall(r'(?m)^(\w+)\s*=\s*"([^"]*)"', src.group(1)))
        elif re.search(r"(?m)^source\s*=\s*\{", head):
            fields["source"] = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', re.search(r"(?m)^source\s*=\s*\{(.*)\}", head).group(1)))
        packages.append(fields)
    return packages


def packages_from(path, include_private=False):
    """Returns (ecosystem, [(name, version)], [(what, why not checked)])."""
    if os.path.islink(path):
        raise ValueError("it is a symbolic link; give the real file")
    name = os.path.basename(path)
    text = read_text(path, 50_000_000)
    found, skipped = [], []

    def private(pkg, resolved):
        host = re.search(r"https?://(?:[^/@\s]*@)?([^/\s\"']+)(/[^\s\"']*)?", resolved or "")
        if host and not include_private and host.group(1) not in PUBLIC_HOSTS and (host.group(1) + (host.group(2) or "")).rstrip("/") not in PUBLIC_HOSTS:
            skipped.append((pkg, f"comes from {host.group(1)}, not a public registry: not sent (pass --include-private only if the user agrees)"))
            return True
        return False
    # Formats that do not say where each package comes from: the package manager's configuration beside the lock file is the only sign.
    scoped, default_private = {}, None
    for config in (".npmrc", ".yarnrc.yml"):
        try:
            for line in read_text(os.path.join(os.path.dirname(os.path.abspath(path)), config), 100_000).splitlines():
                m = re.match(r"\s*(?:\"?(@[\w.-]+)\"?:)?\s*(?:registry|npmRegistryServer)\s*[=:]\s*[\"']?https?://(?:[^/@\s]*@)?([^/\s\"']+)", line)
                if m and m.group(2) not in PUBLIC_HOSTS:
                    if m.group(1):
                        scoped[m.group(1)] = m.group(2)
                    else:
                        default_private = m.group(2)
        except OSError:
            pass

    def unlisted_private(pkg):
        """For entries with no download address in the lock file."""
        if include_private:
            return False
        scope = pkg.split("/")[0] if pkg.startswith("@") else None
        where = scoped.get(scope) or default_private
        if where:
            skipped.append((pkg, f"the package manager's configuration here sends {'this scope' if scope in scoped else 'every package'} to {where}, and this lock file does not say where "
                                 f"each package came from: not sent (pass --include-private only if the user agrees)"))
            return True
        return False
    if name in ("package-lock.json", "npm-shrinkwrap.json"):
        data = json.loads(text)
        if "packages" in data:
            for where, entry in data["packages"].items():
                if not where:
                    continue
                pkg = entry.get("name") or where.split("node_modules/")[-1]
                if "node_modules/" not in where:
                    skipped.append((where, "a workspace member, not a published package"))
                elif entry.get("link"):
                    skipped.append((pkg, "workspace link"))
                elif not entry.get("version"):
                    skipped.append((pkg, "no version"))
                elif entry.get("resolved", "").startswith(("git", "file:", "github:")):
                    skipped.append((pkg, "installed from git or a file, not a registry"))
                elif not private(pkg, entry.get("resolved")) and not (not entry.get("resolved") and unlisted_private(pkg)):
                    found.append((pkg, entry["version"]))
        else:
            def old(deps):
                for pkg, entry in (deps or {}).items():
                    if entry.get("version", "").startswith(("git", "file:", "github:", "http")):
                        skipped.append((pkg, "not from a registry"))
                    elif entry.get("version") and not private(pkg, entry.get("resolved")):
                        found.append((pkg, entry["version"]))
                    old(entry.get("dependencies"))
            old(data.get("dependencies"))
        return "npm", found, skipped
    if name == "yarn.lock":
        for block in re.split(r"\n(?=\S)", text):
            head = block.split("\n", 1)[0]
            version = re.search(r'(?m)^\s+version:?\s+"?([^"\s]+)"?', block)
            names = re.findall(r'"?(@?[^@",\s]+)@', head)
            if not version or not names or head.startswith(("#", "__metadata")):
                continue
            resolution = re.search(r'(?m)^\s+resol(?:ved|ution):?\s+"?([^"\s]+)', block)
            target = resolution.group(1) if resolution else ""
            if re.search(r"@(workspace|patch|portal|link|file|git)", head + " " + target) or version.group(1).startswith("0.0.0-use.local"):
                skipped.append((names[0], "a workspace, patch or non-registry entry"))
            elif not private(names[0], target) and not (not target.startswith("http") and unlisted_private(names[0])):
                found.append((names[0], version.group(1)))
        return "npm", found, skipped
    if name == "pnpm-lock.yaml":
        in_packages = False
        for line in text.splitlines():
            if re.match(r"^(packages|snapshots):", line):
                in_packages = line.startswith("packages")
                continue
            if in_packages and re.match(r"^\S", line):
                in_packages = False
            m = in_packages and (re.match(r"^  '?/((?:@[^/\s]+/)?[^/\s@]+)/(\d[^:_('\s]*)", line) or re.match(r"^  '?/?(@?[^@'\s/][^@'\s]*)@([^:('\s]+)", line))
            if m:
                found.append((m.group(1), m.group(2)))
            elif in_packages and found and "tarball:" in line and private(found[-1][0], line):
                found.pop()
        found = [f for f in found if not unlisted_private(f[0])]
        return "npm", found, skipped
    if re.fullmatch(r"requirements.*\.txt", name) or name == "constraints.txt":
        for line in text.splitlines():
            line = line.split(" #", 1)[0].strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("-r", "-c", "--requirement", "--constraint")):
                skipped.append((line[:60], "another file is included here and was not followed: give it as well"))
                continue
            if line.startswith(("-e", "--editable", "git+", "http")) or " @ " in line:
                skipped.append((line[:60], "installed from a path or URL, not a registry release"))
                continue
            if line.startswith("-"):
                if re.search(r"index-url|find-links", line):
                    host = re.search(r"https?://(?:[^/@\s]*@)?([^/\s]+)", line)
                    if host and host.group(1) not in PUBLIC_HOSTS and not include_private:
                        raise ValueError(f"it takes packages from {host.group(1)}, and a requirements file does not say which pin comes from where, so private names may be "
                                         f"among them: nothing was sent. Pass --include-private only if the user agrees")
                    skipped.append((re.sub(r"//[^/@\s]+@", "//<hidden>@", line)[:60], "sets where packages come from: the pins below it may not be public packages"))
                continue
            m = re.match(r"([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*==\s*([^\s;\\]+)", line)
            if m:
                found.append((m.group(1), m.group(2)))
            else:
                skipped.append((line[:60], "not pinned with ==: the installed version is unknown"))
        return "PyPI", found, skipped
    if name in ("poetry.lock", "uv.lock", "Cargo.lock"):
        for pkg in toml_packages(text):
            source = pkg.get("source")
            if name == "Cargo.lock":
                if not source:
                    skipped.append((pkg.get("name"), "a local crate"))
                    continue
                if isinstance(source, str) and not source.startswith("registry+"):
                    skipped.append((pkg.get("name"), "installed from git or a path"))
                    continue
            if isinstance(source, dict) and (source.get("type") in ("git", "directory", "file", "url") or any(k in source for k in ("git", "path", "editable", "virtual", "directory"))):
                skipped.append((pkg.get("name"), "installed from git or a path"))
            elif private(pkg.get("name"), source if isinstance(source, str) else ((source or {}).get("registry") or (source or {}).get("url") or "")):
                pass
            elif pkg.get("name") and pkg.get("version"):
                found.append((pkg["name"], pkg["version"]))
        return ("crates.io" if name == "Cargo.lock" else "PyPI"), found, skipped
    if name == "Pipfile.lock":
        data = json.loads(text)
        indexes = {s.get("name"): s.get("url", "") for s in (data.get("_meta") or {}).get("sources", []) if isinstance(s, dict)}
        only = next(iter(indexes.values()), "") if len(indexes) == 1 else ""
        for group in ("default", "develop"):
            for pkg, entry in data.get(group, {}).items():
                if private(pkg, indexes.get(entry.get("index"), only)):
                    continue
                if str(entry.get("version", "")).startswith("=="):
                    found.append((pkg, entry["version"][2:]))
                else:
                    skipped.append((pkg, "no pinned version"))
        return "PyPI", found, skipped
    if name == "go.mod":
        replaced = set(re.findall(r"(?m)^\s*(?:replace\s+)?(\S+)(?:\s+v\S+)?\s+=>", text))
        for module, version in re.findall(r"(?m)^\s*(?:require\s+)?([\w.\-/~]+\.[\w.\-/~]+)\s+v(\S+)", text):
            if module in replaced:
                skipped.append((module, "replaced by a `replace` directive: the version built is not this one"))
            else:
                found.append((module, version))
        skipped.append(("the Go standard library and toolchain", "not in go.mod's require list: not checked"))
        if not re.search(r"(?m)^go\s+1\.(1[7-9]|[2-9]\d)", text):
            skipped.append(("indirect dependencies", "this go.mod predates Go 1.17 and does not list them all"))
        return "Go", sorted(set(found)), skipped
    if name == "go.sum":
        raise ValueError("go.sum lists every version in the module graph, including ones the build does not use; give go.mod instead")
    if name == "composer.lock":
        data = json.loads(text)
        for group in ("packages", "packages-dev"):
            for pkg in data.get(group, []):
                if (pkg.get("notification-url") or "https://packagist.org/downloads/").startswith("https://packagist.org/") or include_private:
                    found.append((pkg["name"], str(pkg["version"]).lstrip("v")))
                else:
                    skipped.append((pkg["name"], "not from packagist.org: not sent (pass --include-private only if the user agrees)"))
        return "Packagist", found, skipped
    raise ValueError(f"no reader for {name}: use a scanner for this ecosystem")


# ------------------------------------------------- what a lock file change brought in
# The same reader as ship-vuln-fix's fix_check.py `lockdiff`; test_vuln_scan.py checks the two copies agree.
def lock_kind(name):
    """The lock format a file name stands for, so that copies such as package-lock.before.json are still read."""
    lowered = name.lower()
    for marker, kind in (("package-lock", "package-lock.json"), ("shrinkwrap", "npm-shrinkwrap.json"), ("pnpm-lock", "pnpm-lock.yaml"), ("yarn", "yarn.lock"),
                         ("poetry", "poetry.lock"), ("uv.lock", "uv.lock"), ("cargo", "Cargo.lock"), ("requirements", "requirements.txt"), ("constraints", "constraints.txt")):
        if marker in lowered:
            return kind
    return name


def lock_entries(path, text):
    """name -> list of {version, script, resolved, integrity}. Install scripts are visible only in npm's lock format, version 2 and later."""
    name = lock_kind(os.path.basename(path))
    entries = {}

    def add(pkg, version, script=None, resolved="", integrity=""):
        entries.setdefault(pkg, []).append({"version": version or "?", "script": script, "resolved": resolved or "", "integrity": integrity or ""})
    if name in ("package-lock.json", "npm-shrinkwrap.json"):
        data = json.loads(text)
        if isinstance(data.get("packages"), dict):
            for key, e in data["packages"].items():
                if not key or e.get("link") or "node_modules/" not in key:
                    continue
                add(e.get("name") or key.split("node_modules/")[-1], e.get("version"), bool(e.get("hasInstallScript")), e.get("resolved"), e.get("integrity"))
            return entries, True

        def old(deps):
            for pkg, e in (deps or {}).items():
                add(pkg, e.get("version"), None, e.get("resolved"), e.get("integrity"))
                old(e.get("dependencies"))
        old(data.get("dependencies"))
        return entries, False
    if name == "yarn.lock":
        for block in re.split(r"\n(?=\S)", text):
            head = block.split("\n", 1)[0]
            version = re.search(r'(?m)^\s+version:?\s+"?([^"\s]+)"?', block)
            names = re.findall(r'"?(@?[^@",\s]+)@', head)
            resolved = re.search(r'(?m)^\s+resolved:?\s+"?([^"\s]+)', block)
            resolution = re.search(r'(?m)^\s+resolution:\s+"?([^"\n]+)"?', block)
            checksum = re.search(r'(?m)^\s+(?:integrity|checksum):?\s+"?([^"\s]+)', block)
            if version and names and not head.startswith(("#", "__metadata")):
                source = resolved.group(1) if resolved else ""
                if resolution and not re.search(r"@npm:", resolution.group(1)):
                    source = "non-registry:" + resolution.group(1).split("@")[-1].split(":")[0]
                add(names[0], version.group(1), None, source, checksum.group(1) if checksum else "")
        return entries, False
    if re.fullmatch(r"requirements.*\.txt", name) or name == "constraints.txt":
        for line in text.splitlines():
            stripped = line.strip()
            m = re.match(r"\s*([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*==\s*([^\s;\\#]+)", line)
            if m:
                add(re.sub(r"[-_.]+", "-", m.group(1)).lower(), m.group(2))
            elif re.match(r"(--index-url|--extra-index-url|--find-links|-i\b|-f\b)", stripped):
                add("(option) " + stripped.split()[0], re.sub(r"//[^/@\s]+@", "//<hidden>@", " ".join(stripped.split()[1:]))[:80], None, "non-registry:option")
            elif re.match(r"(-e\b|--editable|git\+|https?://)", stripped) or " @ " in stripped:
                add("(direct) " + re.sub(r"//[^/@\s]+@", "//<hidden>@", stripped)[:70], "url", None, "non-registry:url")
        return entries, False
    if name in ("poetry.lock", "uv.lock", "Cargo.lock"):
        for pkg in toml_packages(text):
            source = pkg.get("source")
            where = source if isinstance(source, str) else ((source or {}).get("url") or (source or {}).get("registry") or (source or {}).get("git") or "")
            if isinstance(source, dict) and (source.get("type") in ("git", "directory", "file", "url") or "git" in source or "path" in source):
                where = "non-registry:" + str(source.get("type") or "git-or-path")
            if isinstance(source, str) and not source.startswith("registry+"):
                where = "non-registry:" + source.split("+")[0]
            add(pkg.get("name", "?"), pkg.get("version"), None, where)
        return entries, False
    if name in ("go.mod", "composer.lock", "Pipfile.lock", "Gemfile.lock"):
        if name == "go.mod":
            for module, version in re.findall(r"(?m)^\s*(?:require\s+)?([\w.\-/~]+\.[\w.\-/~]+)\s+v(\S+)", text):
                add(module, version)
        elif name == "composer.lock":
            data = json.loads(text)
            for pkg in data.get("packages", []) + data.get("packages-dev", []):
                add(pkg["name"], str(pkg.get("version", "?")).lstrip("v"), None, (pkg.get("dist") or {}).get("url", ""), (pkg.get("dist") or {}).get("shasum", ""))
        elif name == "Pipfile.lock":
            data = json.loads(text)
            for group in ("default", "develop"):
                for pkg, e in data.get(group, {}).items():
                    add(re.sub(r"[-_.]+", "-", pkg).lower(), str(e.get("version", "?")).lstrip("="), None, "non-registry:git" if e.get("git") else "")
        else:
            for pkg, version in re.findall(r"(?m)^    ([A-Za-z0-9_.\-]+) \(([^)]+)\)\s*$", text):
                add(pkg, version)
        return entries, False
    if name == "pnpm-lock.yaml":
        records_builds = "requiresBuild" in text
        in_packages, current = False, None
        for line in text.splitlines():
            if re.match(r"^(packages|snapshots):", line):
                in_packages = line.startswith("packages")
                continue
            if in_packages and re.match(r"^\S", line):
                in_packages = False
            m = in_packages and (re.match(r"^  '?/((?:@[^/\s]+/)?[^/\s@]+)/(\d[^:_('\s]*)", line) or re.match(r"^  '?/?(@?[^@'\s/][^@'\s]*)@([^:('\s]+)", line))
            if m:
                add(m.group(1), m.group(2), False if records_builds else None)
                current = entries[m.group(1)][-1]
            elif in_packages and current is not None:
                if re.search(r"requiresBuild:\s*true", line):
                    current["script"] = True
                tarball = re.search(r"tarball:\s*([^,}\s]+)", line)
                if tarball:
                    current["resolved"] = tarball.group(1)
                checksum = re.search(r"integrity:\s*([^,}\s]+)", line)
                if checksum:
                    current["integrity"] = checksum.group(1)
        return entries, records_builds   # pnpm 9 and later no longer record which packages build on install
    raise ValueError(f"no reader for {name}")


def host(resolved):
    if (resolved or "").startswith("non-registry:"):
        return resolved
    m = re.match(r"[a-z+]+://(?:[^/@]*@)?([^/]+)/", resolved or "")
    if m:
        return m.group(1)
    return "non-registry:" + resolved.split(":", 1)[0] if re.match(r"(git|file|github|link)[+:]", resolved or "") else ""


def breaking(before, after):
    """True when the first non-zero component changed: 1.x to 2.x, or 0.3.x to 0.4.x."""
    def lead(version):
        parts = [int(x) for x in re.findall(r"\d+", version or "")[:3]]
        for index, part in enumerate(parts):
            if part:
                return (index, part)
        return None
    a = lead(after)
    return a is not None and all(lead(v) != a for v in before)


def lockdiff(old_label, old_text, new_label, new_text, path):
    try:
        old, old_sees = lock_entries(path, old_text)
        new, sees_scripts = lock_entries(path, new_text)
        sees_scripts = sees_scripts and old_sees
    except (ValueError, json.JSONDecodeError, ImportError, TypeError, AttributeError, KeyError) as e:
        fail(NOT_A_RESULT, f"{path}: could not be read as a lock file ({e}). The change was NOT CHECKED: read the diff yourself before installing.")
    if (not old and old_text.strip()) or (not new and new_text.strip()):
        fail(NOT_A_RESULT, f"{path}: no entries could be read from {'the old' if not old else 'the new'} version. The change was NOT CHECKED: read the diff yourself before installing.")
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed, attention, notes = [], [], []
    for name in sorted(set(new) & set(old)):
        before, after = sorted({e["version"] for e in old[name]}), sorted({e["version"] for e in new[name]})
        had_script, has_script = any(e["script"] for e in old[name]), any(e["script"] for e in new[name])
        if before != after:
            changed.append((name, before, after))
            if any(breaking(before, a) for a in after):
                attention.append(f"{name}: BREAKING-RANGE version change ({', '.join(before)} -> {', '.join(after)}): the first non-zero part of the version moved. Read its changelog")
            if sees_scripts and has_script and had_script:
                notes.append(f"{name}: has an install script (it had one before too). Its new version's script is new code, and a script-free install leaves the package unbuilt")
        else:
            for o in old[name]:
                for n in new[name]:
                    if o["version"] == n["version"] and ((o["integrity"] and n["integrity"] and o["integrity"] != n["integrity"]) or (o["resolved"] and n["resolved"] and o["resolved"] != n["resolved"])):
                        attention.append(f"{name} {n['version']}: SAME VERSION, DIFFERENT CONTENT OR SOURCE (the download address or checksum changed without a version change)")
        if sees_scripts and has_script and not had_script:
            attention.append(f"{name}: GAINED AN INSTALL SCRIPT in {', '.join(after)}: installing normally would run its code. Find out what the script does before anything installs it")
        old_hosts, new_hosts = {host(e["resolved"]) for e in old[name]} - {""}, {host(e["resolved"]) for e in new[name]} - {""}
        if new_hosts - old_hosts and (old_hosts or any(h.startswith("non-registry:") for h in new_hosts)):
            attention.append(f"{name}: now comes from {', '.join(sorted(new_hosts - old_hosts))}" + (f" (was {', '.join(sorted(old_hosts))})" if old_hosts else ""))
    known_hosts = {host(e["resolved"]) for entries in old.values() for e in entries} - {""}
    plain_added = []
    for name in added:
        versions = ", ".join(sorted({e["version"] for e in new[name]}))
        flags = []
        if sees_scripts and any(e["script"] for e in new[name]):
            flags.append("HAS AN INSTALL SCRIPT")
        hosts = {host(e["resolved"]) for e in new[name]} - {""}
        odd = {h for h in hosts if h.startswith("non-registry:")} | ((hosts - known_hosts) if known_hosts else set())
        if odd:
            flags.append("comes from a source nothing else here uses: " + ", ".join(sorted(odd)))
        for e in new[name]:
            tail = (e["resolved"] or "").rsplit("/", 1)[-1]
            if e["resolved"].startswith("http") and name.split("/")[-1] not in e["resolved"]:
                flags.append(f"its download address does not name the package ({tail[:40]})")
        if flags:
            attention.append(f"{name} {versions}: NEW PACKAGE; " + "; ".join(flags))
        else:
            plain_added.append(f"{name} {versions}")
    print(f"Lock file change: {path}  ({old_label} -> {new_label})")
    print(f"Changed versions: {len(changed)}")
    for name, before, after in changed:
        print(f"  - {name}: {', '.join(before)} -> {', '.join(after)}")
    sees_sources = bool(known_hosts)
    said = "nothing flagged" + ("" if sees_scripts and sees_sources else "; this lock format does not show " + " or ".join(
        w for w, seen in (("install scripts", sees_scripts), ("where a package comes from", sees_sources)) if not seen) + ", so that was not checked")
    print(f"Added packages: {len(added)}" + ("  (" + ", ".join(plain_added) + f": new, {said}; name them in your report)" if plain_added else ""))
    print(f"Removed packages: {len(removed)}" + ("  " + ", ".join(removed) if removed else ""))
    print(f"\nSTOP AND LOOK before installing: {len(attention)}")
    for line in attention:
        print(f"  ! {line}")
    for line in notes:
        print(f"  note: {line}")
    if not sees_scripts:
        print("\nThis lock format does not record install scripts, so none can be flagged here: check each changed and added package's metadata instead, and say that you did or could not.")
    else:
        print("\nThe install-script flag is copied from the registry by whoever wrote the lock file; it is a hint. Installing with scripts off is the guard.")
    if not changed and not added and not removed and not attention:
        print("\nNothing changed in the lock file. If a fix was expected, it has not happened.")
    return FLAGGED if attention else 0


# ----------------------------------------------------------------- network
def http_json(url, payload=None, timeout=30):
    request = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                                     headers={"Content-Type": "application/json", "User-Agent": "ship-vuln-scan"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def osv(paths, out_path, dry_run, fetch=http_json, include_private=False):
    results, total, total_skipped, counts, sources = [], 0, [], [], []
    for path in paths:
        try:
            ecosystem, packages, skipped = packages_from(path, include_private)
        except (ValueError, json.JSONDecodeError, OSError, KeyError, TypeError, AttributeError) as e:
            fail(NOT_A_RESULT, f"{path}: could not be read as a lock file ({e}). NOT CHECKED.")
        packages = sorted(set(packages))
        if not packages:
            fail(NOT_A_RESULT, f"{path}: read 0 packages from it ({len(skipped)} entries set aside). Either the format is one this script does not read, or nothing in it "
                               f"can be looked up. NOT CHECKED: this is not a clean result.")
        total += len(packages)
        counts.append(f"{os.path.basename(path)}: {len(packages)} packages")
        sources.append(f"{os.path.abspath(path)} ({len(packages)} package versions looked up)")
        total_skipped += [(path, what, why) for what, why in skipped]
        if dry_run:
            print(f"{path}: would send {len(packages)} {ecosystem} package names and versions to {OSV_API}; {len(skipped)} entries would not be sent")
            for what, why in skipped[:40]:
                print(f"  not sent: {what} ({why})")
            if "--names" in sys.argv:
                print("  would send: " + ", ".join(f"{n}@{v}" for n, v in packages))
            continue
        hits = {}
        try:
            for start in range(0, len(packages), 500):
                chunk = packages[start:start + 500]
                reply = fetch(f"{OSV_API}/v1/querybatch", {"queries": [{"package": {"name": n, "ecosystem": ecosystem}, "version": v} for n, v in chunk]})
                answers = reply.get("results", [])
                if len(answers) != len(chunk):
                    fail(NO_NETWORK, f"{OSV_API} answered {len(answers)} of {len(chunk)} queries. NOT CHECKED: do not report this as a result.")
                for (n, v), answer in zip(chunk, answers):
                    if answer.get("next_page_token"):
                        total_skipped.append((path, f"{n} {v}", "more advisories than one reply holds; the list for this package is incomplete"))
                    for vuln in answer.get("vulns", []):
                        hits.setdefault((n, v), []).append(vuln["id"])
            details = {}
            for vid in sorted({i for ids in hits.values() for i in ids}):
                details[vid] = fetch(f"{OSV_API}/v1/vulns/{vid}")
        except (urllib.error.URLError, OSError, ValueError) as e:
            fail(NO_NETWORK, f"Could not reach {OSV_API} ({e}). NOT CHECKED: no advisory data was obtained, so nothing can be said about these packages.")
        out_packages = []
        for (n, v), ids in sorted(hits.items()):
            vulns = [details[i] for i in ids]
            out_packages.append({"package": {"name": n, "version": v, "ecosystem": ecosystem}, "vulnerabilities": vulns,
                                 "groups": [{"ids": [d["id"]], "aliases": [d["id"]] + d.get("aliases", []), "max_severity": ""} for d in vulns]})
        if out_packages:
            results.append({"source": {"path": os.path.abspath(path), "type": "lockfile"}, "packages": out_packages})
    if dry_run:
        return 0
    result = {"results": results, "ship_vuln_scan": {"queried": total, "api": OSV_API, "sources": sources}}
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
    print(f"Asked {OSV_API} about {total} package versions ({'; '.join(counts)}). Those names and versions were sent to that service.")
    if "SHIP_VULN_OSV_API" in os.environ:
        print(f"NOTE: the advisory service was set by the SHIP_VULN_OSV_API environment variable to {OSV_API}, not the public api.osv.dev. Say so in the answer.")
    if total_skipped:
        print(f"NOT CHECKED, {len(total_skipped)} entr{'y' if len(total_skipped) == 1 else 'ies'}:")
        for path, what, why in total_skipped[:40]:
            print(f"  - {what} ({os.path.basename(path)}): {why}")
        if len(total_skipped) > 40:
            print(f"  ... and {len(total_skipped) - 40} more")
    print("This is a version match against a lock file: it does not see what is installed, vendored or built into an image. A package the service has "
          "never heard of (a private or misspelt name) comes back with no advisories, like a safe one.\n")
    _, findings, scanned = parse_result(result)
    print_summary(re.sub(r"^https?://", "", OSV_API) + " (through this script)", merged(findings), scanned)
    return 0


def exploited(ids, fetch=http_json, groups=None):
    """groups: [(label, [ids])] when the ids come from a result, so each advisory is looked up through its CVE alias."""
    groups = groups or [(i, [i]) for i in ids]
    wanted = {}
    without = []
    for label, names in groups:
        cves = sorted({n.upper() for n in names if n.upper().startswith("CVE-")})
        if cves:
            wanted[label] = cves
        else:
            without.append(label)
    resolved = []
    for label in list(without):
        names = next(n for l, n in groups if l == label)
        for name in names:
            if not re.match(r"(?i)(GHSA|PYSEC|RUSTSEC|GO|OSV)-", name):
                continue
            try:
                aliases = fetch(f"{OSV_API}/v1/vulns/{name}").get("aliases", [])
            except (urllib.error.URLError, OSError, ValueError, AttributeError):
                continue
            found_cves = sorted({a.upper() for a in aliases if a.upper().startswith("CVE-")})
            if found_cves:
                wanted[label] = found_cves
                without.remove(label)
                resolved.append(f"{name} -> {', '.join(found_cves)}")
                break
    if resolved:
        print(f"CVE ids looked up at {OSV_API} for advisories the result gave without one: " + "; ".join(resolved))
    cves = sorted({c for v in wanted.values() for c in v})
    if not cves:
        fail(NOT_A_RESULT, "No CVE ids to look up. The exploited list and EPSS are keyed by CVE id: an advisory with no CVE alias cannot be looked up, which is not the same as 'not exploited'.")
    kev, kev_error, kev_url = None, None, None
    for url in KEV_URLS:
        try:
            kev = fetch(url)
            if not isinstance(kev.get("vulnerabilities"), list) or len(kev["vulnerabilities"]) < 100:
                kev, kev_error = None, "the list came back implausibly short"
                continue
            kev_url = url
            break
        except (urllib.error.URLError, OSError, ValueError, AttributeError) as e:
            kev_error = e
    scores, epss_error = {}, None
    try:
        for start in range(0, len(cves), 80):
            reply = fetch(f"{EPSS_API}?cve={','.join(cves[start:start + 80])}")
            for row in reply.get("data", []):
                scores[row["cve"]] = (row.get("epss"), row.get("percentile"), row.get("date"))
    except (urllib.error.URLError, OSError, ValueError, KeyError, AttributeError) as e:
        epss_error = e
    if kev is None and epss_error is not None:
        fail(NO_NETWORK, f"Could not fetch the exploited list ({kev_error}) or EPSS ({epss_error}). NOT CHECKED: say that exploitation data was unavailable; do not guess it.")
    listed = {v["cveID"]: v for v in kev["vulnerabilities"]} if kev else {}
    if kev:
        print(f"CISA Known Exploited Vulnerabilities catalogue {kev.get('catalogVersion', '?')} (released {kev.get('dateReleased', '?')}), from {kev_url}")
    else:
        print(f"Exploited list NOT CHECKED: could not be fetched ({kev_error}). Do not say anything about known exploitation.")
    if epss_error is not None:
        print(f"EPSS NOT CHECKED: could not be fetched ({epss_error}).")
    else:
        print(f"EPSS from {EPSS_API}")
    for label, mine in wanted.items():
        parts = []
        if kev:
            hit = [listed[c] for c in mine if c in listed]
            parts.append(f"KNOWN EXPLOITED (added {hit[0].get('dateAdded')}; ransomware use: {hit[0].get('knownRansomwareCampaignUse', '?')})" if hit else "not in the exploited list")
        if epss_error is None:
            got = [scores[c] for c in mine if c in scores and scores[c][0] is not None]
            best = max(got, key=lambda x: float(x[0])) if got else None
            parts.append(f"EPSS {float(best[0]):.3f} (percentile {float(best[1]):.2f}, {best[2]})" if best else "no EPSS score returned (the id may be unknown to EPSS)")
        shown = label if label in mine else f"{label} via {', '.join(mine)}"
        print(f"- {shown}: " + "; ".join(parts))
    if without:
        print("No CVE alias, so not looked up (this is not 'unexploited'): " + ", ".join(without))
    print("Absence from the exploited list means only that CISA has not listed it. EPSS is a probability of exploitation somewhere in the next 30 days, not a statement about this code.")
    return 0


def secrets(path):
    """Where each hit in a secret scanner's report is. Never the value."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError as e:
        fail(NOT_A_RESULT, f"{path}: cannot be read ({e.strerror}). NOT CHECKED.")
    hits = None
    try:
        data = json.loads(raw) if raw.strip() else None
        if isinstance(data, list):
            hits = data
    except json.JSONDecodeError:
        lines = [l for l in raw.splitlines() if l.strip().startswith("{")]
        try:
            hits = [json.loads(l) for l in lines] if lines else None
        except json.JSONDecodeError:
            hits = None
    if hits is None or not all(isinstance(h, dict) for h in hits):
        fail(NOT_A_RESULT, f"{path}: not a gitleaks report (a JSON array) or trufflehog output (one JSON object per line). NOT CHECKED. Do not open it to look: it may hold secrets in clear text.")
    hits = [h for h in hits if "RuleID" in h or "DetectorName" in h or "SourceMetadata" in h]
    clear = 0
    print(f"Secret scanner report: {len(hits)} hit(s)")
    for h in hits:
        if "RuleID" in h:
            value = str(h.get("Secret") or "")
            clear += bool(value) and value != "REDACTED"
            # the name the value is assigned to says what the credential is for; it is not the secret
            named = re.match(r"\s*(?:export\s+)?[\"']?([A-Za-z_][A-Za-z0-9_.\-]{2,60})[\"']?\s*[=:]", str(h.get("Match") or ""))
            name = f"  assigned to {named.group(1)}" if named and named.group(1) not in value and named.group(1) != "REDACTED" else ""
            print(f"- {h.get('File', '?')}:{h.get('StartLine', '?')}  rule {h.get('RuleID')}{name}  commit {str(h.get('Commit') or 'working tree')[:12]}  {h.get('Author', '')} {str(h.get('Date', ''))[:10]}".rstrip())
        else:
            meta = h.get("SourceMetadata", {}).get("Data", {})
            where = next(iter(meta.values()), {}) if isinstance(meta, dict) and meta else {}
            clear += bool(h.get("Raw"))
            print(f"- {where.get('file', '?')}:{where.get('line', '?')}  detector {h.get('DetectorName', '?')}  commit {str(where.get('commit') or 'working tree')[:12]}  verified by the scanner: {h.get('Verified', False)}")
    if clear:
        print(f"\nThe report itself holds {clear} secret value(s) in clear text. Treat the file (and any CI log or artefact it came from) as secret; do not open, quote or keep it.")
    if not hits:
        print("No hits in this report. That covers what the scanner was pointed at, with its ignore file and allowlist in effect.")
    print("Every hit that is a real credential must be rotated: removing the line leaves it in history. Nothing here says whether a credential is live; do not test one.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inventory"); p.add_argument("dir", nargs="?", default="."); p.add_argument("--json", action="store_true")
    p = sub.add_parser("summarise"); p.add_argument("result"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare"); p.add_argument("base"); p.add_argument("head")
    p = sub.add_parser("osv"); p.add_argument("lockfiles", nargs="+"); p.add_argument("--out"); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--names", action="store_true"); p.add_argument("--include-private", action="store_true")
    p = sub.add_parser("secrets"); p.add_argument("report")
    p = sub.add_parser("lockdiff"); p.add_argument("old"); p.add_argument("new")
    p = sub.add_parser("exploited"); p.add_argument("ids", nargs="*"); p.add_argument("--from", dest="from_result")
    args = parser.parse_args(argv)
    if args.command == "inventory":
        if not os.path.isdir(args.dir):
            fail(NOT_A_RESULT, f"{args.dir}: not a directory")
        inv = inventory(args.dir)
        print(json.dumps(inv, indent=1)) if args.json else print_inventory(inv)
        return 0
    if args.command == "summarise":
        tool, findings, scanned = load_result(args.result)
        rows = merged(findings)
        print(json.dumps({"tool": tool, "scanned": scanned, "advisories": rows}, indent=1)) if args.json else print_summary(tool, rows, scanned)
        return 0
    if args.command == "compare":
        return compare(args.base, args.head)
    if args.command == "osv":
        return osv(args.lockfiles, args.out, args.dry_run, include_private=args.include_private)
    if args.command == "secrets":
        return secrets(args.report)
    if args.command == "lockdiff":
        for path in (args.old, args.new):
            if not os.path.isfile(path):
                fail(NOT_A_RESULT, f"{path}: no such file. NOT CHECKED.")
        texts = [read_text(path, 50_000_000) for path in (args.old, args.new)]
        if not all(t.strip() for t in texts):
            fail(NOT_A_RESULT, "One of the two files is empty, unreadable or a symbolic link. NOT CHECKED.")
        return lockdiff(args.old, texts[0], args.new, texts[1], args.new)
    if args.command == "exploited":
        if args.from_result:
            _, findings, _ = load_result(args.from_result)
            groups = [(f"{r['package']} {r['id']}", [r["id"]] + r["aliases"]) for r in merged(findings)]
            return exploited([], groups=groups + [(i, [i]) for i in args.ids])
        return exploited(list(args.ids))
    return 1


if __name__ == "__main__":
    sys.exit(main())
