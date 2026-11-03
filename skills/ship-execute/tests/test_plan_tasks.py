#!/usr/bin/env python3
"""
Tests for scripts/plan_tasks.py. Standard library only (git must be on PATH).

Run: python3 -m unittest discover -s skills/ship-execute/tests -v
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "plan_tasks.py"

PLAN = """\
---
type: plan
status: active
approval: approved
plan_format: 2
base: main@abc1234
---

# Plan: demo

## Specification
- FR-1: a greeting helper exists (SC-1)
- AC-1 (FR-1): `greet("a")` returns `hello a` — verify: `python3 -m unittest tests.test_greet`
- AC-2 (FR-1): the legacy file is gone — verify: `ls legacy.txt` fails

## Verification
- **Setup:** `pip install -e .`
- **Commands:** test `python3 -m unittest`
- **Baseline:** 3 passed
- **Final check:** SC-1 by AC-1 and AC-2.

## Tasks

### Conventions for every task
<!-- template comment that must not reach an agent -->
- Standard library only.
- Commit messages start with the task id.

### T1 — Greeting helper
- **Depends on:** none
- **Covers:** FR-1, AC-1
- **Files:** `src/greet.py` (new), `tests/test_greet.py` (new)
- **Do:** Add `greet(name)` returning `hello <name>`, with a unit test.
- **Verify:** `python3 -m unittest tests.test_greet` → passes
- **Kind:** code · **Size:** S · **Reversibility:** safe

### T2 — Docs
- **Depends on:** T1
- **Covers:** none — enabling: users can find the helper that AC-1 describes
- **Files:** `README.md` (modify)
- **Do:** Document the helper in the README usage section.
- **Verify:** `grep -c greet README.md` → 1 or more
- **Kind:** docs · **Size:** S · **Reversibility:** safe

### T3 — Delete the legacy file
- **Depends on:** T1
- **Covers:** AC-2
- **Files:** `legacy.txt` (delete)
- **Do:** Delete the legacy file; nothing reads it.
- **Verify:** `ls legacy.txt` → No such file
- **Kind:** code · **Size:** S · **Reversibility:** destructive: the only copy
- **Gate:** the user confirms the file was archived

### T4 — Changelog
- **Depends on:** T3, T2
- **Covers:** none — enabling: release notes
- **Files:** `CHANGELOG.md` (modify)
- **Do:** Add a changelog line for the helper and the removal.
- **Verify:** `grep -c legacy CHANGELOG.md` → 1 or more
- **Kind:** docs · **Size:** S · **Reversibility:** safe

### Execution order
```mermaid
graph TD
  T1 --> T2
```

## Status
Approved.
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout.strip()


class Repo:
    """A throwaway git repository holding the plan and a few files."""

    def __init__(self, plan_text: str = PLAN):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q", "-b", "main")
        for rel, body in {"README.md": "# demo\n", "legacy.txt": "old\n", "CHANGELOG.md": "# log\n",
                          "tests/test_old.py": "assert True\n", "src/__init__.py": ""}.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(body)
        self.plan = self.root / "docs" / "plan.md"
        self.plan.parent.mkdir()
        self.plan.write_text(plan_text)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "init")

    def run(self, *args: str):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.plan), *args],
                                cwd=self.root, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout + result.stderr

    def commit(self, files: dict[str, str | None], message: str = "work") -> str:
        for rel, body in files.items():
            target = self.root / rel
            if body is None:
                git(self.root, "rm", "-q", rel)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body)
                git(self.root, "add", "-f", rel)
        git(self.root, "commit", "-q", "-m", message)
        return git(self.root, "rev-parse", "--short", "HEAD")

    def add_worktree(self, name: str, branch: str) -> str:
        path = self.root / ".claude" / "worktrees" / name
        git(self.root, "worktree", "add", "-q", "-b", branch, str(path))
        return git(path, "rev-parse", "--show-toplevel")

    def done(self, task: str):
        """Mark a task done the way the executor must: gate passed if any, a real commit, a verification note."""
        self.run("approve", task, "--note", "yes")
        return self.run("mark", task, "done", "--commit", "HEAD", "--verified", "check -> ok")

    def close(self):
        self.tmp.cleanup()


class Base(unittest.TestCase):
    plan_text = PLAN

    def setUp(self):
        self.repo = Repo(self.plan_text)
        self.addCleanup(self.repo.close)


class Summary(Base):
    def test_summary_lists_tasks_waves_and_gates(self):
        code, out = self.repo.run("summary")
        self.assertEqual(code, 0, out)
        self.assertIn("Plan: demo", out)
        self.assertIn("Approval: approved", out)
        self.assertIn("Wave 2: T2, T3  (independent; gated: T3)", out)
        self.assertIn("gate: the user confirms the file was archived", out)
        self.assertIn("verify: `grep -c greet README.md` → 1 or more", out)
        self.assertIn("Agents: 4 task agent(s), 1 review of the whole change", out)

    def test_summary_json(self):
        code, out = self.repo.run("summary", "--json")
        data = json.loads(out)
        self.assertEqual(data["waves"], [["T1"], ["T2", "T3"], ["T4"]])
        self.assertEqual(data["tasks"]["T1"]["covers"], ["AC-1", "FR-1"])
        self.assertEqual(data["tasks"]["T2"]["covers"], [])
        self.assertEqual(data["tasks"]["T4"]["depends_on"], ["T3", "T2"])
        self.assertEqual(data["verification"]["setup"], "`pip install -e .`")

    def test_ledger_lives_in_the_git_directory(self):
        self.repo.done("T1")
        self.assertEqual(len(list((self.repo.root / ".git" / "ship-execute").glob("plan-*.json"))), 1)
        self.assertEqual(git(self.repo.root, "status", "--short"), "")

    def test_verify_is_printed_exactly_as_written(self):
        repo = Repo(PLAN.replace("`grep -c greet README.md` → 1 or more", "`grep -c \"^  greet\" README.md` → 1 or more"))
        self.addCleanup(repo.close)
        code, out = repo.run("summary")
        self.assertIn('verify: `grep -c "^  greet" README.md`', out)


class Problems(unittest.TestCase):
    def check(self, old: str, new: str, expected: str):
        repo = Repo(PLAN.replace(old, new))
        self.addCleanup(repo.close)
        code, out = repo.run("summary")
        self.assertEqual(code, 1, out)
        self.assertIn(expected, out)
        code, out = repo.run("next")
        self.assertEqual(code, 1, out)

    def test_unparseable_dependency(self):
        self.check("- **Depends on:** T3, T2", "- **Depends on:** the earlier tasks", "T4: 'Depends on' is not `none` or a list of task ids")

    def test_unknown_dependency(self):
        self.check("- **Depends on:** T3, T2", "- **Depends on:** T9", "T4: depends on T9, which is not a task")

    def test_cycle(self):
        self.check("### T1 — Greeting helper\n- **Depends on:** none", "### T1 — Greeting helper\n- **Depends on:** T4", "dependency cycle")

    def test_missing_verify(self):
        self.check("- **Verify:** `grep -c greet README.md` → 1 or more\n", "", "T2: the card has no 'Verify'")

    def test_destructive_task_without_gate(self):
        self.check("- **Gate:** the user confirms the file was archived\n", "", "T3: reversibility is 'destructive: the only copy' but the card has no 'Gate'")

    def test_missing_reversibility(self):
        self.check("- **Kind:** docs · **Size:** S · **Reversibility:** safe\n\n### T3", "- **Kind:** docs · **Size:** S\n\n### T3", "T2: the card has no 'Reversibility'")

    def test_missing_files(self):
        self.check("- **Files:** `README.md` (modify)\n", "", "T2: the card has no 'Files'")

    def test_no_cards(self):
        repo = Repo("# Plan: old style\n\n## Tasks\n1. do a thing\n2. do another\n")
        self.addCleanup(repo.close)
        code, out = repo.run("summary")
        self.assertEqual(code, 1)
        self.assertIn("no task cards found", out)


class Brief(Base):
    def test_brief_carries_exactly_what_a_task_agent_needs(self):
        code, out = self.repo.run("brief", "T1")
        self.assertEqual(code, 0, out)
        self.assertIn("TASK T1 — Greeting helper", out)
        self.assertIn("Add `greet(name)` returning `hello <name>`", out)
        self.assertIn("- src/greet.py (new)", out)
        self.assertIn("- FR-1: a greeting helper exists (SC-1)", out)
        self.assertIn('- AC-1 (FR-1): `greet("a")` returns `hello a`', out)
        self.assertIn("`python3 -m unittest tests.test_greet` → passes", out)
        self.assertIn("- Standard library only.", out)
        self.assertIn("`pip install -e .`", out)
        self.assertIn("never `git add -A`", out)
        self.assertNotIn("GATE:", out)

    def test_fenced_code_in_a_card_reaches_the_briefing(self):
        repo = Repo(PLAN.replace("- **Do:** Document the helper in the README usage section.",
                                 "- **Do:** Document the helper in the README usage section, with this example:\n  ```python\n  greet(\"a\")  # hello a\n  ```"))
        self.addCleanup(repo.close)
        code, out = repo.run("brief", "T2")
        self.assertIn('greet("a")  # hello a', out)
        self.assertIn("```python", out)

    def test_template_comment_in_a_field_is_dropped(self):
        repo = Repo(PLAN.replace("- **Kind:** docs · **Size:** S · **Reversibility:** safe\n\n### T3",
                                 "- **Kind:** docs · **Size:** S · **Reversibility:** safe\n<!-- When Reversibility is anything but safe, add: - **Gate:** what a person confirms -->\n\n### T3"))
        self.addCleanup(repo.close)
        data = json.loads(repo.run("summary", "--json")[1])
        self.assertEqual(data["tasks"]["T2"]["gate"], "")
        self.assertEqual(data["tasks"]["T2"]["reversibility"], "safe")

    def test_gated_task_briefing_says_whether_the_gate_was_passed(self):
        code, out = self.repo.run("brief", "T3")
        self.assertIn("GATE (not yet confirmed): the user confirms the file was archived", out)
        self.assertIn("WHAT CANNOT BE UNDONE: destructive: the only copy", out)
        code, out = self.repo.run("brief", "T3", "--out")
        self.assertEqual(code, 1)
        self.assertIn("cannot be handed to an agent", out)
        self.repo.run("approve", "T3", "--note", "archived on the NAS")
        code, out = self.repo.run("brief", "T3")
        self.assertIn("GATE (passed): the user confirms the file was archived", out)
        self.assertIn('"archived on the NAS"', out)
        self.assertEqual(self.repo.run("brief", "T3", "--out")[0], 0)

    def test_task_with_no_files_is_told_not_to_commit(self):
        repo = Repo(PLAN.replace("- **Files:** `README.md` (modify)", "- **Files:** none"))
        self.addCleanup(repo.close)
        code, out = repo.run("brief", "T2")
        self.assertIn("THIS TASK CHANGES NO FILES", out)
        self.assertNotIn("git add", out)

    def test_out_writes_the_briefing_where_any_worktree_can_read_it(self):
        code, out = self.repo.run("brief", "T1", "--out")
        path = Path(out.strip())
        self.assertTrue(path.is_file())
        self.assertIn("/.git/ship-execute/", str(path))
        self.assertIn("TASK T1", path.read_text())

    def test_brief_leaves_out_what_the_card_does_not_cover(self):
        code, out = self.repo.run("brief", "T1")
        self.assertNotIn("AC-2", out)
        self.assertNotIn("legacy", out)
        self.assertNotIn("template comment", out)

    def test_enabling_task_gets_no_criteria(self):
        code, out = self.repo.run("brief", "T2")
        self.assertNotIn("WHAT THIS TASK CONTRIBUTES TO", out)

    def test_unknown_task(self):
        code, out = self.repo.run("brief", "T9")
        self.assertEqual(code, 2)


class Next(Base):
    def next(self):
        code, out = self.repo.run("next", "--json")
        self.assertEqual(code, 0, out)
        return json.loads(out)

    def test_first_wave(self):
        result = self.next()
        self.assertEqual(result["ready"], ["T1"])
        self.assertEqual(result["waiting"], ["T2", "T3", "T4"])
        self.assertFalse(result["finished"])

    def test_gated_task_is_never_in_the_parallel_set(self):
        self.repo.done("T1")
        result = self.next()
        self.assertEqual(result["ready"], ["T2"])
        self.assertEqual(result["gated"], ["T3"])
        code, out = self.repo.run("wave")
        self.assertEqual(code, 1, out)

    def test_declined_gate_stops_its_dependents_only(self):
        self.repo.done("T1")
        self.repo.done("T2")
        self.repo.run("mark", "T3", "declined")
        result = self.next()
        self.assertEqual(result["ready"], [])
        self.assertEqual(result["unreachable"], {"T4": "T3"})
        self.assertTrue(result["finished"])
        self.assertFalse(result["all_done"])
        code, out = self.repo.run("next")
        self.assertIn("Not runnable: T4 depends on T3, which is declined", out)
        self.assertIn("some tasks did not complete", out)

    def test_running_task_keeps_the_run_unfinished(self):
        tree = self.repo.add_worktree("wt-1", "worktree-1")
        code, out = self.repo.run("mark", "T1", "running", "--worktree", tree, "--branch", "worktree-1")
        self.assertEqual(code, 0, out)
        result = self.next()
        self.assertEqual(result["running"], ["T1"])
        self.assertIn(f"worktree: {tree}", self.repo.run("ledger")[1])
        self.assertFalse(result["finished"])

    def test_all_done(self):
        for task in ("T1", "T2", "T3", "T4"):
            self.assertEqual(self.repo.done(task)[0], 0)
        result = self.next()
        self.assertTrue(result["finished"] and result["all_done"])

    def test_tasks_naming_the_same_file_are_not_run_together(self):
        repo = Repo(PLAN.replace("- **Files:** `README.md` (modify)", "- **Files:** `README.md` (modify), `CHANGELOG.md` (modify)")
                        .replace("- **Depends on:** T3, T2", "- **Depends on:** T1"))
        self.addCleanup(repo.close)
        repo.done("T1")
        result = json.loads(repo.run("next", "--json")[1])
        self.assertEqual(result["ready"], ["T2"])
        self.assertEqual(result["ready_after"], {"T4": "T2"})

    def test_a_task_that_changes_no_files_runs_alone_and_can_stop_the_plan(self):
        repo = Repo(PLAN.replace("- **Files:** `README.md` (modify)", "- **Files:** none").replace("- **Depends on:** T3, T2", "- **Depends on:** T1"))
        self.addCleanup(repo.close)
        repo.done("T1")
        result = json.loads(repo.run("next", "--json")[1])
        self.assertEqual(result["ready"], ["T2"])
        self.assertEqual(result["ready_after"], {"T3": "T2", "T4": "T2"})
        self.assertEqual(result["gated"], [])
        self.assertFalse(result["finished"])
        repo.run("mark", "T2", "needs-decision", "--note", "the answer was: stop")
        result = json.loads(repo.run("next", "--json")[1])
        self.assertEqual(result["ready"], [])
        self.assertEqual(result["unreachable"], {"T3": "T2", "T4": "T2"})

    def test_wave_prints_workflow_arguments_for_the_parallel_set(self):
        repo = Repo(PLAN.replace("- **Depends on:** T3, T2", "- **Depends on:** T1"))
        self.addCleanup(repo.close)
        repo.done("T1")
        code, out = repo.run("wave")
        self.assertEqual(code, 0, out)
        args = json.loads(out)
        self.assertEqual([t["id"] for t in args["tasks"]], ["T2", "T4"])
        self.assertEqual(args["startCommit"], git(repo.root, "rev-parse", "--short", "HEAD"))
        self.assertTrue(all(Path(t["briefPath"]).is_file() for t in args["tasks"]))


class Ledger(Base):
    def test_mark_and_set_are_recorded(self):
        git(self.repo.root, "switch", "-q", "-c", "ship/demo")
        self.repo.run("set", "branch", "ship/demo")
        sha = git(self.repo.root, "rev-parse", "--short", "HEAD")
        self.repo.run("mark", "T1", "done", "--commit", sha, "--verified", "unittest -> 4 passed", "--note", "no deviations")
        code, out = self.repo.run("ledger")
        self.assertIn("branch: ship/demo", out)
        self.assertIn(f"T1: done — {sha} · verified: unittest -> 4 passed · note: no deviations", out)
        self.assertIn("T2: pending", out)

    def test_done_needs_a_verification_and_a_real_commit_on_the_branch(self):
        code, out = self.repo.run("mark", "T1", "done", "--commit", "HEAD")
        self.assertEqual(code, 1)
        self.assertIn("give --verified", out)
        code, out = self.repo.run("mark", "T1", "done", "--verified", "ok")
        self.assertIn("needs --commit", out)
        code, out = self.repo.run("mark", "T1", "done", "--verified", "ok", "--commit", "deadbeef")
        self.assertIn("does not exist", out)
        git(self.repo.root, "switch", "-q", "-c", "side")
        side = self.repo.commit({"x.txt": "x\n"})
        git(self.repo.root, "switch", "-q", "main")
        code, out = self.repo.run("mark", "T1", "done", "--verified", "ok", "--commit", side)
        self.assertEqual(code, 1)
        self.assertIn("is not on the current branch", out)

    def test_task_cannot_start_before_its_dependencies_are_done(self):
        code, out = self.repo.run("mark", "T2", "running")
        self.assertEqual(code, 1)
        self.assertIn("T2 depends on T1, which is not done", out)

    def test_gated_task_cannot_run_until_the_gate_is_recorded(self):
        self.repo.done("T1")
        code, out = self.repo.run("mark", "T3", "running")
        self.assertEqual(code, 1)
        self.assertIn("its gate has not been passed", out)
        code, out = self.repo.run("approve", "T3")
        self.assertEqual(code, 1)
        self.repo.run("approve", "T3", "--note", "yes, archived last week")
        self.assertEqual(self.repo.run("mark", "T3", "running")[0], 0)
        self.assertIn("gate passed", self.repo.run("ledger")[1])
        self.assertEqual(self.repo.run("approve", "T2", "--note", "x")[0], 1)

    def test_a_gate_is_passed_for_one_dispatch_and_one_card(self):
        self.repo.done("T1")
        self.repo.run("approve", "T3", "--note", "yes")
        self.repo.run("mark", "T3", "running")
        self.repo.run("mark", "T3", "blocked")
        code, out = self.repo.run("mark", "T3", "running")
        self.assertEqual(code, 1)
        self.assertIn("its gate has not been passed", out)
        self.repo.run("approve", "T3", "--note", "yes again")
        self.repo.plan.write_text(self.repo.plan.read_text().replace("Delete the legacy file; nothing reads it.", "Delete the legacy file and the data directory."))
        code, out = self.repo.run("mark", "T3", "running")
        self.assertEqual(code, 1)
        self.assertIn("its card changed since the gate was passed", out)

    def test_work_is_refused_off_the_run_branch(self):
        self.repo.run("set", "branch", "ship/demo")
        code, out = self.repo.run("mark", "T1", "running")
        self.assertEqual(code, 1)
        self.assertIn("the run is on branch `ship/demo` but `main` is checked out", out)

    def test_a_commit_from_before_the_run_is_not_a_tasks_work(self):
        self.repo.run("set", "start", git(self.repo.root, "rev-parse", "--short", "HEAD"))
        code, out = self.repo.run("mark", "T1", "done", "--verified", "ok", "--commit", "HEAD")
        self.assertEqual(code, 1)
        self.assertIn("was already there when the run started", out)

    def test_worktree_and_branch_claims_are_checked(self):
        code, out = self.repo.run("mark", "T1", "running", "--worktree", "/somewhere/else")
        self.assertEqual(code, 1)
        self.assertIn("is not a linked worktree", out)
        tree = self.repo.add_worktree("wt-2", "worktree-2")
        code, out = self.repo.run("mark", "T1", "running", "--worktree", tree, "--branch", "main")
        self.assertEqual(code, 1)
        self.assertIn("not a task's throwaway branch", out)

    def test_cleanup_removes_only_a_finished_tasks_worktree(self):
        tree = self.repo.add_worktree("wt-3", "worktree-3")
        self.repo.run("mark", "T1", "running", "--worktree", tree, "--branch", "worktree-3")
        code, out = self.repo.run("cleanup", "T1")
        self.assertEqual(code, 1)
        self.assertIn("is not done", out)
        self.assertTrue(Path(tree).is_dir())
        self.repo.done("T1")
        code, out = self.repo.run("cleanup", "T1")
        self.assertEqual(code, 0, out)
        self.assertFalse(Path(tree).exists())
        self.assertEqual(git(self.repo.root, "branch", "--list", "worktree-3"), "")

    def test_corrupt_ledger_is_reported_and_kept(self):
        self.repo.done("T1")
        ledger = next((self.repo.root / ".git" / "ship-execute").glob("plan-*.json"))
        ledger.write_text("{not json")
        code, out = self.repo.run("next")
        self.assertEqual(code, 1)
        self.assertIn("is not valid JSON", out)
        self.assertEqual(ledger.read_text(), "{not json")

    def test_card_edited_after_it_was_done_is_flagged(self):
        self.repo.done("T1")
        self.repo.plan.write_text(self.repo.plan.read_text().replace("returning `hello <name>`", "returning `hi <name>`"))
        code, out = self.repo.run("next")
        self.assertIn("WARNING  T1: its card changed after it was marked done", out)

    def test_clear_removes_the_ledger(self):
        self.repo.done("T1")
        self.repo.run("clear")
        self.assertIn("T1: pending", self.repo.run("ledger")[1])

    def test_bad_state_is_rejected(self):
        code, out = self.repo.run("mark", "T1", "finished")
        self.assertEqual(code, 2)


class Check(Base):
    def test_commit_matching_the_card_passes(self):
        sha = self.repo.commit({"src/greet.py": "def greet(n): return 'hello ' + n\n", "tests/test_greet.py": "assert True\n"})
        code, out = self.repo.run("check", "T1", sha)
        self.assertEqual(code, 0, out)
        self.assertIn("OK    T1", out)

    def test_editing_an_existing_test_outside_the_card_fails(self):
        sha = self.repo.commit({"src/greet.py": "x = 1\n", "tests/test_greet.py": "assert True\n", "tests/test_old.py": "assert True  # loosened\n"})
        code, out = self.repo.run("check", "T1", sha)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL  tests/test_old.py: changes an existing test that the card does not own", out)

    def test_deleting_an_existing_test_outside_the_card_fails(self):
        sha = self.repo.commit({"src/greet.py": "x = 1\n", "tests/test_greet.py": "assert True\n", "tests/test_old.py": None})
        code, out = self.repo.run("check", "T1", sha)
        self.assertEqual(code, 1, out)
        self.assertIn("deletes an existing test", out)

    def test_committed_cache_or_env_file_fails(self):
        sha = self.repo.commit({"src/greet.py": "x = 1\n", "tests/test_greet.py": "assert True\n",
                                "src/__pycache__/greet.cpython-312.pyc": "x", ".env": "SECRET=1\n"})
        code, out = self.repo.run("check", "T1", sha)
        self.assertEqual(code, 1, out)
        self.assertIn("src/__pycache__/greet.cpython-312.pyc: build output, cache, or environment/credential file committed", out)
        self.assertIn(".env: build output, cache, or environment/credential file committed", out)

    def test_other_file_outside_the_card_is_a_note(self):
        sha = self.repo.commit({"src/greet.py": "x = 1\n", "tests/test_greet.py": "assert True\n", "README.md": "# demo\nmore\n"})
        code, out = self.repo.run("check", "T1", sha)
        self.assertEqual(code, 0, out)
        self.assertIn("NOTE  README.md: changed outside the card's Files", out)

    def test_owned_file_left_untouched_is_a_note(self):
        sha = self.repo.commit({"src/greet.py": "x = 1\n"})
        code, out = self.repo.run("check", "T1", sha)
        self.assertEqual(code, 0, out)
        self.assertIn("NOTE  tests/test_greet.py: listed in the card's Files but not changed", out)

    def test_a_card_that_owns_a_test_may_delete_it(self):
        repo = Repo(PLAN.replace("- **Files:** `legacy.txt` (delete)", "- **Files:** `legacy.txt` (delete), `tests/test_old.py` (delete)"))
        self.addCleanup(repo.close)
        sha = repo.commit({"legacy.txt": None, "tests/test_old.py": None})
        code, out = repo.run("check", "T3", sha)
        self.assertEqual(code, 0, out)

    def test_unknown_commit(self):
        code, out = self.repo.run("check", "T1", "deadbeef")
        self.assertEqual(code, 1)
        self.assertIn("cannot read deadbeef", out)

    def test_files_the_card_owns_are_never_junk(self):
        repo = Repo(PLAN.replace("`src/greet.py` (new), `tests/test_greet.py` (new)", "`src/greet.py` (new), `tests/test_greet.py` (new), `build/config.json` (new)"))
        self.addCleanup(repo.close)
        sha = repo.commit({"src/greet.py": "x = 1\n", "tests/test_greet.py": "assert True\n", "build/config.json": "{}\n"})
        code, out = repo.run("check", "T1", sha)
        self.assertEqual(code, 0, out)

    def test_env_example_is_not_a_secret(self):
        sha = self.repo.commit({"src/greet.py": "x = 1\n", "tests/test_greet.py": "assert True\n", ".env.example": "KEY=\n"})
        code, out = self.repo.run("check", "T1", sha)
        self.assertEqual(code, 0, out)
        self.assertIn("NOTE  .env.example: added outside the card's Files", out)

    def test_changing_check_configuration_outside_the_card_fails(self):
        sha = self.repo.commit({"src/greet.py": "x = 1\n", "tests/test_greet.py": "assert True\n", "pyproject.toml": "[tool.pytest]\n", "conftest.py": "collect_ignore = ['tests/test_old.py']\n"})
        code, out = self.repo.run("check", "T1", sha)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL  pyproject.toml: changes a check or its configuration", out)
        self.assertIn("FAIL  conftest.py: changes a check or its configuration", out)

    def test_range_audits_every_commit_together(self):
        start = git(self.repo.root, "rev-parse", "--short", "HEAD")
        self.repo.commit({"src/greet.py": "x = 1\n"})
        tip = self.repo.commit({"tests/test_greet.py": "assert True\n", "tests/test_old.py": "assert True  # loosened\n"})
        code, out = self.repo.run("check", "T1", f"{start}..{tip}")
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_old.py", out)
        self.assertNotIn("not changed", out)


class Preflight(Base):
    def test_cards_that_match_the_tree(self):
        code, out = self.repo.run("preflight")
        self.assertEqual(code, 0, out)
        self.assertIn("is not a commit in this repository", out)

    def test_missing_and_already_existing_files(self):
        repo = Repo(PLAN.replace("`README.md` (modify)", "`docs/guide.md` (modify)").replace("`src/greet.py` (new)", "`src/__init__.py` (new)"))
        self.addCleanup(repo.close)
        code, out = repo.run("preflight")
        self.assertEqual(code, 1, out)
        self.assertIn("PROBLEM  T2: `docs/guide.md` is marked (modify) but does not exist", out)
        self.assertIn("PROBLEM  T1: `src/__init__.py` is marked (new) but already exists", out)

    def test_files_changed_since_the_base_are_listed(self):
        base = git(self.repo.root, "rev-parse", "--short", "HEAD")
        self.repo.plan.write_text(self.repo.plan.read_text().replace("base: main@abc1234", f"base: main@{base}"))
        self.repo.commit({"README.md": "# demo\nchanged\n"})
        code, out = self.repo.run("preflight")
        self.assertEqual(code, 0, out)
        self.assertIn(f"NOTE     T2: changed since the plan's base ({base}): README.md", out)


if __name__ == "__main__":
    unittest.main()
