import contextlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("fix_check", os.path.join(HERE, "..", "scripts", "fix_check.py"))
fc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc)


def lock(**packages):
    """packages: name -> version, or name -> dict(version=..., script=True, resolved=...)"""
    out = {"lockfileVersion": 3, "packages": {"": {"name": "app"}}}
    for name, value in packages.items():
        entry = {"version": value} if isinstance(value, str) else {"version": value["version"]}
        if not isinstance(value, str):
            if value.get("script"):
                entry["hasInstallScript"] = True
            if value.get("resolved"):
                entry["resolved"] = value["resolved"]
        entry.setdefault("resolved", f"https://registry.npmjs.org/{name}/-/{name}-{entry['version']}.tgz")
        out["packages"]["node_modules/" + name.replace("__", "/")] = entry
    return json.dumps(out)


def scan(*rows):
    """rows: (package, version, id, aliases) or (package, version, id, aliases, fixed)"""
    rows = [tuple(r) + ("9.9.9",) * (5 - len(r)) for r in rows]
    if not rows:
        return json.dumps({"results": [], "experimental_config": {"licenses": {"summary": False}}})
    return json.dumps({"results": [{"source": {"path": "package-lock.json", "type": "lockfile"}, "packages": [
        {"package": {"name": p, "version": v, "ecosystem": "npm"},
         "vulnerabilities": [{"id": i, "aliases": a, "affected": [{"package": {"name": p}, "ranges": [{"events": [{"introduced": "0"}, {"fixed": f}]}]}]}],
         "groups": [{"ids": [i], "aliases": [i] + a, "max_severity": "7.5"}]} for p, v, i, a, f in rows]}]})


class Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.realpath(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        return path

    def git(self, *args):
        subprocess.run(["git", "-C", self.dir, "-c", "user.name=t", "-c", "user.email=t@example.test"] + list(args), check=True, capture_output=True)

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = fc.main(list(argv))
            except SystemExit as e:
                code = e.code
        return code, out.getvalue(), err.getvalue()


class PreflightTest(Scratch):
    def repo(self):
        self.write("package.json", '{"name": "app", "scripts": {}}\n')
        self.write("package-lock.json", lock(a="1.0.0"))
        self.write("src/app.js", "1\n")
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")

    def test_clean_tree(self):
        self.repo()
        code, out, _ = self.run_main("preflight", self.dir)
        self.assertEqual(code, 0)
        self.assertIn("package.json: no uncommitted changes", out)
        self.assertIn("2 manifest and lock file(s), none with uncommitted changes", out)
        self.assertIn("In use, from the lock files found: npm", out)

    def test_a_manifest_with_uncommitted_changes_is_named_and_others_are_not_blocked(self):
        self.repo()
        self.write("package.json", '{"name": "app", "scripts": {"lint": "x"}}\n')
        self.write("src/app.js", "2\n")
        self.write("TODO.txt", "x\n")
        code, out, _ = self.run_main("preflight", self.dir)
        self.assertIn("package.json: HAS UNCOMMITTED CHANGES", out)
        self.assertIn("package-lock.json: no uncommitted changes", out)
        self.assertIn("must not be edited as they are: package.json.", out)
        self.assertIn("TODO.txt", out)
        self.assertIn("do not stash or reset", out)

    def test_not_a_git_repository_is_said(self):
        self.write("package.json", "{}")
        code, out, _ = self.run_main("preflight", self.dir)
        self.assertEqual(code, 0)
        self.assertIn("NOT a git repository", out)

    def test_registry_and_script_settings_are_reported_without_credentials(self):
        self.repo()
        self.write(".npmrc", "registry=https://npm.internal.example.test/\n//npm.internal.example.test/:_authToken=abc123secretvalue\nignore-scripts=false\n")
        code, out, _ = self.run_main("preflight", self.dir)
        self.assertIn("sets where packages come from: registry -> npm.internal.example.test", out)
        self.assertIn("changes whether install scripts run: ignore-scripts=false", out)
        self.assertNotIn("abc123secretvalue", out)

    def test_a_symlinked_path_to_the_repository_still_sees_the_changes(self):
        self.repo()
        self.write("package.json", '{"name": "app", "scripts": {"lint": "x"}}\n')
        link = self.dir + "-link"
        os.symlink(self.dir, link)
        self.addCleanup(os.remove, link)
        code, out, _ = self.run_main("preflight", link)
        self.assertIn("package.json: HAS UNCOMMITTED CHANGES", out)

    def test_an_ignored_lock_file_is_not_called_clean(self):
        self.repo()
        self.write(".gitignore", "requirements.txt\n")
        self.git("add", ".gitignore")
        self.git("commit", "-q", "-m", "ignore")
        self.write("requirements.txt", "flask==2.0.0\n")
        code, out, _ = self.run_main("preflight", self.dir)
        self.assertIn("requirements.txt: NOT TRACKED BY GIT", out)
        self.assertIn("must not be edited as they are: requirements.txt", out)

    def test_packages_that_already_have_install_scripts_are_listed(self):
        self.write("package.json", "{}")
        self.write("package-lock.json", lock(a="1.0.0", sharp={"version": "0.33.0", "script": True}))
        code, out, _ = self.run_main("preflight", self.dir)
        self.assertIn("already have an install script: sharp", out)

    def test_existing_overrides_are_shown(self):
        self.write("package.json", '{"name": "app", "overrides": {"x": "1.2.3"}}')
        code, out, _ = self.run_main("preflight", self.dir)
        self.assertIn('package.json has overrides: {"x": "1.2.3"}', out)


class LockDiffTest(Scratch):
    def diff(self, old, new, name="package-lock.json"):
        a = self.write("old/" + name, old)
        b = self.write("new/" + name, new)
        return self.run_main("lockdiff", a, b)

    def test_a_plain_patch_bump_needs_no_attention(self):
        code, out, _ = self.diff(lock(a="1.0.0", b="2.0.0"), lock(a="1.0.1", b="2.0.0"))
        self.assertEqual(code, 0)
        self.assertIn("- a: 1.0.0 -> 1.0.1", out)
        self.assertIn("STOP AND LOOK before installing: 0", out)

    def test_a_gained_install_script_is_flagged(self):
        code, out, _ = self.diff(lock(img="1.4.0"), lock(img={"version": "1.4.1", "script": True}))
        self.assertIn("img: GAINED AN INSTALL SCRIPT in 1.4.1", out)

    def test_a_script_that_was_already_there_is_not_flagged_as_gained(self):
        code, out, _ = self.diff(lock(img={"version": "1.4.0", "script": True}), lock(img={"version": "1.4.1", "script": True}))
        self.assertNotIn("GAINED", out)

    def test_a_new_package_is_flagged_with_its_script_and_host(self):
        code, out, _ = self.diff(lock(a="1.0.0"), lock(a="1.0.0", evil={"version": "0.0.1", "script": True, "resolved": "https://cdn.example.test/evil-0.0.1.tgz"}))
        self.assertIn("evil 0.0.1: NEW PACKAGE", out)
        self.assertIn("HAS AN INSTALL SCRIPT", out)
        self.assertIn("comes from a source nothing else here uses: cdn.example.test", out)
        self.assertEqual(code, fc.NOT_CLOSED)

    def test_a_major_change_and_a_changed_host_are_flagged(self):
        code, out, _ = self.diff(lock(kit="2.0.0"), lock(kit={"version": "3.0.0", "resolved": "https://mirror.example.test/kit-3.0.0.tgz"}))
        self.assertIn("kit: BREAKING-RANGE version change (2.0.0 -> 3.0.0)", out)
        self.assertIn("kit: now comes from mirror.example.test (was registry.npmjs.org)", out)
        self.assertEqual(code, fc.NOT_CLOSED)

    def test_a_copy_with_another_name_is_still_read(self):
        a = self.write("package-lock.before.json", lock(a="1.0.0"))
        b = self.write("package-lock.after.json", lock(a="2.0.0"))
        code, out, _ = self.run_main("lockdiff", a, b)
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("a: BREAKING-RANGE version change", out)

    def test_a_zero_dot_minor_change_counts_as_breaking_and_a_patch_does_not(self):
        code, out, _ = self.diff(lock(a="0.3.1", b="0.3.1"), lock(a="0.4.0", b="0.3.2"))
        self.assertIn("a: BREAKING-RANGE", out)
        self.assertNotIn("b: BREAKING-RANGE", out)

    def test_the_same_version_with_another_checksum_is_flagged(self):
        old = json.loads(lock(a="1.0.0")); new = json.loads(lock(a="1.0.0"))
        old["packages"]["node_modules/a"]["integrity"] = "sha512-AAAA"
        new["packages"]["node_modules/a"]["integrity"] = "sha512-BBBB"
        code, out, _ = self.diff(json.dumps(old), json.dumps(new))
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("a 1.0.0: SAME VERSION, DIFFERENT CONTENT OR SOURCE", out)

    def test_a_version_change_on_a_package_with_a_script_is_noted(self):
        code, out, _ = self.diff(lock(img={"version": "1.4.0", "script": True}), lock(img={"version": "1.4.1", "script": True}))
        self.assertEqual(code, 0)
        self.assertIn("note: img: has an install script", out)

    def test_a_file_that_parses_to_no_entries_is_not_checked(self):
        code, out, err = self.diff(lock(a="1.0.0"), '{"lockfileVersion": 3, "packages": {"": {}}}')
        self.assertEqual(code, fc.NOT_A_RESULT)
        self.assertIn("NOT CHECKED", err)

    def test_an_old_format_lock_does_not_claim_to_see_scripts(self):
        old = json.dumps({"lockfileVersion": 1, "dependencies": {"a": {"version": "1.0.0"}}})
        new = json.dumps({"lockfileVersion": 1, "dependencies": {"a": {"version": "1.0.1"}}})
        code, out, _ = self.diff(old, new)
        self.assertIn("does not record install scripts", out)

    def test_a_git_source_in_requirements_is_flagged(self):
        code, out, _ = self.diff("flask==2.0.0\n", "flask==2.0.0\nthing @ git+https://example.test/thing.git\n", name="requirements.txt")
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("NEW PACKAGE", out)
        self.assertIn("non-registry", out)

    PNPM9 = "lockfileVersion: '9.0'\n\npackages:\n\n  a@{a}:\n    resolution: {{integrity: sha512-{h}}}\n{extra}\nsnapshots:\n\n  a@{a}: {{}}\n"

    def test_a_pnpm_lock_that_does_not_record_builds_does_not_claim_to_see_scripts(self):
        new = self.PNPM9.format(a="1.0.1", h="BBBB", extra="\n  b@2.0.0:\n    resolution: {integrity: sha512-CCCC}\n")
        code, out, _ = self.diff(self.PNPM9.format(a="1.0.0", h="AAAA", extra=""), new, name="pnpm-lock.yaml")
        self.assertIn("- a: 1.0.0 -> 1.0.1", out)
        self.assertIn("does not record install scripts", out)
        self.assertIn("this lock format does not show install scripts or where a package comes from, so that was not checked", out)
        self.assertNotIn("no install script", out)

    def test_a_pnpm_checksum_change_at_the_same_version_is_flagged(self):
        code, out, _ = self.diff(self.PNPM9.format(a="1.0.0", h="AAAA", extra=""), self.PNPM9.format(a="1.0.0", h="ZZZZ", extra=""), name="pnpm-lock.yaml")
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("SAME VERSION, DIFFERENT CONTENT OR SOURCE", out)

    def test_go_composer_pipenv_and_bundler_locks_are_read(self):
        code, out, _ = self.diff("module x\n\nrequire (\n\texample.test/lib v1.2.0\n)\n", "module x\n\nrequire (\n\texample.test/lib v1.2.4\n)\n", name="go.mod")
        self.assertIn("- example.test/lib: 1.2.0 -> 1.2.4", out)
        code, out, _ = self.diff("GEM\n  specs:\n    rack (3.0.0)\n", "GEM\n  specs:\n    rack (3.0.9)\n", name="Gemfile.lock")
        self.assertIn("- rack: 3.0.0 -> 3.0.9", out)

    def test_no_change_is_said(self):
        code, out, _ = self.diff(lock(a="1.0.0"), lock(a="1.0.0"))
        self.assertIn("Nothing changed in the lock file", out)

    def test_requirements_are_compared_and_scripts_cannot_be_seen(self):
        code, out, _ = self.diff("Flask==2.0.0\nrequests==2.31.0\n", "Flask==3.0.0\nrequests==2.31.0\nnewpkg==0.1\n", name="requirements.txt")
        self.assertIn("- flask: 2.0.0 -> 3.0.0", out)
        self.assertIn("flask: BREAKING-RANGE version change", out)
        self.assertIn("Added packages: 1  (newpkg 0.1: new, nothing flagged; this lock format does not show install scripts", out)
        self.assertNotIn("newpkg 0.1: NEW PACKAGE", out)
        self.assertIn("does not record install scripts", out)

    def test_against_git(self):
        self.write("package-lock.json", lock(a="1.0.0"))
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        path = self.write("package-lock.json", lock(a={"version": "1.0.1", "script": True}))
        code, out, _ = self.run_main("lockdiff", "--git", path)
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("(HEAD -> working copy)", out)
        self.assertIn("GAINED AN INSTALL SCRIPT", out)

    def test_an_unreadable_lock_file_is_not_checked(self):
        code, out, err = self.diff("{not json", lock(a="1.0.0"))
        self.assertEqual(code, fc.NOT_A_RESULT)
        self.assertIn("NOT CHECKED", err)


class ClosureTest(Scratch):
    def closure(self, before, after, *ids):
        a = self.write("before.json", before)
        b = self.write("after.json", after)
        return self.run_main("closure", a, b, *(["--ids"] + list(ids) if ids else []))

    def test_closed(self):
        code, out, _ = self.closure(scan(("a", "1.0.0", "GHSA-1", ["CVE-1"]), ("b", "2.0.0", "GHSA-2", [])), scan(("b", "2.0.0", "GHSA-2", [])), "GHSA-1")
        self.assertEqual(code, 0)
        self.assertIn("No longer reported: 1", out)
        self.assertIn("STILL REPORTED: 0", out)

    def test_a_target_can_be_named_by_an_alias(self):
        code, out, _ = self.closure(scan(("a", "1.0.0", "GHSA-1", ["CVE-1"]), ("b", "2.0.0", "GHSA-2", [])), scan(("b", "2.0.0", "GHSA-2", [])), "cve-1")
        self.assertEqual(code, 0)

    def test_an_empty_second_scan_is_not_closure_on_its_own(self):
        code, out, _ = self.closure(scan(("a", "1.0.0", "GHSA-1", [])), scan(), "GHSA-1")
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("GONE FROM THE OUTPUT BUT NOT SHOWN TO BE RESCANNED: 1", out)
        self.assertIn("--lock", out)

    def test_an_empty_second_scan_with_a_lock_file_that_moved_is_closure(self):
        a = self.write("before.json", scan(("a", "1.0.0", "GHSA-1", [], "1.0.1")))
        b = self.write("after.json", scan())
        moved = self.write("package-lock.json", lock(a="1.0.1"))
        code, out, _ = self.run_main("closure", a, b, "--ids", "GHSA-1", "--lock", moved)
        self.assertEqual(code, 0)
        self.assertIn("the lock file now resolves 1.0.1", out)

    def test_a_lock_file_that_moved_to_a_version_below_the_fix_is_not_closure(self):
        a = self.write("before.json", scan(("a", "1.0.0", "GHSA-1", [], "1.0.5")))
        b = self.write("after.json", scan())
        code, out, _ = self.run_main("closure", a, b, "--ids", "GHSA-1", "--lock", self.write("package-lock.json", lock(a="1.0.2")))
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("below the fixed version (1.0.5)", out)

    def test_a_lock_file_without_the_package_or_that_is_not_a_lock_file_proves_nothing(self):
        a = self.write("before.json", scan(("a", "1.0.0", "GHSA-1", [], "1.0.1")))
        b = self.write("after.json", scan())
        code, out, _ = self.run_main("closure", a, b, "--ids", "GHSA-1", "--lock", self.write("package-lock.json", lock(other="1.0.0")))
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("does not list a", out)
        code, out, _ = self.run_main("closure", a, b, "--ids", "GHSA-1", "--lock", self.write("notes.txt", "hello\n"))
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("could not be read as a lock file", out)
        code, out, err = self.run_main("closure", a, b, "--ids", "GHSA-1", "--lock", os.path.join(self.dir, "missing.json"))
        self.assertEqual(code, fc.NOT_A_RESULT)

    def test_a_fix_on_another_release_line_counts_only_for_that_line(self):
        a = self.write("before.json", scan(("a", "2.0.0", "GHSA-1", [], "1.0.5")))
        b = self.write("after.json", scan())
        code, out, _ = self.run_main("closure", a, b, "--ids", "GHSA-1", "--lock", self.write("package-lock.json", lock(a="3.0.0")))
        self.assertEqual(code, 0)

    def test_an_audit_that_ran_again_is_still_checked_against_the_lock_file(self):
        def audit(*vulns):
            return json.dumps({"auditReportVersion": 2, "vulnerabilities": {n: {"name": n, "via": [{"name": n, "url": "https://github.com/advisories/GHSA-aaaa-bbbb-cccc", "range": "<1.0.1", "severity": "high"}], "fixAvailable": True} for n in vulns},
                               "metadata": {"vulnerabilities": {"total": len(vulns)}, "dependencies": {"total": 5}}})
        a = self.write("before.json", audit("a"))
        b = self.write("after.json", audit())
        self.assertEqual(self.run_main("closure", a, b)[0], 0)
        code, out, _ = self.run_main("closure", a, b, "--lock", self.write("package-lock.json", lock(other="1.0.0")))
        self.assertEqual(code, fc.NOT_CLOSED)

    def test_a_package_that_pip_audit_skipped_the_second_time_is_not_closed(self):
        before = json.dumps({"dependencies": [{"name": "quill", "version": "0.9.0", "vulns": [{"id": "PYSEC-1", "aliases": [], "fix_versions": ["0.9.4"]}]}, {"name": "other", "version": "1.0", "vulns": []}]})
        after = json.dumps({"dependencies": [{"name": "quill", "skip_reason": "could not be resolved"}, {"name": "other", "version": "1.0", "vulns": []}]})
        code, out, _ = self.closure(before, after)
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("the second run skipped this package", out)

    def test_an_empty_second_scan_with_a_lock_file_that_did_not_move_is_not_closure(self):
        a = self.write("before.json", scan(("a", "1.0.0", "GHSA-1", [])))
        b = self.write("after.json", scan())
        same = self.write("package-lock.json", lock(a="1.0.0"))
        code, out, _ = self.run_main("closure", a, b, "--ids", "GHSA-1", "--lock", same)
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("still resolves a at 1.0.0", out)

    def test_results_from_two_different_tools_are_refused(self):
        npm = json.dumps({"auditReportVersion": 2, "vulnerabilities": {}, "metadata": {"vulnerabilities": {"total": 0}, "dependencies": {"total": 5}}})
        code, out, err = self.closure(scan(("a", "1.0.0", "GHSA-1", [])), npm, "GHSA-1")
        self.assertEqual(code, fc.NOT_A_RESULT)
        self.assertIn("NOT COMPARABLE", err)

    def test_still_reported_fails(self):
        code, out, _ = self.closure(scan(("a", "1.0.0", "GHSA-1", [])), scan(("a", "1.0.1", "GHSA-1", [])), "GHSA-1")
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("STILL REPORTED: 1", out)
        self.assertIn("a 1.0.1  GHSA-1", out)

    def test_a_new_advisory_fails_even_when_the_target_is_gone(self):
        code, out, _ = self.closure(scan(("a", "1.0.0", "GHSA-1", [])), scan(("c", "3.0.0", "GHSA-3", [])), "GHSA-1")
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("NEW since the first scan: 1", out)

    def test_a_target_that_was_never_in_the_first_scan_fails(self):
        code, out, _ = self.closure(scan(("a", "1.0.0", "GHSA-1", [])), scan(), "GHSA-9")
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("NOT IN THE FIRST SCAN", out)

    def test_without_ids_everything_in_the_first_scan_is_a_target(self):
        code, out, _ = self.closure(scan(("a", "1.0.0", "GHSA-1", []), ("b", "2.0.0", "GHSA-2", [])), scan(("b", "2.0.0", "GHSA-2", [])))
        self.assertEqual(code, fc.NOT_CLOSED)
        self.assertIn("No longer reported: 1", out)
        self.assertIn("STILL REPORTED: 1", out)

    def test_an_error_in_place_of_the_second_scan_is_never_closure(self):
        for bad in ("", "npm error code ENOTFOUND", '{"message": "rate limited"}'):
            code, out, err = self.closure(scan(("a", "1.0.0", "GHSA-1", [])), bad, "GHSA-1")
            self.assertEqual(code, fc.NOT_A_RESULT)
            self.assertIn("NOT CHECKED", err)
            self.assertNotIn("No longer reported", out)


if __name__ == "__main__":
    unittest.main()
