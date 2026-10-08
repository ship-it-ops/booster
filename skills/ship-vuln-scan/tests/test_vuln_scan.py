import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("vuln_scan", os.path.join(HERE, "..", "scripts", "vuln_scan.py"))
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


FILLER = [{"cveID": f"CVE-1999-{i:04d}"} for i in range(150)]


def osv_result(*rows):
    """rows: (source, package, version, id, aliases, fixed, score)"""
    by_source = {}
    for source, package, version, vid, aliases, fixed, score in rows:
        by_source.setdefault(source, []).append({
            "package": {"name": package, "version": version, "ecosystem": "npm"},
            "vulnerabilities": [{"id": vid, "aliases": aliases, "summary": "s",
                                 "affected": [{"package": {"name": package}, "ranges": [{"type": "SEMVER", "events": [{"introduced": "0"}, {"fixed": fixed}]}]}]}],
            "groups": [{"ids": [vid], "aliases": [vid] + aliases, "max_severity": str(score)}]})
    return {"results": [{"source": {"path": s, "type": "lockfile"}, "packages": p} for s, p in by_source.items()]}


class Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text if isinstance(text, str) else json.dumps(text))
        return path

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = vs.main(list(argv))
            except SystemExit as e:
                code = e.code
        return code, out.getvalue(), err.getvalue()


class InventoryTest(Scratch):
    def test_lists_lockfiles_images_and_infrastructure(self):
        self.write("package.json", "{}")
        self.write("package-lock.json", "{}")
        self.write("api/requirements.txt", "flask==3.0.0\nrequests>=2\n")
        self.write("Dockerfile", "FROM node:22-slim AS build\nFROM gcr.io/distroless/nodejs22\n")
        self.write("infra/main.tf", "")
        inv = vs.inventory(self.dir)
        self.assertEqual(inv["lockfiles"], [{"path": "package-lock.json", "ecosystem": "npm"}])
        self.assertEqual((inv["requirements"][0]["lines"], inv["requirements"][0]["pinned"]), (2, 1))
        self.assertEqual(inv["images"][0]["base_images"], ["node:22-slim", "gcr.io/distroless/nodejs22"])
        self.assertEqual(inv["infrastructure"], [os.path.join("infra", "main.tf")])
        self.assertEqual(inv["manifests_without_lock"], [])

    def test_manifest_without_a_lock_file_is_reported(self):
        self.write("svc/package.json", "{}")
        inv = vs.inventory(self.dir)
        self.assertEqual(inv["manifests_without_lock"][0]["path"], os.path.join("svc", "package.json"))

    def test_osv_scanner_ignore_entries_are_listed_with_reason_and_expiry(self):
        self.write("osv-scanner.toml", '[[IgnoredVulns]]\nid = "GHSA-aaaa-bbbb-cccc"\nreason = "not reachable"\n\n[[IgnoredVulns]]\nid = "CVE-2026-0001"\nignoreUntil = 2027-01-01\n')
        entries = vs.inventory(self.dir)["suppressions"][0]["entries"]
        self.assertEqual([e["what"] for e in entries], ["GHSA-aaaa-bbbb-cccc", "CVE-2026-0001"])
        self.assertIn("no expiry", entries[0]["detail"])
        self.assertIn('reason given: "not reachable"', entries[0]["detail"])
        self.assertIn("until 2027-01-01", entries[1]["detail"])

    def test_trivyignore_and_gitleaksignore_lines_are_listed(self):
        self.write(".trivyignore", "# comment\nCVE-2025-1111\n")
        self.write(".gitleaksignore", "abc123:config/a.env:generic-api-key:3\n")
        found = {s["path"]: [e["what"] for e in s["entries"]] for s in vs.inventory(self.dir)["suppressions"]}
        self.assertEqual(found[".trivyignore"], ["CVE-2025-1111"])
        self.assertEqual(len(found[".gitleaksignore"]), 1)

    def test_inline_markers_and_narrowing_flags_in_ci_are_found(self):
        self.write("infra/main.tf", "# checkov:skip=CKV_AWS_18: logging not needed\n")
        self.write(".github/workflows/scan.yml", "      - run: trivy fs --severity CRITICAL --ignore-unfixed .\n")
        inv = vs.inventory(self.dir)
        self.assertEqual(inv["inline_suppressions"][0]["marker"], "checkov:skip")
        self.assertEqual(inv["narrowing_flags"][0]["flags"], ["--ignore-unfixed", "--severity"])

    def test_action_inputs_environment_variables_and_a_nested_grype_config_are_found(self):
        self.write(".github/workflows/scan.yml", "jobs:\n  s:\n    steps:\n      - uses: aquasecurity/trivy-action@0.28.0\n        with:\n          severity: CRITICAL\n          ignore-unfixed: true\n          trivyignores: .ci/ignores.txt\n        env:\n          TRIVY_SKIP_DIRS: vendor\n")
        self.write(".grype/config.yaml", "ignore:\n  - vulnerability: CVE-2026-0001\n")
        self.write("build/package-lock.json", "{}")
        inv = vs.inventory(self.dir)
        flags = {f for n in inv["narrowing_flags"] for f in n["flags"]}
        self.assertTrue({"severity", "ignore-unfixed", "trivyignores", "TRIVY_SKIP_DIRS"} <= flags, flags)
        self.assertIn(os.path.join(".grype", "config.yaml"), [s["path"] for s in inv["suppressions"]])
        self.assertEqual(inv["not_walked"], ["build"])
        code, out, _ = self.run_main("inventory", self.dir)
        self.assertIn("Directories not walked, so nothing in them is listed above: build", out)

    def test_symlinks_are_listed_and_not_read(self):
        secret = os.path.join(self.dir, "outside-secret")
        with open(secret, "w") as f:
            f.write("CVE-2026-9999\n")
        os.makedirs(os.path.join(self.dir, "repo"))
        os.symlink(secret, os.path.join(self.dir, "repo", ".trivyignore"))
        inv = vs.inventory(os.path.join(self.dir, "repo"))
        self.assertEqual(inv["symlinks"], [".trivyignore"])
        self.assertEqual(inv["suppressions"], [])

    def test_audit_keys_in_package_json_and_registry_settings_are_reported(self):
        self.write("package.json", {"pnpm": {"auditConfig": {"ignoreGhsas": ["GHSA-aaaa-bbbb-cccc"]}}})
        self.write("package-lock.json", "{}")
        self.write(".npmrc", "registry=https://user:tok3n@npm.corp.example.test/\n")
        self.write(".yarnrc.yml", "yarnPath: .yarn/releases/yarn-4.cjs\n")
        inv = vs.inventory(self.dir)
        self.assertEqual(inv["suppressions"][0]["entries"][0]["what"], "GHSA-aaaa-bbbb-cccc")
        notes = " ".join(n for c in inv["package_manager_config"] for n in c["notes"])
        self.assertIn("packages come from npm.corp.example.test", notes)
        self.assertIn("yarnPath: code from the repository", notes)
        self.assertNotIn("tok3n", json.dumps(inv))

    def test_a_worktree_is_a_repository(self):
        self.write("main/.git/worktrees/wt/commondir", "../..\n")
        self.write("wt/.git", "gitdir: ../main/.git/worktrees/wt\n")
        self.assertTrue(vs.inventory(os.path.join(self.dir, "wt"))["git"]["repository"])

    def test_node_modules_and_git_are_not_walked(self):
        self.write("node_modules/x/package-lock.json", "{}")
        self.write(".git/osv-scanner.toml", "")
        inv = vs.inventory(self.dir)
        self.assertEqual(inv["lockfiles"], [])
        self.assertEqual(inv["suppressions"], [])


class ReadResultTest(Scratch):
    def test_osv_scanner_result(self):
        path = self.write("r.json", osv_result(("package-lock.json", "left-padder", "1.2.0", "GHSA-7xq2-m4vv-9c3p", ["CVE-2026-31801"], "1.2.3", 9.8)))
        tool, findings, scanned = vs.load_result(path)
        self.assertEqual(tool, "osv-scanner")
        self.assertEqual(scanned, ["package-lock.json"])
        self.assertEqual((findings[0]["package"], findings[0]["fixed"], findings[0]["score"]), ("left-padder", "1.2.3", 9.8))

    def test_an_empty_osv_result_is_a_result_with_no_advisories(self):
        code, out, _ = self.run_main("summarise", self.write("r.json", {"results": [], "experimental_config": {}}))
        self.assertEqual(code, 0)
        self.assertIn("No advisories in this result", out)

    def test_a_bare_empty_results_list_is_refused_as_ambiguous(self):
        code, out, err = self.run_main("summarise", self.write("r.json", {"results": []}))
        self.assertEqual(code, vs.NOT_A_RESULT)
        self.assertIn("cannot be told apart from a scan that read nothing", err)

    def test_another_tools_results_list_is_refused(self):
        for data in ({"results": [{"check_id": "x", "path": "a.py"}], "errors": []}, {"results": [{"filename": "a.py"}], "metrics": {}}, {"results": [], "errors": [{"message": "boom"}]}):
            code, out, _ = self.run_main("summarise", self.write("r.json", data))
            self.assertEqual(code, vs.NOT_A_RESULT)
            self.assertNotIn("No advisories", out)

    def test_pnpm_audit_result(self):
        data = {"advisories": {"1": {"module_name": "lodash", "findings": [{"version": "4.17.11"}], "github_advisory_id": "GHSA-35jh-r3h4-6jhm", "cves": ["CVE-2021-23337"],
                "patched_versions": ">=4.17.21", "severity": "high", "title": "Command Injection", "vulnerable_versions": "<4.17.21"}}, "metadata": {"totalDependencies": 12}}
        tool, findings, scanned = vs.load_result(self.write("r.json", data))
        self.assertEqual((tool, findings[0]["id"], findings[0]["version"], findings[0]["aliases"]), ("pnpm audit", "GHSA-35jh-r3h4-6jhm", "4.17.11", ["CVE-2021-23337"]))
        self.assertIn("12 dependencies examined", scanned[0])

    def test_pip_audit_skipped_packages_are_listed_as_not_audited(self):
        data = {"dependencies": [{"name": "ok", "version": "1", "vulns": []}, {"name": "local-pkg", "skip_reason": "Dependency not found on PyPI"}]}
        _, _, scanned = vs.load_result(self.write("r.json", data))
        self.assertIn("1 packages audited", scanned[0])
        self.assertIn("NOT AUDITED by pip-audit: local-pkg", scanned[1])

    def test_fixed_version_ignores_git_ranges_and_matches_pypi_names_loosely(self):
        vuln = {"affected": [{"package": {"name": "django"}, "ranges": [{"type": "GIT", "events": [{"fixed": "abc123def"}]}, {"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "4.2.1"}]}]}]}
        self.assertEqual(vs.fixed_from_osv(vuln, "Django", "PyPI"), "4.2.1")

    def test_a_malicious_package_advisory_sorts_first(self):
        data = osv_result(("l", "p", "1.0.0", "GHSA-9", [], "1.0.1", 9.8), ("l", "evil", "0.0.1", "MAL-2026-1", [], "", 0))
        rows = vs.merged(vs.parse_result(data)[1])
        self.assertEqual((rows[0]["id"], rows[0]["label"]), ("MAL-2026-1", "MALICIOUS PACKAGE"))

    def test_the_summary_groups_by_package(self):
        data = osv_result(*[("l", "p", "1.0.0", f"GHSA-{i}", [f"SNYK-JS-{i}"], f"1.0.{i}", 5.0 + i) for i in range(1, 7)])
        path = self.write("r.json", data)
        code, out, _ = self.run_main("summarise", path)
        self.assertIn("p 1.0.0  [npm]  6 advisories; lowest version that clears all of them: 1.0.6", out)
        self.assertIn("... and 2 more for this package", out)
        self.assertNotIn("SNYK-", out)

    def test_results_that_show_nothing_was_read_are_refused(self):
        cases = {
            "trivy": {"SchemaVersion": 2, "ArtifactName": ".", "Results": None},
            "npm": {"auditReportVersion": 2, "vulnerabilities": {}, "metadata": {"vulnerabilities": {"total": 0}, "dependencies": {"total": 0}}},
            "pip": {"dependencies": [{"name": "x", "skip_reason": "could not be resolved"}]},
        }
        for name, data in cases.items():
            code, out, err = self.run_main("summarise", self.write(name + ".json", data))
            self.assertEqual(code, vs.NOT_A_RESULT, name)
            self.assertIn("NOT CHECKED", err, name)

    def test_an_advisory_with_no_severity_is_not_left_to_look_minor(self):
        data = osv_result(("l", "p", "1.0.0", "GHSA-1", [], "1.0.1", ""))
        code, out, _ = self.run_main("summarise", self.write("r.json", data))
        self.assertIn("NO SEVERITY IN THIS RESULT (rate it as high", out)

    def test_the_fix_shown_is_the_nearest_one_above_what_is_installed(self):
        self.assertEqual(vs.nearest_fix("4.17.1", "4.17.3, 5.0.0-beta.1, 3.4.9"), "4.17.3")
        self.assertEqual(vs.nearest_fix("5.0.0", "4.17.3, 3.4.9"), None)
        self.assertEqual(vs.nearest_fix("affected range <1", "1.0.0"), None)

    def test_npm_audit_result(self):
        data = {"auditReportVersion": 2, "vulnerabilities": {"lodash": {"name": "lodash", "severity": "high", "fixAvailable": {"name": "lodash", "version": "4.17.21", "isSemVerMajor": False},
                "via": [{"source": 1, "name": "lodash", "title": "Command Injection", "url": "https://github.com/advisories/GHSA-35jh-r3h4-6jhm", "severity": "high", "cvss": {"score": 7.2}, "range": "<4.17.21"}]}}}
        tool, findings, _ = vs.load_result(self.write("r.json", data))
        self.assertEqual((tool, findings[0]["id"], findings[0]["score"], findings[0]["fixed"]), ("npm audit", "GHSA-35jh-r3h4-6jhm", 7.2, "by installing lodash@4.17.21"))
        self.assertEqual(findings[0]["version"], "affected range <4.17.21")

    def test_pip_audit_result(self):
        data = {"dependencies": [{"name": "jinja2", "version": "2.11.2", "vulns": [{"id": "PYSEC-2021-66", "fix_versions": ["2.11.3"], "aliases": ["CVE-2020-28493"], "description": "d"}]}, {"name": "ok", "version": "1", "vulns": []}], "fixes": []}
        tool, findings, _ = vs.load_result(self.write("r.json", data))
        self.assertEqual((tool, len(findings), findings[0]["fixed"]), ("pip-audit", 1, "2.11.3"))

    def test_trivy_result(self):
        data = {"SchemaVersion": 2, "ArtifactName": "app:1", "Results": [{"Target": "app:1 (debian 12)", "Type": "debian", "Vulnerabilities": [
            {"VulnerabilityID": "CVE-2026-1", "PkgName": "openssl", "InstalledVersion": "3.0.1", "FixedVersion": "3.0.2", "Severity": "HIGH", "CVSS": {"nvd": {"V3Score": 7.5}}, "Title": "t"}]}, {"Target": "clean"}]}
        tool, findings, scanned = vs.load_result(self.write("r.json", data))
        self.assertEqual((tool, findings[0]["score"], scanned), ("trivy", 7.5, ["app:1 (debian 12)", "clean"]))

    def test_grype_result(self):
        data = {"descriptor": {"name": "grype"}, "source": {"target": {"userInput": "app:1"}}, "matches": [{"vulnerability": {"id": "GHSA-x", "severity": "High", "fix": {"versions": ["2.0"]}, "cvss": [{"metrics": {"baseScore": 8.1}}]},
                "relatedVulnerabilities": [{"id": "CVE-2026-2"}], "artifact": {"name": "pkg", "version": "1.0", "type": "npm"}}]}
        tool, findings, _ = vs.load_result(self.write("r.json", data))
        self.assertEqual((tool, findings[0]["aliases"], findings[0]["score"]), ("grype", ["CVE-2026-2"], 8.1))

    def test_an_error_message_is_not_a_result(self):
        for name, text in (("a.json", ""), ("b.json", "npm error code ENOTFOUND"), ("c.json", '{"error": {"code": "ENOTFOUND"}}'), ("d.json", "[]")):
            code, out, err = self.run_main("summarise", self.write(name, text))
            self.assertEqual(code, vs.NOT_A_RESULT, name)
            self.assertIn("NOT CHECKED", err)
            self.assertEqual(out, "")

    def test_a_missing_file_is_not_a_result(self):
        code, _, err = self.run_main("summarise", os.path.join(self.dir, "absent.json"))
        self.assertEqual(code, vs.NOT_A_RESULT)
        self.assertIn("NOT CHECKED", err)

    def test_the_same_advisory_under_two_ids_or_in_two_lock_files_is_one_row(self):
        data = osv_result(("a/package-lock.json", "p", "1.0.0", "GHSA-1", ["CVE-1"], "1.0.1", 7.0), ("b/package-lock.json", "p", "1.0.0", "CVE-1", ["GHSA-1"], "1.0.1", 7.0))
        _, findings, _ = vs.parse_result(data)
        rows = vs.merged(findings)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sources"], ["a/package-lock.json", "b/package-lock.json"])

    def test_two_advisories_for_one_package_stay_two_rows_highest_first(self):
        data = osv_result(("l", "p", "1.0.0", "GHSA-1", [], "1.0.1", 5.0), ("l", "p", "1.0.0", "GHSA-2", [], "1.0.2", 9.1))
        rows = vs.merged(vs.parse_result(data)[1])
        self.assertEqual([r["id"] for r in rows], ["GHSA-2", "GHSA-1"])


class CompareTest(Scratch):
    def test_introduced_gone_and_kept(self):
        base = self.write("base.json", osv_result(("l", "old", "1.0.0", "GHSA-old", [], "1.0.1", 5.0), ("l", "kept", "2.0.0", "GHSA-kept", ["CVE-9"], "2.0.1", 6.0)))
        head = self.write("head.json", osv_result(("l", "kept", "2.0.0", "CVE-9", ["GHSA-kept"], "2.0.1", 6.0), ("l", "new", "3.0.0", "GHSA-new", [], "3.0.1", 9.8)))
        code, out, _ = self.run_main("compare", base, head)
        self.assertEqual(code, 0)
        self.assertRegex(out, r"Introduced \(in HEAD, not in BASE\): 1\n  - new 3\.0\.0  GHSA-new")
        self.assertRegex(out, r"No longer reported \(in BASE, not in HEAD\): 1\n  - old 1\.0\.0")
        self.assertRegex(out, r"In both: 1\n  - kept")

    def test_compare_refuses_when_one_side_is_an_error(self):
        base = self.write("base.json", dict(osv_result(), experimental_config={}))
        head = self.write("head.json", "fatal: network unreachable")
        code, out, err = self.run_main("compare", base, head)
        self.assertEqual(code, vs.NOT_A_RESULT)
        self.assertNotIn("Introduced", out)


class LockfileTest(Scratch):
    def test_package_lock_v3_skips_links_and_git_installs(self):
        path = self.write("package-lock.json", {"lockfileVersion": 3, "packages": {"": {"name": "app"}, "node_modules/a": {"version": "1.0.0", "resolved": "https://registry.npmjs.org/a/-/a-1.0.0.tgz"},
                          "node_modules/@s/b": {"version": "2.0.0"}, "node_modules/ws": {"link": True, "resolved": "packages/ws"}, "node_modules/g": {"version": "1.0.0", "resolved": "git+ssh://git@github.com/x/g.git#abc"},
                          "node_modules/a/node_modules/c": {"version": "3.0.0"}}})
        ecosystem, found, skipped = vs.packages_from(path)
        self.assertEqual(ecosystem, "npm")
        self.assertEqual(sorted(found), [("@s/b", "2.0.0"), ("a", "1.0.0"), ("c", "3.0.0")])
        self.assertEqual(sorted(w for w, _ in skipped), ["g", "ws"])

    def test_package_lock_v1(self):
        path = self.write("package-lock.json", {"lockfileVersion": 1, "dependencies": {"a": {"version": "1.0.0", "dependencies": {"b": {"version": "2.0.0"}}}}})
        self.assertEqual(sorted(vs.packages_from(path)[1]), [("a", "1.0.0"), ("b", "2.0.0")])

    def test_requirements_unpinned_lines_are_skipped_and_said_so(self):
        path = self.write("requirements.txt", "flask==3.0.0  # web\nrequests>=2\n-r other.txt\nuvicorn[standard]==0.30.1 ; python_version > '3.8'\n")
        _, found, skipped = vs.packages_from(path)
        self.assertEqual(found, [("flask", "3.0.0"), ("uvicorn", "0.30.1")])
        self.assertEqual(skipped[0][0], "requests>=2")

    def test_poetry_lock(self):
        path = self.write("poetry.lock", '[[package]]\nname = "a"\nversion = "1.0"\n\n[[package]]\nname = "g"\nversion = "0.1"\n[package.source]\ntype = "git"\nurl = "x"\n')
        _, found, skipped = vs.packages_from(path)
        self.assertEqual((found, [w for w, _ in skipped]), ([("a", "1.0")], ["g"]))

    def test_yarn_and_pnpm_and_go(self):
        yarn = self.write("yarn.lock", '# yarn lockfile v1\n\n"@s/b@^2.0.0":\n  version "2.0.1"\n  resolved "x"\n\na@^1.0.0, a@^1.1.0:\n  version "1.2.0"\n')
        self.assertEqual(sorted(vs.packages_from(yarn)[1]), [("@s/b", "2.0.1"), ("a", "1.2.0")])
        pnpm = self.write("pnpm-lock.yaml", "lockfileVersion: '9.0'\n\npackages:\n\n  '@s/b@2.0.1':\n    resolution: {integrity: x}\n\n  a@1.2.0:\n    resolution: {integrity: y}\n\nsnapshots:\n\n  a@1.2.0: {}\n")
        self.assertEqual(sorted(vs.packages_from(pnpm)[1]), [("@s/b", "2.0.1"), ("a", "1.2.0")])
        pnpm5 = self.write("old/pnpm-lock.yaml", "lockfileVersion: 5.4\n\npackages:\n\n  /lodash/4.17.11:\n    resolution: {integrity: x}\n\n  /@s/b/2.0.1_peer@1.0.0:\n    resolution: {integrity: y}\n")
        self.assertEqual(sorted(vs.packages_from(pnpm5)[1]), [("@s/b", "2.0.1"), ("lodash", "4.17.11")])

    def test_go_mod_is_read_and_go_sum_is_refused(self):
        gomod = self.write("go.mod", "module example.com/app\n\ngo 1.22\n\nrequire (\n\texample.com/m v1.2.3\n\texample.com/n v0.4.0 // indirect\n)\n\nreplace example.com/n => ../n\n")
        _, found, skipped = vs.packages_from(gomod)
        self.assertEqual(found, [("example.com/m", "1.2.3")])
        self.assertTrue(any("replace" in why for _, why in skipped))
        self.assertTrue(any("standard library" in what for what, _ in skipped))
        with self.assertRaises(ValueError):
            vs.packages_from(self.write("go.sum", "example.com/m v1.2.3 h1:abc=\n"))

    def test_private_registry_packages_are_held_back_unless_asked_for(self):
        path = self.write("package-lock.json", {"lockfileVersion": 3, "packages": {"": {}, "node_modules/pub": {"version": "1.0.0", "resolved": "https://registry.npmjs.org/pub/-/pub-1.0.0.tgz"},
                          "node_modules/@corp/secret-name": {"version": "2.0.0", "resolved": "https://npm.corp.example.test/@corp/secret-name-2.0.0.tgz"}, "packages/app": {"version": "0.1.0"}}})
        _, found, skipped = vs.packages_from(path)
        self.assertEqual(found, [("pub", "1.0.0")])
        self.assertEqual(sorted(w for w, _ in skipped), ["@corp/secret-name", "packages/app"])
        self.assertEqual(sorted(vs.packages_from(path, include_private=True)[1]), [("@corp/secret-name", "2.0.0"), ("pub", "1.0.0")])

    def test_requirements_includes_and_urls_are_not_checked_and_said_so(self):
        path = self.write("requirements.txt", "-r base.txt\n--index-url https://user:tok@pypi.org/simple\n-e git+https://example.test/x.git#egg=x\nflask==3.0.0\n")
        _, found, skipped = vs.packages_from(path)
        self.assertEqual(found, [("flask", "3.0.0")])
        text = " ".join(w + " " + y for w, y in skipped)
        self.assertIn("not followed", text)
        self.assertIn("installed from a path or URL", text)
        self.assertNotIn("tok@", text)

    def test_a_requirements_file_with_a_private_index_sends_nothing_unless_asked(self):
        path = self.write("requirements.txt", "--extra-index-url https://user:tok@pypi.corp.example.test/simple\nflask==3.0.0\nacme-billing==1.2.3\n")
        with self.assertRaises(ValueError) as caught:
            vs.packages_from(path)
        self.assertIn("pypi.corp.example.test", str(caught.exception))
        self.assertNotIn("tok", str(caught.exception))
        self.assertEqual(len(vs.packages_from(path, include_private=True)[1]), 2)

    def test_private_sources_are_held_back_in_uv_cargo_pnpm_pipenv_and_composer_locks(self):
        cases = {
            "uv.lock": '[[package]]\nname = "flask"\nversion = "3.0.0"\nsource = { registry = "https://pypi.org/simple" }\n\n[[package]]\nname = "acme-billing"\nversion = "1.2.3"\nsource = { registry = "https://pypi.internal.example.test/simple" }\n',
            "Cargo.lock": '[[package]]\nname = "serde"\nversion = "1.0.0"\nsource = "registry+https://github.com/rust-lang/crates.io-index"\n\n[[package]]\nname = "acme-secret"\nversion = "0.1.0"\nsource = "registry+https://cargo.internal.example.test/index"\n',
            "pnpm-lock.yaml": "lockfileVersion: '9.0'\n\npackages:\n\n  left-pad@1.3.0:\n    resolution: {integrity: sha512-A}\n\n  '@acme/auth@3.1.0':\n    resolution: {integrity: sha512-B, tarball: https://npm.internal.example.test/@acme/auth/-/auth-3.1.0.tgz}\n",
            "Pipfile.lock": json.dumps({"_meta": {"sources": [{"name": "corp", "url": "https://pypi.internal.example.test/simple"}]}, "default": {"acme-billing": {"version": "==1.2.3", "index": "corp"}}}),
            "composer.lock": json.dumps({"packages": [{"name": "monolog/monolog", "version": "3.0.0", "notification-url": "https://packagist.org/downloads/"},
                                                      {"name": "acme/billing", "version": "1.0.0", "notification-url": "https://repo.internal.example.test/downloads/"}]}),
        }
        for name, text in cases.items():
            _, found, skipped = vs.packages_from(self.write(name, text))
            sent = [n for n, _ in found]
            self.assertFalse([n for n in sent if "acme" in n], name)
            self.assertTrue(any("acme" in str(w) for w, _ in skipped), name)
            self.assertTrue(any("acme" in n for n, _ in vs.packages_from(self.write(name, text), include_private=True)[1]), name)

    def test_a_scoped_or_default_private_registry_beside_a_lock_file_that_names_no_sources(self):
        self.write(".npmrc", "@acme:registry=https://npm.internal.example.test/\n//npm.internal.example.test/:_authToken=abc\n")
        path = self.write("pnpm-lock.yaml", "lockfileVersion: '9.0'\n\npackages:\n\n  left-pad@1.3.0:\n    resolution: {integrity: sha512-A}\n\n  '@acme/auth@3.1.0':\n    resolution: {integrity: sha512-B}\n")
        _, found, skipped = vs.packages_from(path)
        self.assertEqual(found, [("left-pad", "1.3.0")])
        self.assertIn("this scope", skipped[0][1])
        self.write(".npmrc", "registry=https://npm.internal.example.test/\n")
        _, found, skipped = vs.packages_from(path)
        self.assertEqual(found, [])
        self.assertEqual(len(skipped), 2)

    def test_toml_lock_files_are_read_without_tomllib(self):
        path = self.write("poetry.lock", '[[package]]\nname = "a"\nversion = "1.0"\n\n[[package]]\nname = "g"\nversion = "0.1"\n\n[package.source]\ntype = "git"\nurl = "x"\n')
        saved, vs.tomllib = vs.tomllib, None
        try:
            _, found, skipped = vs.packages_from(path)
        finally:
            vs.tomllib = saved
        self.assertEqual((found, [w for w, _ in skipped]), ([("a", "1.0")], ["g"]))

    def test_a_symlinked_lock_file_is_refused(self):
        real = self.write("elsewhere/secret.txt", "flask==1.0\n")
        link = os.path.join(self.dir, "requirements.txt")
        os.symlink(real, link)
        with self.assertRaises(ValueError):
            vs.packages_from(link)

    def test_an_unknown_lock_file_is_refused(self):
        with self.assertRaises(ValueError):
            vs.packages_from(self.write("Gemfile.lock", ""))


class OsvTest(Scratch):
    def fake(self, vulns_by_package):
        calls = []

        def fetch(url, payload=None, timeout=30):
            calls.append((url, payload))
            if url.endswith("/v1/querybatch"):
                return {"results": [{"vulns": [{"id": i} for i in vulns_by_package.get(q["package"]["name"], [])]} for q in payload["queries"]]}
            vid = url.rsplit("/", 1)[-1]
            return {"id": vid, "aliases": ["CVE-2026-1"], "summary": "bad", "database_specific": {"severity": "HIGH"},
                    "affected": [{"package": {"name": "a"}, "ranges": [{"type": "SEMVER", "events": [{"introduced": "0"}, {"fixed": "1.0.1"}]}]}]}
        return fetch, calls

    def test_writes_a_result_the_other_commands_can_read(self):
        lock = self.write("requirements.txt", "a==1.0.0\nb==2.0.0\nc>=1\n")
        out_path = os.path.join(self.dir, "r.json")
        fetch, calls = self.fake({"a": ["GHSA-1"]})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            vs.osv([lock], out_path, False, fetch=fetch)
        self.assertEqual(len(calls[0][1]["queries"]), 2)
        self.assertIn("NOT CHECKED, 1 entry", out.getvalue())
        self.assertIn("Those names and versions were sent", out.getvalue())
        tool, findings, _ = vs.load_result(out_path)
        self.assertEqual((findings[0]["package"], findings[0]["id"], findings[0]["fixed"], findings[0]["label"]), ("a", "GHSA-1", "1.0.1", "HIGH"))

    def test_a_lock_file_that_parses_to_nothing_is_not_checked(self):
        lock = self.write("pnpm-lock.yaml", "lockfileVersion: '99'\n\nsomething-else:\n  x: 1\n")
        fetch, calls = self.fake({})
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as ctx:
            vs.osv([lock], None, False, fetch=fetch)
        self.assertEqual(ctx.exception.code, vs.NOT_A_RESULT)
        self.assertIn("read 0 packages", err.getvalue())
        self.assertEqual(calls, [])

    def test_a_clean_lookup_still_says_what_was_looked_up(self):
        lock = self.write("requirements.txt", "a==1.0.0\n")
        out_path = os.path.join(self.dir, "r.json")
        fetch, _ = self.fake({})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            vs.osv([lock], out_path, False, fetch=fetch)
        self.assertIn("requirements.txt: 1 packages", out.getvalue())
        tool, findings, scanned = vs.load_result(out_path)
        self.assertEqual(findings, [])
        self.assertIn("1 package versions looked up", scanned[0])

    def test_dry_run_sends_nothing(self):
        lock = self.write("requirements.txt", "a==1.0.0\n")
        fetch, calls = self.fake({})
        with contextlib.redirect_stdout(io.StringIO()):
            vs.osv([lock], None, True, fetch=fetch)
        self.assertEqual(calls, [])

    def test_a_network_failure_is_not_checked_and_writes_no_result(self):
        lock = self.write("requirements.txt", "a==1.0.0\n")
        out_path = os.path.join(self.dir, "r.json")

        def fetch(url, payload=None, timeout=30):
            raise urllib.error.URLError("unreachable")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as ctx:
            vs.osv([lock], out_path, False, fetch=fetch)
        self.assertEqual(ctx.exception.code, vs.NO_NETWORK)
        self.assertIn("NOT CHECKED", err.getvalue())
        self.assertFalse(os.path.exists(out_path))

    def test_a_short_reply_is_not_treated_as_clean(self):
        lock = self.write("requirements.txt", "a==1.0.0\nb==1.0.0\n")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
            vs.osv([lock], None, False, fetch=lambda url, payload=None, timeout=30: {"results": [{}]})
        self.assertEqual(ctx.exception.code, vs.NO_NETWORK)


class LockDiffTest(Scratch):
    def lock(self, **packages):
        out = {"lockfileVersion": 3, "packages": {"": {"name": "app"}}}
        for name, entry in packages.items():
            entry = dict(entry)
            entry.setdefault("resolved", f"https://registry.npmjs.org/{name}/-/{name}-{entry['version']}.tgz")
            out["packages"]["node_modules/" + name] = entry
        return out

    def test_a_gained_install_script_and_another_source_are_flagged(self):
        old = self.write("base/package-lock.json", self.lock(img={"version": "1.4.0"}, kit={"version": "2.0.0"}))
        new = self.write("head/package-lock.json", self.lock(img={"version": "1.4.1", "hasInstallScript": True}, kit={"version": "2.0.1", "resolved": "https://cdn.example.test/kit-2.0.1.tgz"}))
        code, out, _ = self.run_main("lockdiff", old, new)
        self.assertEqual(code, vs.FLAGGED)
        self.assertIn("img: GAINED AN INSTALL SCRIPT in 1.4.1", out)
        self.assertIn("kit: now comes from cdn.example.test", out)

    def test_a_plain_bump_is_not_flagged_and_a_missing_file_is_not_checked(self):
        old = self.write("base/package-lock.json", self.lock(a={"version": "1.0.0"}))
        new = self.write("head/package-lock.json", self.lock(a={"version": "1.0.1"}))
        self.assertEqual(self.run_main("lockdiff", old, new)[0], 0)
        code, _, err = self.run_main("lockdiff", old, os.path.join(self.dir, "nope.json"))
        self.assertEqual(code, vs.NOT_A_RESULT)
        self.assertIn("NOT CHECKED", err)

    def test_the_copy_in_ship_vuln_fix_is_the_same_code(self):
        other = os.path.join(HERE, "..", "..", "ship-vuln-fix", "scripts", "fix_check.py")
        if not os.path.isfile(other):
            self.skipTest("ship-vuln-fix is not beside this skill")

        def body(path, start, end):
            text = open(path, encoding="utf-8").read()
            return text[text.index(start):text.index(end)].replace("NOT_CLOSED", "FLAGGED").rstrip()
        mine = body(os.path.join(HERE, "..", "scripts", "vuln_scan.py"), "def lock_entries(path, text):", "# ----------------------------------------------------------------- network")
        theirs = body(other, "def lock_entries(path, text):", "# -------------------------------------------------------------------- closure")
        self.assertEqual(mine, theirs)


class SecretsTest(Scratch):
    VALUE = "pk!legacy#Zq7-mN2~xR9"

    def test_a_gitleaks_report_is_read_without_printing_the_value(self):
        path = self.write("g.json", [{"RuleID": "generic-api-key", "File": "config/a.env", "StartLine": 3, "Match": "KEY=" + self.VALUE, "Secret": self.VALUE, "Commit": "4f1d2c9a0000", "Author": "dana", "Date": "2026-02-11T09:14:02Z"}])
        code, out, _ = self.run_main("secrets", path)
        self.assertEqual(code, 0)
        self.assertIn("config/a.env:3  rule generic-api-key  assigned to KEY  commit 4f1d2c9a0000  dana 2026-02-11", out)
        self.assertIn("holds 1 secret value(s) in clear text", out)
        self.assertNotIn(self.VALUE, out)
        self.assertNotIn("Zq7", out)

    def test_the_name_is_shown_only_when_it_is_not_part_of_the_value(self):
        path = self.write("g.json", [{"RuleID": "basic-auth", "File": "a", "StartLine": 1, "Match": "deploy:" + self.VALUE, "Secret": "deploy:" + self.VALUE},
                                     {"RuleID": "bare", "File": "b", "StartLine": 2, "Match": self.VALUE, "Secret": self.VALUE}])
        out = self.run_main("secrets", path)[1]
        self.assertNotIn("assigned to", out)
        self.assertNotIn("deploy", out)

    def test_a_redacted_report_is_not_called_clear_text(self):
        path = self.write("g.json", [{"RuleID": "r", "File": "a", "StartLine": 1, "Secret": "REDACTED", "Match": "REDACTED"}])
        self.assertNotIn("clear text", self.run_main("secrets", path)[1])

    def test_trufflehog_lines(self):
        line = {"DetectorName": "AWS", "Verified": False, "Raw": self.VALUE, "SourceMetadata": {"Data": {"Git": {"file": "a.env", "line": 2, "commit": "abcdef123456789"}}}}
        path = self.write("t.jsonl", json.dumps({"level": "info", "msg": "starting"}) + "\n" + json.dumps(line) + "\n")
        code, out, _ = self.run_main("secrets", path)
        self.assertIn("a.env:2  detector AWS  commit abcdef123456", out)
        self.assertNotIn(self.VALUE, out)

    def test_an_empty_report_and_a_non_report(self):
        self.assertIn("No hits in this report", self.run_main("secrets", self.write("e.json", "[]"))[1])
        code, out, err = self.run_main("secrets", self.write("x.txt", "Finding: KEY=" + self.VALUE))
        self.assertEqual(code, vs.NOT_A_RESULT)
        self.assertNotIn(self.VALUE, out + err)


class ExploitedTest(unittest.TestCase):
    def run_exploited(self, ids, fetch):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = vs.exploited(ids, fetch=fetch)
            except SystemExit as e:
                code = e.code
        return code, out.getvalue(), err.getvalue()

    def test_listed_and_unlisted(self):
        def fetch(url, payload=None, timeout=30):
            if "epss" in url:
                return {"data": [{"cve": "CVE-2026-1", "epss": "0.91", "percentile": "0.99", "date": "2026-10-07"}]}
            return {"catalogVersion": "2026.10.04", "dateReleased": "2026-10-04", "vulnerabilities": [{"cveID": "CVE-2026-1", "dateAdded": "2026-09-01", "knownRansomwareCampaignUse": "Known"}] + FILLER}
        code, out, _ = self.run_exploited(["CVE-2026-1", "cve-2026-2", "GHSA-xxxx-yyyy-zzzz"], fetch)
        self.assertEqual(code, 0)
        self.assertIn("CVE-2026-1: KNOWN EXPLOITED (added 2026-09-01; ransomware use: Known); EPSS 0.910", out)
        self.assertIn("CVE-2026-2: not in the exploited list; no EPSS score returned", out)
        self.assertIn("No CVE alias, so not looked up (this is not 'unexploited'): GHSA-xxxx-yyyy-zzzz", out)

    def test_an_advisory_is_looked_up_through_its_cve_alias(self):
        def fetch(url, payload=None, timeout=30):
            if "epss" in url:
                return {"data": [{"cve": "CVE-2026-1", "epss": "0.5", "percentile": "0.9", "date": "2026-10-07"}]}
            return {"catalogVersion": "v", "vulnerabilities": FILLER}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            vs.exploited([], fetch=fetch, groups=[("pkg GHSA-aaaa", ["GHSA-aaaa", "CVE-2026-1"]), ("pkg GHSA-bbbb", ["GHSA-bbbb"])])
        self.assertIn("- pkg GHSA-aaaa via CVE-2026-1: not in the exploited list; EPSS 0.500", out.getvalue())
        self.assertIn("No CVE alias, so not looked up (this is not 'unexploited'): pkg GHSA-bbbb", out.getvalue())

    def test_an_implausibly_short_exploited_list_is_not_trusted(self):
        def fetch(url, payload=None, timeout=30):
            if "epss" in url:
                return {"data": []}
            return {"catalogVersion": "v", "vulnerabilities": []}
        code, out, _ = self.run_exploited(["CVE-2026-1"], fetch)
        self.assertIn("Exploited list NOT CHECKED", out)
        self.assertNotIn("not in the exploited list", out)

    def test_one_source_down_is_said_and_the_other_still_reported(self):
        def fetch(url, payload=None, timeout=30):
            if "epss" in url:
                raise urllib.error.URLError("down")
            return {"catalogVersion": "v", "vulnerabilities": FILLER}
        code, out, _ = self.run_exploited(["CVE-2026-1"], fetch)
        self.assertEqual(code, 0)
        self.assertIn("EPSS NOT CHECKED", out)
        self.assertIn("CVE-2026-1: not in the exploited list", out)
        self.assertNotIn("EPSS 0", out)

    def test_both_sources_down_is_not_checked(self):
        def fetch(url, payload=None, timeout=30):
            raise urllib.error.URLError("down")
        code, out, err = self.run_exploited(["CVE-2026-1"], fetch)
        self.assertEqual(code, vs.NO_NETWORK)
        self.assertIn("NOT CHECKED", err)
        self.assertEqual(out, "")

    def test_an_advisory_with_no_cve_alias_in_the_result_is_resolved_through_the_advisory_service(self):
        def fetch(url, payload=None, timeout=30):
            if "/v1/vulns/GHSA-aaaa-bbbb-cccc" in url:
                return {"id": "GHSA-aaaa-bbbb-cccc", "aliases": ["CVE-2026-0007"]}
            if "epss" in url:
                return {"data": [{"cve": "CVE-2026-0007", "epss": "0.5", "percentile": "0.9", "date": "2026-10-01"}]}
            return {"catalogVersion": "v", "vulnerabilities": FILLER + [{"cveID": "CVE-2026-0007", "dateAdded": "2026-09-01"}]}
        code, out, _ = self.run_exploited(["GHSA-aaaa-bbbb-cccc"], fetch)
        self.assertEqual(code, 0)
        self.assertIn("GHSA-aaaa-bbbb-cccc -> CVE-2026-0007", out)
        self.assertIn("KNOWN EXPLOITED", out)

    def test_no_cve_ids_is_refused_not_reported_as_unexploited(self):
        code, _, err = self.run_exploited(["GHSA-xxxx-yyyy-zzzz"], lambda *a, **k: {})
        self.assertEqual(code, vs.NOT_A_RESULT)
        self.assertIn("not the same as 'not exploited'", err)


if __name__ == "__main__":
    unittest.main()
