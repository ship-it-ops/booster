#!/usr/bin/env python3
"""
Tests for scripts/lint_plan.py. Standard library only.

Run: python3 -m unittest discover -s skills/ship-better-plans/tests -v
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
LINTER = SKILL_DIR / "scripts" / "lint_plan.py"
EXAMPLES = SKILL_DIR / "examples"

GOOD_PLAN = """\
---
type: plan
status: active
approval: draft
created: 2026-01-05
---

# Plan: demo

## Summary
Add a greeting helper and use it from the entry point.

## Context
- **Problem:** the entry point builds its greeting inline.

## Success criteria
- SC-1: the greeting comes from one helper.

## Non-goals
- Localisation.

## Constraints
- Standard library only.

## Facts and assumptions
- F-1: the entry point is `src/main.py:1`

## Approach
- **Chosen:** extract a helper — **deciding factor:** it is the only candidate.

## Risks and rollback
- **Rollback:** revert the commit.

## Specification
- FR-1: a `greet(name)` helper returns the greeting (SC-1)
- FR-2: the entry point calls the helper (SC-1)
- AC-1 (FR-1): `greet("a")` returns `hello a` — verify: `python3 -m unittest tests.test_greet`
- AC-2 (FR-2): running the entry point prints the greeting — verify: `python3 src/main.py`

## Verification
- **Commands:** test `python3 -m unittest`
- **Final check:** SC-1 by AC-1 and AC-2.

## Tasks

### T1 — Greeting helper
- **Depends on:** none
- **Covers:** FR-1, AC-1
- **Files:** `src/greet.py` (new), `tests/test_greet.py` (new)
- **Do:** Add `greet(name)` returning the string `hello <name>` and a unit test for it next to the other tests. Keep it free of I/O.
- **Verify:** `python3 -m unittest tests.test_greet` → passes
- **Kind:** code · **Size:** S · **Reversibility:** safe

### T2 — Use the helper from the entry point
- **Depends on:** T1
- **Covers:** FR-2, AC-2
- **Files:** `src/main.py` (modify), `src/greet.py` (modify)
- **Do:** Replace the inline greeting in the entry point with a call to `greet` from the helper module, and export `greet` from the module's public names.
- **Verify:** `python3 src/main.py` → prints `hello world`
- **Kind:** code · **Size:** S · **Reversibility:** safe

### Execution order
- Sequential: T1 → T2

## Open questions
None.

## Audit
Skipped by the user.

## Status
Draft.
"""


def run_linter(plan_text: str, *extra: str, files: tuple[str, ...] = ("src/main.py",)):
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        for rel in files:
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("print('hello world')\n", encoding="utf-8")
        repo.mkdir(exist_ok=True)
        plan = Path(tmp) / "plan.md"
        plan.write_text(plan_text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(LINTER), str(plan), "--repo", str(repo), *extra],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout + result.stderr


class GoodPlan(unittest.TestCase):
    def test_clean_plan_passes(self):
        code, out = run_linter(GOOD_PLAN)
        self.assertEqual(code, 0, out)
        self.assertIn("0 error(s), 0 warning(s), 2 task(s), approval: draft", out)

    def test_dag_is_derived_from_cards(self):
        code, out = run_linter(GOOD_PLAN, "--dag")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip(), "- Sequential: T1 → T2")

    def test_dag_shows_waves_when_tasks_can_run_in_parallel(self):
        plan = GOOD_PLAN.replace("`src/main.py` (modify), `src/greet.py` (modify)", "`src/main.py` (modify)")
        plan = plan.replace("- **Depends on:** T1", "- **Depends on:** none")
        code, out = run_linter(plan, "--dag")
        self.assertEqual(code, 0, out)
        self.assertIn("- Wave 1: T1, T2 (can run in parallel)", out)

    def test_bundled_examples_pass(self):
        for example in sorted(EXAMPLES.glob("example-plan-*.md")):
            result = subprocess.run(
                [sys.executable, str(LINTER), str(example), "--no-paths"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, f"{example.name}:\n{result.stdout}")
            self.assertIn("0 error(s), 0 warning(s)", result.stdout, example.name)


class Structure(unittest.TestCase):
    def test_missing_section(self):
        code, out = run_linter(GOOD_PLAN.replace("## Non-goals\n- Localisation.\n", ""))
        self.assertEqual(code, 1)
        self.assertIn("missing required section '## Non-goals'", out)

    def test_empty_section(self):
        code, out = run_linter(GOOD_PLAN.replace("- Standard library only.\n", ""))
        self.assertEqual(code, 1)
        self.assertIn("section '## Constraints' is empty", out)

    def test_placeholder_left_in(self):
        code, out = run_linter(GOOD_PLAN.replace("revert the commit.", "TBD"))
        self.assertEqual(code, 1)
        self.assertIn("placeholder TBD", out)

    def test_angle_brackets_in_real_content_are_allowed(self):
        code, out = run_linter(GOOD_PLAN.replace("Standard library only.", "Paths look like plugins/<name>/skills/<name>/."))
        self.assertEqual(code, 0, out)


class Traceability(unittest.TestCase):
    def test_requirement_without_criterion_or_task(self):
        code, out = run_linter(GOOD_PLAN.replace("- AC-1 (FR-1)", "- FR-3: an orphan requirement (SC-1)\n- AC-1 (FR-1)"))
        self.assertEqual(code, 1)
        self.assertIn("FR-3 has no acceptance criterion", out)
        self.assertIn("FR-3 is not covered by any task", out)

    def test_criterion_must_name_its_requirement(self):
        code, out = run_linter(GOOD_PLAN.replace("- AC-2 (FR-2):", "- AC-2:"))
        self.assertEqual(code, 1)
        self.assertIn("AC-2 does not name the requirement or success criterion it verifies", out)

    def test_task_covering_undefined_id(self):
        code, out = run_linter(GOOD_PLAN.replace("**Covers:** FR-2, AC-2", "**Covers:** FR-2, AC-2, FR-9"))
        self.assertEqual(code, 1)
        self.assertIn("FR-9 is referenced but never defined", out)

    def test_blocking_open_question_is_reported(self):
        code, out = run_linter(GOOD_PLAN.replace("## Open questions\nNone.", "## Open questions\n- OQ-1 (blocking): which greeting?"))
        self.assertEqual(code, 0, out)
        self.assertIn("OQ-1 is blocking", out)


class Tasks(unittest.TestCase):
    def test_missing_field(self):
        code, out = run_linter(GOOD_PLAN.replace("- **Verify:** `python3 src/main.py` → prints `hello world`\n", ""))
        self.assertEqual(code, 1)
        self.assertIn("T2 (line", out)
        self.assertIn("field 'Verify' is missing or empty", out)

    def test_dependency_cycle(self):
        code, out = run_linter(GOOD_PLAN.replace("- **Depends on:** none", "- **Depends on:** T2"))
        self.assertEqual(code, 1)
        self.assertIn("dependency cycle", out)

    def test_unknown_dependency(self):
        code, out = run_linter(GOOD_PLAN.replace("- **Depends on:** T1", "- **Depends on:** T7"))
        self.assertEqual(code, 1)
        self.assertIn("T2 depends on T7, which is not a task", out)

    def test_hard_to_reverse_task_needs_a_gate(self):
        plan = GOOD_PLAN.replace(
            "prints `hello world`\n- **Kind:** code · **Size:** S · **Reversibility:** safe",
            "prints `hello world`\n- **Kind:** code · **Size:** S · **Reversibility:** destructive",
        )
        code, out = run_linter(plan)
        self.assertEqual(code, 1)
        self.assertIn("T2: reversibility is 'destructive', not `safe`, but the card has no 'Gate'", out)
        code, out = run_linter(plan.replace("**Reversibility:** destructive", "**Reversibility:** destructive\n- **Gate:** the user confirms"))
        self.assertEqual(code, 0, out)


class Parallel(unittest.TestCase):
    def test_unlinked_tasks_sharing_a_file(self):
        code, out = run_linter(GOOD_PLAN.replace("- **Depends on:** T1", "- **Depends on:** none"))
        self.assertEqual(code, 1)
        self.assertIn("T1 and T2 both touch `src/greet.py`", out)


class Grounding(unittest.TestCase):
    def test_modified_file_must_exist(self):
        code, out = run_linter(GOOD_PLAN, files=())
        self.assertEqual(code, 1)
        self.assertIn("`src/main.py` is marked (modify) but does not exist", out)

    def test_new_file_must_not_exist(self):
        code, out = run_linter(GOOD_PLAN, files=("src/main.py", "src/greet.py"))
        self.assertEqual(code, 1)
        self.assertIn("`src/greet.py` is marked (new) but already exists", out)

    def test_file_created_by_a_dependency_counts_as_existing(self):
        code, out = run_linter(GOOD_PLAN)
        self.assertNotIn("src/greet.py` is marked (modify)", out)

    def test_evidence_line_must_exist(self):
        code, out = run_linter(GOOD_PLAN.replace("`src/main.py:1`", "`src/main.py:400`"))
        self.assertEqual(code, 1)
        self.assertIn("evidence `src/main.py:400` is past the end of the file", out)

    def test_no_paths_skips_grounding(self):
        code, out = run_linter(GOOD_PLAN, "--no-paths", files=())
        self.assertEqual(code, 0, out)


class StricterChecks(unittest.TestCase):
    def test_comment_only_section_is_empty(self):
        code, out = run_linter(GOOD_PLAN.replace("## Audit\nSkipped by the user.", "## Audit\n<!-- fill me in -->"))
        self.assertEqual(code, 1)
        self.assertIn("section '## Audit' is empty", out)

    def test_bare_ellipsis_item_is_a_placeholder(self):
        code, out = run_linter(GOOD_PLAN.replace("- Localisation.", "- …"))
        self.assertEqual(code, 1)
        self.assertIn("unfilled value", out)

    def test_todo_in_real_content_is_allowed(self):
        plan = GOOD_PLAN.replace("### T1 — Greeting helper", "### T1 — Greeting helper replacing the TODO in main")
        plan = plan.replace("- Sequential: T1 → T2", "- Sequential: T1 → T2")
        code, out = run_linter(plan)
        self.assertEqual(code, 0, out)

    def test_depends_on_must_parse(self):
        code, out = run_linter(GOOD_PLAN.replace("- **Depends on:** T1", "- **Depends on:** the helper task"))
        self.assertEqual(code, 1)
        self.assertIn("'Depends on' must be `none` or task ids", out)

    def test_duplicate_task_id(self):
        code, out = run_linter(GOOD_PLAN.replace("### T2 — Use the helper", "### T1 — Use the helper"))
        self.assertEqual(code, 1)
        self.assertIn("task id T1 is used twice", out)

    def test_stale_execution_order(self):
        code, out = run_linter(GOOD_PLAN.replace("- Sequential: T1 → T2", "- Sequential: T2 → T1"))
        self.assertEqual(code, 1)
        self.assertIn("'Execution order' does not match the task cards", out)

    def test_any_reversibility_other_than_safe_needs_a_gate(self):
        plan = GOOD_PLAN.replace(
            "prints `hello world`\n- **Kind:** code · **Size:** S · **Reversibility:** safe",
            "prints `hello world`\n- **Kind:** code · **Size:** S · **Reversibility:** not reversible, drops the legacy column",
        )
        code, out = run_linter(plan)
        self.assertEqual(code, 1)
        self.assertIn("but the card has no 'Gate'", out)

    def test_reversibility_is_required(self):
        plan = GOOD_PLAN.replace("prints `hello world`\n- **Kind:** code · **Size:** S · **Reversibility:** safe", "prints `hello world`\n- **Kind:** code · **Size:** S")
        code, out = run_linter(plan)
        self.assertEqual(code, 1)
        self.assertIn("T2 (line", out)
        self.assertIn("field 'Reversibility' is missing or empty", out)

    def test_modify_note_mentioning_add_is_not_new(self):
        code, out = run_linter(GOOD_PLAN.replace("`src/main.py` (modify)", "`src/main.py` (modify — add the call)"))
        self.assertEqual(code, 0, out)

    def test_undefined_id_anywhere(self):
        code, out = run_linter(GOOD_PLAN.replace("- **Rollback:** revert the commit.", "- **Rollback:** revert the commit; see AC-9."))
        self.assertEqual(code, 1)
        self.assertIn("AC-9 is referenced but never defined", out)

    def test_criterion_needs_an_owner(self):
        code, out = run_linter(GOOD_PLAN.replace("**Covers:** FR-2, AC-2", "**Covers:** FR-2").replace("SC-1 by AC-1 and AC-2.", "SC-1 by AC-1."))
        self.assertEqual(code, 1)
        self.assertIn("AC-2 has no owner", out)

    def test_success_criterion_must_be_carried(self):
        code, out = run_linter(GOOD_PLAN.replace("- SC-1: the greeting comes from one helper.", "- SC-1: the greeting comes from one helper.\n- SC-2: nobody notices."))
        self.assertEqual(code, 1)
        self.assertIn("SC-2 is not carried by any requirement", out)

    def test_path_spelling_does_not_hide_a_collision(self):
        plan = GOOD_PLAN.replace("- **Depends on:** T1", "- **Depends on:** none").replace("`src/greet.py` (modify)", "`./src/greet.py` (modify)")
        code, out = run_linter(plan)
        self.assertEqual(code, 1)
        self.assertIn("T1 and T2 both touch `src/greet.py`", out)

    def test_directory_entry_collides_with_files_under_it(self):
        plan = GOOD_PLAN.replace("- **Depends on:** T1", "- **Depends on:** none").replace("`src/main.py` (modify), `src/greet.py` (modify)", "`src/` (modify)")
        code, out = run_linter(plan)
        self.assertEqual(code, 1)
        self.assertIn("T1 and T2 both touch", out)

    def test_verify_cannot_need_a_file_from_an_unrelated_task(self):
        plan = GOOD_PLAN.replace("- **Depends on:** T1", "- **Depends on:** none").replace("`src/main.py` (modify), `src/greet.py` (modify)", "`src/main.py` (modify)")
        plan = plan.replace("- **Verify:** `python3 src/main.py` → prints `hello world`", "- **Verify:** `python3 src/main.py` → prints `hello world`; `tests/test_greet.py` passes")
        plan = plan.replace("- Sequential: T1 → T2", "")
        code, out = run_linter(plan)
        self.assertIn("'Verify' needs `tests/test_greet.py`, created by T1, which T2 does not depend on", out)

    def test_fact_without_evidence_is_a_warning(self):
        code, out = run_linter(GOOD_PLAN.replace("- F-1: the entry point is `src/main.py:1`", "- F-1: the entry point is the main module"))
        self.assertEqual(code, 0, out)
        self.assertIn("F-1 has no evidence", out)

    def test_revising_allows_new_files_that_exist(self):
        code, out = run_linter(GOOD_PLAN, "--revising", files=("src/main.py", "src/greet.py", "tests/test_greet.py"))
        self.assertEqual(code, 0, out)

    def test_approved_plan_cannot_have_a_blocking_question(self):
        plan = GOOD_PLAN.replace("approval: draft", "approval: approved").replace("## Open questions\nNone.", "## Open questions\n- OQ-1 (blocking): which greeting?")
        code, out = run_linter(plan)
        self.assertEqual(code, 1)
        self.assertIn("OQ-1 is blocking but the plan is marked approved", out)

    def test_id_named_in_enabling_prose_is_not_covered(self):
        plan = GOOD_PLAN.replace("**Covers:** FR-2, AC-2", "**Covers:** none — enabling: the run that AC-2 needs").replace("SC-1 by AC-1 and AC-2.", "SC-1 by AC-1.")
        code, out = run_linter(plan)
        self.assertEqual(code, 1)
        self.assertIn("FR-2 is not covered by any task", out)
        self.assertIn("AC-2 has no owner", out)

    def test_dag_marks_a_gated_task_in_a_parallel_wave(self):
        plan = GOOD_PLAN.replace("`src/main.py` (modify), `src/greet.py` (modify)", "`src/main.py` (modify)")
        plan = plan.replace("- **Depends on:** T1", "- **Depends on:** none")
        plan = plan.replace("prints `hello world`\n- **Kind:** code · **Size:** S · **Reversibility:** safe",
                            "prints `hello world`\n- **Kind:** code · **Size:** S · **Reversibility:** destructive\n- **Gate:** the user confirms")
        code, out = run_linter(plan, "--dag")
        self.assertEqual(code, 0, out)
        self.assertIn("- Wave 1: T1, T2 (T2 waits for its gate and runs alone)", out)

    def test_directory_names_in_do_are_not_treated_as_missing_files(self):
        plan = GOOD_PLAN.replace("Keep it free of I/O.", "Keep it free of I/O. Tests live under `tests/` like the others in `src/helpers/`.")
        code, out = run_linter(plan)
        self.assertEqual(code, 0, out)
        self.assertNotIn("does not exist", out)


if __name__ == "__main__":
    unittest.main()
