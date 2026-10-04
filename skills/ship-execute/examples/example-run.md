# Example — a run with a parallel wave, a declined gate and a task that needs a decision

What the user sees from start to finish. The plan has five tasks: T1; then T2, T3 and T5, which are independent of each other; then T4, which needs T3 and T5. T3 deletes a legacy export and has a gate. T2 turns out to contradict an existing test.

---

## The start summary and the one question

```text
Plan: "Reorder list, empty-total change, and legacy export removal" (approved, 5 tasks)
  Wave 1: T1
  Wave 2: T2, T5 in parallel; T3 alone, behind a gate
  Wave 3: T4
Gate on T3: you confirm the legacy export has been archived outside the repository.
  T3 deletes data/legacy.csv; it cannot be recovered from the repository afterwards.
Branch: I will create ship/reorder-and-legacy-cleanup from main@6fce1fb. Working tree is clean.
Checks I will run: python3 -m unittest discover -s tests (and each task's own check).
How: one agent per task, T2 and T5 at the same time in separate worktrees, then one reviewer
  on the whole change.
```

Question: Start · Start, one task at a time · Show the task briefings and stop · Cancel

## Progress, one line at a time

```text
Baseline: python3 -m unittest discover -s tests → 3 passed.
T1 started.
T1 done (b23b91c). Verify: python3 -m unittest tests.test_reorder → 4 passed.
Gate on T3: has the legacy export been archived outside the repository?
```

Question on the gate, asked before the tasks beside it start: Yes, run T3 · No, do not run it

```text
T3 not run: you declined the gate. T4 depends on it and will not run.
T2 and T5 started in parallel.
T5 done (c7f8286). Verify: grep -c reorder_list README.md → 1.
T2 needs your decision: the card changes total([]) to return None, but tests/test_stock.py
  asserts it is 0, and the card does not own that test.
```

Question on T2: Add the test file to the card and update the test · Drop T2 · Leave it for now

```text
T2 left as it is, on your answer.
Suite on ship/reorder-and-legacy-cleanup → 7 passed.
```

## The report

```text
Built 2 of 5 tasks of "Reorder list, empty-total change, and legacy export removal" on branch
ship/reorder-and-legacy-cleanup (b23b91c..5a862cf). Incomplete: one task needs your decision
and you declined the gate on another.

Tasks
- T1 Reorder list: done (b23b91c). Verify: python3 -m unittest tests.test_reorder → 4 passed
- T2 Empty total returns None: needs your decision. The card contradicts tests/test_stock.py,
  which it does not own.
- T3 Delete the legacy export and its loader: not run. You declined its gate.
- T4 Remove the legacy export from the README: not run. Depends on T3.
- T5 Document the reorder list: done (c7f8286). Verify: grep -c reorder_list README.md → 1

Checks on the last task commit (c7f8286)
- python3 -m unittest discover -s tests → 7 passed (baseline: 3 passed)

Success criteria
- SC-1 reorder list: met. AC-1 by the test run, AC-4 by the grep.
- SC-2 explicit empty total: not met. T2 was not built.
- SC-3 legacy export removed: not met. T3 and T4 were not run.

Review
- Whole change reviewed by one independent reviewer, without sibling review skills (none
  installed). No blocking findings.

Left behind
- The repository has no ignore rule for __pycache__; test runs leave untracked caches.
```

The plan's `status` stays `active`, and its Status section records the same account.

Question: Keep the branch · Push and open a pull request · Show the diff · Discard the work
