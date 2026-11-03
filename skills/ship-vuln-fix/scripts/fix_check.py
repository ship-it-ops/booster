#!/usr/bin/env python3
"""Mechanics for ship-vuln-fix: is the tree safe to edit, what did a lock file change bring in, and is it closed.

    fix_check.py preflight [DIR]
    fix_check.py lockdiff OLD NEW
    fix_check.py lockdiff --git PATH [--rev REV]
    fix_check.py closure BEFORE.json AFTER.json [--ids ID...] [--lock LOCKFILE]

`preflight` says which manifests and lock files have uncommitted changes or are not
tracked by git (those are not edited as they are), which package manager the project
uses, which packages already have install scripts, and whether its configuration changes
where packages come from, whether install scripts run, or what an audit hides. `lockdiff`
compares two versions of a lock file, or the working copy with a commit, and flags what a
dependency change brought in besides the version: a gained install script, another source,
the same version with different content, a breaking-range version; it exits non-zero when
anything is flagged. `closure` compares the same scanner's JSON output from before and
after a fix; it refuses anything that is not a scan result or that comes from another
tool, so an error is never read as "fixed", and it exits non-zero unless every targeted
advisory is gone, shown to have been looked at again (with `--lock`, by the lock file
resolving a fixed version), and no new one appeared.

Standard library only. Nothing here installs, builds, resolves or edits anything.
"""
import argparse
import json
import os
import re
import subprocess
import sys

NOT_A_RESULT = 2
NOT_CLOSED = 1
LABEL_RANK = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "MEDIUM": 2, "LOW": 1}
MANIFEST_NAMES = ("package.json", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "pyproject.toml", "poetry.lock", "uv.lock",
                  "Pipfile", "Pipfile.lock", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock", "composer.json", "composer.lock", "Gemfile", "Gemfile.lock",
                  "pom.xml", "build.gradle", "build.gradle.kts", "gradle.lockfile")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".terraform", "dist", "build"}


def fail(code, message):
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(code)


def read_text(path, limit=50_000_000):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


# The readers below are the same as in ship-vuln-scan's script; the two plugins install separately, so each carries its own copy.
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



# ------------------------------------------------------------------ preflight
def git(directory, *args):
    try:
        done = subprocess.run(["git", "-C", directory] + list(args), capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)
    return done.returncode, done.stdout


def is_manifest(name):
    return name in MANIFEST_NAMES or re.fullmatch(r"requirements.*\.(txt|in)", name) or name == "constraints.txt"


def host_only(line):
    """The key and the host of a configuration line that names a URL. Never the line: it can carry a token."""
    key = re.split(r"[=:\s]", line.strip(), maxsplit=1)[0][:40]
    m = re.search(r"[a-z][a-z0-9+.-]*://(?:[^/@\s]*@)?([^/:\s\"']+)", line)
    return f"{key} -> {m.group(1)}" if m else key


def preflight(directory):
    directory = os.path.realpath(directory)
    code, top = git(directory, "rev-parse", "--show-toplevel")
    print(f"Directory: {directory}")
    dirty, tracked, in_git = {}, set(), code == 0
    if not in_git:
        print("Git: NOT a git repository. There is no way to see or undo a change here: copy any file before editing it, and say so.")
    else:
        top = os.path.realpath(top.strip())
        _, branch = git(directory, "rev-parse", "--abbrev-ref", "HEAD")
        _, status = git(directory, "status", "--porcelain", "--untracked-files=all")
        for line in status.splitlines():
            state, path = line[:2], line[3:].split(" -> ")[-1].strip('"')
            dirty[os.path.realpath(os.path.join(top, path))] = state
        _, listed = git(directory, "ls-files", "-z")
        tracked = {os.path.realpath(os.path.join(directory, p)) for p in listed.split("\0") if p}
        print(f"Git: branch {branch.strip() or '?'}; {len(dirty)} path(s) with uncommitted changes or untracked")
    found = []
    for base, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        found += [os.path.join(base, n) for n in sorted(files) if is_manifest(n)]
    print("\nManifests and lock files:")
    if not found:
        print("  none found")
    blocked, clean = [], 0
    for path in found:
        real = os.path.realpath(path)
        state = dirty.get(real)
        rel = os.path.relpath(path, directory)
        if state is None and (not in_git or real in tracked):
            clean += 1
            print(f"  {rel}: " + ("no uncommitted changes" if in_git else "not under git"))
        elif state is None or state.strip() == "??":
            print(f"  {rel}: NOT TRACKED BY GIT (untracked or ignored): git cannot show or undo a change to it. Copy it to the scratch directory before changing it, and compare with `lockdiff OLD NEW`")
            blocked.append(rel)
        else:
            print(f"  {rel}: HAS UNCOMMITTED CHANGES (the user's work: do not edit it, and do not stash or reset it)")
            blocked.append(rel)
    inside = [p for p in dirty if os.path.commonpath([directory, p]) == directory]
    others = sorted(os.path.relpath(p, directory) for p in inside if not is_manifest(os.path.basename(p)))
    if others:
        print(f"\nOther uncommitted or untracked paths ({len(others)}), which a dependency fix has no reason to touch: " + ", ".join(others[:15]) + (" ..." if len(others) > 15 else ""))
    print("\nPackage manager and its configuration:")
    names = {os.path.basename(p) for p in found}
    managers = [label for lock, label in (("package-lock.json", "npm"), ("npm-shrinkwrap.json", "npm"), ("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("poetry.lock", "poetry"),
                                          ("uv.lock", "uv"), ("Pipfile.lock", "pipenv"), ("go.mod", "go"), ("Cargo.lock", "cargo"), ("composer.lock", "composer"), ("Gemfile.lock", "bundler")) if lock in names]
    if any(re.fullmatch(r"requirements.*\.txt", n) for n in names) and not {"poetry", "uv", "pipenv"} & set(managers):
        managers.append("pip (requirements files)")
    print("  In use, from the lock files found: " + (", ".join(dict.fromkeys(managers)) or "could not tell"))
    pkg = os.path.join(directory, "package.json")
    if os.path.isfile(pkg):
        try:
            data = json.loads(read_text(pkg))
        except json.JSONDecodeError:
            data = {}
        if data.get("packageManager"):
            print(f"  package.json pins the package manager: {data['packageManager']}")
        if data.get("workspaces"):
            print("  workspaces: " + json.dumps(data["workspaces"]) + " (one lock file at the root; run commands from there)")
        for field in ("overrides", "resolutions"):
            if data.get(field):
                print(f"  package.json has {field}: {json.dumps(data[field])}  (an existing pin may be what holds a package at a vulnerable version)")
        if isinstance(data.get("pnpm"), dict) and data["pnpm"].get("overrides"):
            print(f"  package.json has pnpm.overrides: {json.dumps(data['pnpm']['overrides'])}")
        hidden = (data.get("pnpm") or {}).get("auditConfig") if isinstance(data.get("pnpm"), dict) else None
        if hidden or data.get("auditConfig"):
            print(f"  package.json tells the audit to ignore advisories: {json.dumps(hidden or data.get('auditConfig'))}  (no command-line flag switches this off: these stay hidden in both scans; name them)")
    lock = os.path.join(directory, "package-lock.json")
    if os.path.isfile(lock):
        try:
            entries, sees = lock_entries(lock, read_text(lock))
            scripted = sorted(n for n, es in entries.items() if any(e["script"] for e in es))
            if sees:
                print("  Packages in the lock file that already have an install script: " + (", ".join(scripted[:20]) or "none") +
                      (". A script-free reinstall leaves these unbuilt: do not wipe node_modules to verify." if scripted else ""))
        except (ValueError, json.JSONDecodeError, TypeError, AttributeError):
            print("  package-lock.json could not be read")
    for name in (".npmrc", ".yarnrc.yml", ".yarnrc", ".pnpmfile.cjs", "pip.conf", ".pip/pip.conf", "poetry.toml", "uv.toml", ".cargo/config.toml"):
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            notes = ["code that runs on every pnpm command"] if name == ".pnpmfile.cjs" else []
            for line in read_text(path, 100_000).splitlines():
                s = line.strip()
                if not s or s.startswith(("#", ";")):
                    continue
                if re.search(r"registry|index-url|extra-index-url|npmRegistryServer|\[\[tool\.uv\.index|\[registries|\[source", s, re.I) and "://" in s:
                    notes.append("sets where packages come from: " + host_only(s))
                elif re.search(r"ignore-scripts|enableScripts|script-shell|unsafe-perm", s, re.I):
                    notes.append("changes whether install scripts run: " + s.split("//")[0][:60])
                elif re.match(r"(yarnPath|plugins)\b", s):
                    notes.append(s.split(":")[0] + ": code from the repository that every yarn command runs")
                elif re.search(r"minimum-?release-?age|npmMinimalAgeGate|exclude-newer", s, re.I):
                    notes.append("sets a minimum release age (keep to it): " + s[:60])
                elif re.search(r"npmAuditIgnoreAdvisories|npmAuditExcludePackages|audit-level|^omit\b", s):
                    notes.append("narrows the audit, and stays in force for both scans: " + s[:60])
            state = dirty.get(os.path.realpath(path))
            print(f"  {name}: " + ("; ".join(dict.fromkeys(notes)) if notes else "present, nothing about registries or scripts") + ("  [HAS UNCOMMITTED CHANGES: say so before running the package manager]" if state else ""))
    print("\nResult: " + ("these files must not be edited as they are: " + ", ".join(blocked) + ". Do not run a package-manager command that could rewrite them. Fix through files with no uncommitted changes, or stop and give the user the plan."
                         if blocked else f"{clean} manifest and lock file(s), none with uncommitted changes."))
    return 0


# ------------------------------------------------------------------- lockdiff
def lock_kind(name):
    """The lock format a file name stands for, so that copies such as package-lock.before.json are still read."""
    lowered = name.lower()
    for marker, kind in (("package-lock", "package-lock.json"), ("shrinkwrap", "npm-shrinkwrap.json"), ("pnpm-lock", "pnpm-lock.yaml"), ("yarn", "yarn.lock"),
                         ("poetry", "poetry.lock"), ("uv.lock", "uv.lock"), ("cargo", "Cargo.lock"), ("requirements", "requirements.txt"), ("constraints", "constraints.txt")):
        if marker in lowered:
            return kind
    return name


def toml_packages(text):
    try:
        import tomllib
        return tomllib.loads(text).get("package", [])
    except ImportError:
        packages = []
        for block in re.split(r"(?m)^\[\[package\]\]\s*$", text)[1:]:
            fields = dict(re.findall(r'(?m)^(name|version|source)\s*=\s*"([^"]*)"', re.split(r"(?m)^\[", block)[0]))
            src = re.search(r"(?ms)^\[package\.source\]\s*$(.*?)(?=^\[|\Z)", block)
            if src:
                fields["source"] = dict(re.findall(r'(?m)^(\w+)\s*=\s*"([^"]*)"', src.group(1)))
            packages.append(fields)
        return packages


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
    return NOT_CLOSED if attention else 0


# -------------------------------------------------------------------- closure
def lock_versions(path, package):
    """The versions the lock file resolves for a package: a list (empty when the package is not in it), or None when the file cannot be read as a lock file."""
    try:
        entries, _ = lock_entries(path, read_text(path))
    except (ValueError, json.JSONDecodeError, ImportError, TypeError, AttributeError, KeyError):
        return None
    if not entries:
        return None
    kind = lock_kind(os.path.basename(path))
    key = re.sub(r"[-_.]+", "-", package).lower() if kind.startswith(("requirements", "constraints", "poetry", "uv", "Pipfile")) else package
    return sorted({e["version"] for e in entries.get(key, [])})


def version_tuple(version):
    return tuple(int(x) for x in re.findall(r"\d+", version or "")[:4])


def lock_verdict(lock, row):
    """(proves the fix, what to say). The lock file proves a fix when every version it resolves is at or above a version the advisory names as fixed."""
    versions = lock_versions(lock, row["package"])
    name = os.path.basename(lock)
    if versions is None:
        return False, f"{name} could not be read as a lock file, so it proves nothing"
    if not versions:
        return False, f"{name} does not list {row['package']}: either the package was removed, or this is not the lock file the scan read. Say which"
    if row["version"] in versions:
        return False, f"{name} still resolves {row['package']} at {', '.join(versions)}"
    fixes = [version_tuple(v) for v in str(row["fixed"] or "").split(",") if v.strip()[:1].isdigit()]
    if not fixes:
        return False, f"{name} now resolves {', '.join(versions)}, but the first result names no fixed version to compare it with"
    below = [v for v in versions if not any(version_tuple(v) >= f and version_tuple(v)[:1] == f[:1] for f in fixes) and version_tuple(v) < max(fixes)]
    if below:
        return False, f"{name} now resolves {', '.join(below)}, which is below the fixed version ({row['fixed']})"
    return True, f"the lock file now resolves {', '.join(versions)}"


def closure(before_path, after_path, ids, lock=None):
    before_tool, before, before_scanned = load_result(before_path)
    after_tool, after, after_scanned = load_result(after_path)
    if before_tool != after_tool:
        fail(NOT_A_RESULT, f"The two results come from different tools ({before_tool}, then {after_tool}). That is not the same scan run again: NOT COMPARABLE.")
    if lock and not os.path.isfile(lock):
        fail(NOT_A_RESULT, f"{lock}: no such file. NOT CHECKED.")
    before_rows, after_rows = merged(before), merged(after)

    def names(row):
        return set([row["id"]] + row["aliases"])
    wanted = {i.upper() for i in ids}
    targets = [r for r in before_rows if not wanted or {n.upper() for n in names(r)} & wanted]
    missing = sorted(i for i in wanted if not any(i in {n.upper() for n in names(r)} for r in before_rows))
    still, gone = [], []
    for row in targets:
        (still if any(a["package"] == row["package"] and names(a) & names(row) for a in after_rows) else gone).append(row)
    new = [a for a in after_rows if not any(b["package"] == a["package"] and names(b) & names(a) for b in before_rows)]
    print(f"Closure check ({os.path.basename(before_path)} -> {os.path.basename(after_path)}), both from {after_tool}")
    print("Sources in the first result: " + ("; ".join(str(s) for s in before_scanned[:6]) or "none listed"))
    print("Sources in the second result: " + ("; ".join(str(s) for s in after_scanned[:6]) or "none listed"))
    unproven, notes = [], {}
    whole_run = ("npm audit", "pnpm audit", "pip-audit")   # these read everything they were pointed at, or fail
    not_audited = " ".join(str(s) for s in after_scanned if str(s).startswith("NOT AUDITED"))
    for row in gone:
        if lock:
            ok, said = lock_verdict(lock, row)
            notes[id(row)] = said
            if not ok:
                unproven.append((row, said))
            continue
        listed = any(src and src in str(s) for s in after_scanned for src in row["sources"]) or any(set(row["sources"]) & set(a["sources"]) for a in after_rows)
        if re.search(r"\b%s \(" % re.escape(row["package"] or "?"), not_audited):
            unproven.append((row, "the second run skipped this package, so it was not audited"))
        elif not (after_tool in whole_run or listed):
            unproven.append((row, "the second result does not show that its source was read again"))
    proven = [r for r in gone if r not in [u[0] for u in unproven]]
    print(f"No longer reported: {len(proven)}")
    for r in proven:
        print(f"  - {r['package']} {r['version']}  {r['id']}" + (f"  ({notes[id(r)]})" if id(r) in notes else ""))
    print(f"GONE FROM THE OUTPUT BUT NOT SHOWN TO BE RESCANNED: {len(unproven)}")
    for r, why in unproven:
        print(f"  - {r['package']} {r['version']}  {r['id']}: {why}")
    print(f"STILL REPORTED: {len(still)}")
    for r in still:
        now = next(a for a in after_rows if a["package"] == r["package"] and names(a) & names(r))
        print(f"  - {r['package']} {now['version']}  {r['id']}  (fixed in: {now['fixed'] or '?'})")
    print(f"NEW since the first scan: {len(new)}")
    for r in new:
        print(f"  - {r['package']} {r['version']}  {r['id']}  (fixed in: {r['fixed'] or '?'})")
    if missing:
        print("NOT IN THE FIRST SCAN, so nothing can be said about them: " + ", ".join(missing))
    if unproven:
        print("\nAn advisory that vanishes from a scanner's output looks the same whether it was fixed or its file was not read. `--lock <the lock file the scan read>` "
              "checks the resolved version against the fixed version the first result names; without that proof the fix is 'changed, not confirmed'.")
    print("\nThis compares two outputs. It means what it says only if both came from the same scanner command with the same ignore configuration, and the second ran after the change.")
    return 0 if not still and not new and not missing and not unproven else NOT_CLOSED


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preflight"); p.add_argument("dir", nargs="?", default=".")
    p = sub.add_parser("lockdiff"); p.add_argument("paths", nargs="+"); p.add_argument("--git", action="store_true"); p.add_argument("--rev", default="HEAD")
    p = sub.add_parser("closure"); p.add_argument("before"); p.add_argument("after"); p.add_argument("--ids", nargs="*", default=[]); p.add_argument("--lock")
    args = parser.parse_args(argv)
    if args.command == "preflight":
        if not os.path.isdir(args.dir):
            fail(NOT_A_RESULT, f"{args.dir}: not a directory")
        return preflight(args.dir)
    if args.command == "lockdiff":
        if args.git:
            if len(args.paths) != 1:
                fail(NOT_A_RESULT, "lockdiff --git takes one path")
            path = args.paths[0]
            directory = os.path.dirname(os.path.realpath(path)) or "."
            code, prefix = git(directory, "rev-parse", "--show-prefix")
            code2, old_text = git(directory, "show", f"{args.rev}:{prefix.strip()}{os.path.basename(path)}")
            if code != 0 or code2 != 0:
                fail(NOT_A_RESULT, f"{path}: not in git at {args.rev}. NOT CHECKED: copy the file before changing it and use `lockdiff OLD NEW`.")
            return lockdiff(args.rev, old_text, "working copy", read_text(path), path)
        if len(args.paths) != 2:
            fail(NOT_A_RESULT, "lockdiff takes OLD and NEW, or --git PATH")
        for p_ in args.paths:
            if not os.path.isfile(p_):
                fail(NOT_A_RESULT, f"{p_}: no such file. NOT CHECKED.")
        return lockdiff(args.paths[0], read_text(args.paths[0]), args.paths[1], read_text(args.paths[1]), args.paths[1])
    if args.command == "closure":
        return closure(args.before, args.after, args.ids, args.lock)
    return 1


if __name__ == "__main__":
    sys.exit(main())
