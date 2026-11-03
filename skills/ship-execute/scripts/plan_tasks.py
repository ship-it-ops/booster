#!/usr/bin/env python3
"""
Read a ship-better-plans plan (plan_format: 2) for execution, so the executor
never has to parse a long plan by eye or keep run state in its head.

Usage (run from inside the repository):
  python3 plan_tasks.py <plan.md> summary              what the plan contains and whether it can be executed
  python3 plan_tasks.py <plan.md> preflight            the cards against the repository as it is now
  python3 plan_tasks.py <plan.md> next                 which tasks are ready now, given the run ledger
  python3 plan_tasks.py <plan.md> wave                 Workflow arguments for the ready parallel set
  python3 plan_tasks.py <plan.md> brief <Tn> [--out]   the exact briefing for one task agent
  python3 plan_tasks.py <plan.md> check <Tn> <commit|base..tip>   what was changed, against the card
  python3 plan_tasks.py <plan.md> approve <Tn> --note <the user's answer>   record that a gate was passed
  python3 plan_tasks.py <plan.md> mark <Tn> <state> [--commit <sha>] [--verified <text>] [--note <text>]
                                  [--branch <name>] [--worktree <path>]
  python3 plan_tasks.py <plan.md> set <key> <value>    record a fact about the run (branch, start, baseline, ...)
  python3 plan_tasks.py <plan.md> ledger               print the run ledger
  python3 plan_tasks.py <plan.md> cleanup <Tn>         remove the worktree and throwaway branch of a finished task
  python3 plan_tasks.py <plan.md> clear                delete the run ledger and saved briefings

  Add --json to summary, next and ledger for machine-readable output.
  Add --ledger <file> to choose where the ledger lives.

Task states: pending, running, done, blocked, needs-decision, declined, skipped.
A task is ready when every task it depends on is done. A task that depends,
directly or through a chain, on a task that is blocked, needs-decision,
declined or skipped is not runnable and is reported as such, never as ready.

The ledger refuses claims it can check. `mark <Tn> running` and `mark <Tn> done`
fail unless the task's dependencies are done, the run's recorded branch is
checked out, and, for a task with a gate, the gate was recorded with `approve`
for the card as it is now. An approval is used up when the task leaves
`running` for any state but `done`, so every dispatch of a gated task needs a
fresh yes. `mark <Tn> done` also needs --verified (the check you ran and its
result) and, for a task that changes files, a --commit made during this run
that is on the current branch.

The ledger is a small JSON file inside the repository's git directory
(<git-common-dir>/ship-execute/), so it is shared by every worktree, survives
a new session, and never shows up in `git status`. Briefings written with
--out go beside it, so a task agent in any worktree can read its own.

`check` fails when the change touches a test, a check or its configuration
that the card does not own, or commits caches, build output or environment
files the card does not own. It lists every other file outside the card so
the deviation is looked at instead of trusted.

Standard library only. Exit codes: 0 ok, 1 the plan cannot be executed as it
stands, a check failed or a claim was refused (see what is printed), 2 usage.
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

STATES = ("pending", "running", "done", "blocked", "needs-decision", "declined", "skipped")
STOPPED = ("blocked", "needs-decision", "declined", "skipped")
MAX_WAVE = 4  # more agents at once than this costs more in setup and review than it saves

H2 = re.compile(r"^##\s+(.+?)\s*$")
HEADING = re.compile(r"^#{1,6}\s")
TASK_HEADING = re.compile(r"^###\s+(T\d+[a-z]?)\b\s*(?:[—–:-]\s*)?(.*)$")
FIELD = re.compile(
    r"^\s*[-*]\s+\*{0,2}(Depends on|Covers|Files|Do|Verify|Kind|Size|Reversibility|Gate)"
    r"\*{0,2}\s*:\s*\*{0,2}\s*(.*)$",
    re.I,
)
INLINE_FIELD = re.compile(r"\*{0,2}(Kind|Size|Reversibility|Gate)\*{0,2}\s*:\s*\*{0,2}\s*([^·\n]+)", re.I)
ID_DEF = re.compile(r"^\s*(?:[-*]|\|)\s*\*{0,2}((?:SC|FR|AC)-\d+)\b")
ID_REF = re.compile(r"\b(?:SC|FR|AC)-\d+\b")
TASK_REF = re.compile(r"\bT\d+[a-z]?\b")
FILE_ENTRY = re.compile(r"`([^`\n]+)`(?:\s*\(([^)]*)\))?")
RULES = """\
RULES FOR THIS TASK
- You are one task in a larger plan. This briefing is everything you get: you will not see the rest of the plan.
- Work only in your current checkout. Before you start, run `pwd`, `git rev-parse --short HEAD` and `git status --short`, and include all three in your result.
- Change only the files listed as owned. If the task cannot be done without touching another file, touch it, and say which and why in your result.
- Do not edit, delete, skip or weaken an existing test, a check, or the configuration of either, to get a green result, unless that file is listed as owned.
- If the task contradicts an existing test, the conventions, or the code as it actually is, or if the verification cannot pass as written (the command does not exist, it needs something this task does not own, the expected result is impossible), stop, change nothing further, and return status "needs-decision" with the contradiction stated.
- Run the verification exactly as written, after your last change, and read its real output. Do not change the verification command. If it fails for a reason outside your files, say so; do not work around it.
- If it is red, find the cause before changing anything else. After three failed attempts, stop and return status "blocked" with the last output.
{commit_rule}
- Do not push, open a pull request, switch branches, or touch any other checkout. Do not run anything against a shared, staging or production system. Do not read or print the contents of environment or credential files.
- Your result must give: status (done, needs-decision or blocked), {result_fields}the branch (`git rev-parse --abbrev-ref HEAD`), the verification command you ran with its exit code and the last lines of its output, every file you changed, anything you did differently from the briefing, and your question if you have one.
"""

COMMIT_RULE = (
    "- When it is green, commit: `git add` each file you changed by path (never `git add -A` or `git add .`), then make "
    "one commit with a message that follows the conventions, or \"<task id>: <task title>\" if they give none. Do not "
    "commit build output, caches or environment files unless they are listed as owned. After committing, "
    "`git status --short` should show nothing you created."
)
NO_COMMIT_RULE = (
    "- THIS TASK CHANGES NO FILES. Do not commit anything. Put what you found in the `answer` field of your result, "
    "specific enough that someone who has not seen your work can act on it."
)


BOLD_ITEM = re.compile(r"^\s*[-*]\s+\*\*([^*:]+):?\*\*:?\s*(.*)$")


def mask_fences(lines: list[str]) -> list[str]:
    out, fence = [], None
    for line in lines:
        stripped = line.lstrip()
        marker = stripped[:3] if stripped[:3] in ("```", "~~~") else None
        if fence is None and marker:
            fence = marker
            out.append("")
        elif fence is not None:
            if marker == fence:
                fence = None
            out.append("")
        else:
            out.append(line)
    return out


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()


def parse(plan: Path) -> dict:
    raw = plan.read_text(encoding="utf-8").split("\n")
    lines = mask_fences(raw)

    meta: dict[str, str] = {}
    if raw and raw[0].strip() == "---":
        for line in raw[1:]:
            if line.strip() == "---":
                break
            key, sep, value = line.partition(":")
            if sep:
                meta[key.strip()] = value.strip()

    heads = [(i, H2.match(line).group(1).strip().lower()) for i, line in enumerate(lines) if H2.match(line)]
    sections = {}
    for n, (i, title) in enumerate(heads):
        sections[title] = (i + 1, heads[n + 1][0] if n + 1 < len(heads) else len(lines))

    def section(prefix: str):
        return next((span for title, span in sections.items() if title.startswith(prefix)), None)

    # Text of every SC / FR / AC, so a task's briefing can quote exactly the ids it covers.
    ids: dict[str, str] = {}
    current = None
    for line in lines:
        match = ID_DEF.match(line)
        if match:
            current = match.group(1)
            ids.setdefault(current, re.sub(r"^\s*[-*|]\s*", "", line).strip())
        elif current and line.startswith((" ", "\t")) and line.strip():
            ids[current] += " " + line.strip()
        else:
            current = None

    # Verification: the bold-labelled items (Setup, Commands, Baseline, Final check).
    verification: dict[str, str] = {}
    span = section("verification")
    if span:
        label = None
        for line in lines[span[0]:span[1]]:
            match = BOLD_ITEM.match(line)
            if match:
                label = match.group(1).strip().lower()
                verification[label] = match.group(2).strip()
            elif label and line.strip() and not line.lstrip().startswith("<!--"):
                verification[label] += " " + line.strip()

    tasks: dict[str, dict] = {}
    conventions = ""
    problems: list[str] = []
    span = section("tasks")
    if span:
        current_task, field, in_conventions, conv_lines = None, None, False, []
        for i in range(span[0], span[1]):
            line = lines[i]
            heading = TASK_HEADING.match(line)
            if heading:
                in_conventions = False
                if heading.group(1) in tasks:
                    problems.append(f"task id {heading.group(1)} is used twice")
                current_task = {"id": heading.group(1), "title": heading.group(2).strip(), "fields": {}}
                tasks[heading.group(1)] = current_task
                field = None
                continue
            if HEADING.match(line):
                current_task, field = None, None
                in_conventions = bool(re.match(r"^###\s+Conventions for every task", line, re.I))
                continue
            if in_conventions:
                conv_lines.append(raw[i])
                continue
            if current_task is None:
                continue
            match = FIELD.match(line)
            if match:
                field = match.group(1).lower()
                current_task["fields"][field] = match.group(2).strip()
            elif field and raw[i].strip():
                # Continuation lines come from the raw text, so fenced code inside Do or Verify is kept.
                current_task["fields"][field] += "\n" + raw[i].rstrip()
        conventions = strip_comments("\n".join(conv_lines))

    for tid, task in tasks.items():
        fields = {name: strip_comments(value) for name, value in task.pop("fields").items()}
        for name in ("kind", "size", "reversibility", "gate"):
            for key, value in INLINE_FIELD.findall(fields.get(name, "")):
                fields.setdefault(key.lower(), value.strip())
            if name in fields:
                fields[name] = fields[name].split("·")[0].strip()
        depends = fields.get("depends on", "").strip().rstrip(".")
        if re.fullmatch(r"(?i)none", depends) or not depends:
            task["depends_on"] = []
        elif re.fullmatch(r"T\d+[a-z]?(?:\s*,\s*T\d+[a-z]?)*", depends):
            task["depends_on"] = TASK_REF.findall(depends)
        else:
            task["depends_on"] = TASK_REF.findall(depends)
            problems.append(f"{tid}: 'Depends on' is not `none` or a list of task ids ('{depends}')")
        covers = fields.get("covers", "")
        task["covers"] = [] if re.match(r"(?i)\s*none\b", covers) else sorted(set(ID_REF.findall(covers)), key=lambda x: (x[:2], int(x.split("-")[1])))
        task["files"] = [{"path": p.strip(), "change": (n or "").strip()} for p, n in FILE_ENTRY.findall(fields.get("files", ""))]
        task["changes_files"] = bool(task["files"])
        task["do"] = fields.get("do", "").strip()
        task["verify"] = fields.get("verify", "").strip()
        task["kind"] = fields.get("kind", "").strip().lower()
        task["size"] = fields.get("size", "").strip()
        task["reversibility"] = fields.get("reversibility", "").strip()
        task["gate"] = fields.get("gate", "").strip()
        if "files" not in fields:
            problems.append(f"{tid}: the card has no 'Files' (write `none` for a task that changes no files)")
        if not task["reversibility"]:
            problems.append(f"{tid}: the card has no 'Reversibility', so it cannot be told whether it needs a gate")
        if not task["do"]:
            problems.append(f"{tid}: the card has no 'Do'")
        if not task["verify"]:
            problems.append(f"{tid}: the card has no 'Verify'")
        if task["reversibility"] and not re.match(r"(?i)\s*safe\b", task["reversibility"]) and not task["gate"]:
            problems.append(f"{tid}: reversibility is '{task['reversibility']}' but the card has no 'Gate'")
        for ref in task["covers"]:
            if ref not in ids:
                problems.append(f"{tid}: covers {ref}, which the plan does not define")
    for tid, task in tasks.items():
        for dep in task["depends_on"]:
            if dep not in tasks:
                problems.append(f"{tid}: depends on {dep}, which is not a task")
    if not tasks:
        problems.append("no task cards found (expected '### T1 — title' headings under '## Tasks'); this is not a plan_format 2 plan")
    cycle = find_cycle(tasks)
    if cycle:
        problems.append("dependency cycle: " + " → ".join(cycle))

    for task in tasks.values():
        blob = json.dumps([task["depends_on"], task["files"], task["do"], task["verify"], task["gate"]], sort_keys=True)
        task["card_hash"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]

    return {
        "plan": str(plan),
        "title": re.sub(r"^Plan:\s*", "", next((ln[2:].strip() for ln in raw if ln.startswith("# ")), plan.stem)),
        "approval": meta.get("approval", "").lower() or "not set",
        "base": meta.get("base", ""),
        "plan_format": meta.get("plan_format", ""),
        "conventions": conventions,
        "verification": verification,
        "ids": ids,
        "tasks": tasks,
        "problems": problems,
        "has_cycle": bool(cycle),
    }


def find_cycle(tasks: dict[str, dict]):
    state: dict[str, int] = {}

    def visit(tid: str, path: list[str]):
        state[tid] = 1
        for dep in tasks[tid]["depends_on"]:
            if dep not in tasks:
                continue
            if state.get(dep) == 1:
                return path[path.index(dep):] + [dep]
            if state.get(dep) is None:
                found = visit(dep, path + [dep])
                if found:
                    return found
        state[tid] = 2
        return None

    for tid in tasks:
        if state.get(tid) is None:
            found = visit(tid, [tid])
            if found:
                return found
    return None


def waves(tasks: dict[str, dict]) -> list[list[str]]:
    level: dict[str, int] = {}

    def depth(tid: str) -> int:
        if tid not in level:
            deps = [d for d in tasks[tid]["depends_on"] if d in tasks]
            level[tid] = 1 + max((depth(d) for d in deps), default=0)
        return level[tid]

    grouped: dict[int, list[str]] = {}
    for tid in tasks:
        grouped.setdefault(depth(tid), []).append(tid)
    return [grouped[n] for n in sorted(grouped)]


def overlap(a: dict, b: dict) -> list[str]:
    """Files two tasks both name. The planner's linter forbids this for unlinked tasks; check again, cheaply."""
    pa = {f["path"].rstrip("/") for f in a["files"]}
    pb = {f["path"].rstrip("/") for f in b["files"]}
    shared = pa & pb
    shared |= {x for x in pa for y in pb if x != y and (x.startswith(y + "/") or y.startswith(x + "/"))}
    return sorted(shared)


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


def git(*args: str, cwd=None) -> tuple[int, str]:
    try:
        done = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd, check=False)
        return done.returncode, (done.stdout or done.stderr).strip()
    except FileNotFoundError:
        return 127, "git not found"


def run_dir(plan: Path) -> Path:
    code, common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=plan.parent)
    if code != 0:
        return plan.parent / ".ship-execute"
    return Path(common) / "ship-execute"


def run_key(plan: Path) -> str:
    """The plan's name plus a short hash of its path, so two plans with the same file name do not share a ledger."""
    code, top = git("rev-parse", "--show-toplevel", cwd=plan.parent)
    try:
        rel = str(plan.resolve().relative_to(Path(top).resolve())) if code == 0 else str(plan)
    except ValueError:
        rel = str(plan)
    return f"{plan.stem}-{hashlib.sha256(rel.encode('utf-8')).hexdigest()[:8]}"


def default_ledger(plan: Path) -> Path:
    return run_dir(plan) / f"{run_key(plan)}.json"


class LedgerError(Exception):
    pass


def load_ledger(path: Path) -> dict:
    if not path.is_file():
        return {"run": {}, "tasks": {}}
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise LedgerError(f"the run ledger at {path} is not valid JSON ({error}); it was left untouched. "
                          f"Repair it, or delete it with `clear` and rebuild the state from the branch.") from error
    ledger.setdefault("run", {})
    ledger.setdefault("tasks", {})
    return ledger


def save_ledger(path: Path, ledger: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def state_of(ledger: dict, tid: str) -> str:
    return ledger["tasks"].get(tid, {}).get("state", "pending")


def compute_next(data: dict, ledger: dict) -> dict:
    tasks = data["tasks"]
    unreachable: dict[str, str] = {}

    def stopped_by(tid: str, seen: tuple[str, ...] = ()) -> str:
        for dep in tasks[tid]["depends_on"]:
            if dep not in tasks or dep in seen:
                continue
            if state_of(ledger, dep) in STOPPED:
                return dep
            deeper = stopped_by(dep, seen + (tid,))
            if deeper:
                return deeper
        return ""

    ready, waiting = [], []
    for tid in tasks:
        state = state_of(ledger, tid)
        if state != "pending":
            continue
        cause = stopped_by(tid)
        if cause:
            unreachable[tid] = cause
        elif all(state_of(ledger, d) == "done" for d in tasks[tid]["depends_on"] if d in tasks):
            ready.append(tid)
        else:
            waiting.append(tid)
    # A task that changes no files exists to answer a question, so it runs alone and everything waits for it.
    stopped_question = next((t for t in tasks if not tasks[t]["changes_files"] and state_of(ledger, t) in STOPPED), None)
    if stopped_question:
        for tid in ready + waiting:
            unreachable.setdefault(tid, stopped_question)
        ready, waiting = [], []
    question = next((t for t in ready if not tasks[t]["changes_files"] and not tasks[t]["gate"]), None)
    held_for_question = [t for t in ready if question and t != question]
    if question:
        ready = [question]
    gated = [t for t in ready if tasks[t]["gate"]]
    free = [t for t in ready if not tasks[t]["gate"]]
    # Ready tasks that name the same file must not run together, whatever the plan says.
    parallel: list[str] = []
    held: dict[str, str] = {}
    for tid in free:
        clash = next((other for other in parallel if overlap(tasks[tid], tasks[other])), None)
        if clash:
            held[tid] = clash
        elif len(parallel) >= MAX_WAVE:
            held[tid] = parallel[0]
        else:
            parallel.append(tid)
    for tid in held_for_question:
        held[tid] = question
    counts = {s: sum(1 for t in tasks if state_of(ledger, t) == s) for s in STATES}
    running = [t for t in tasks if state_of(ledger, t) == "running"]
    return {
        "ready": parallel,
        "ready_after": held,
        "gated": gated,
        "waiting": waiting,
        "running": running,
        "unreachable": unreachable,
        "counts": counts,
        "finished": not ready and not waiting and not running and not held,
        "all_done": counts["done"] == len(tasks),
    }


# ---------------------------------------------------------------------------
# Checking a task's commit against its card
# ---------------------------------------------------------------------------

TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs)(/|$)|(^|/)test_[^/]*$|[._-](test|spec)\.[A-Za-z0-9]+$|_test\.[A-Za-z0-9]+$")
CHECK_CONFIG = re.compile(
    r"(^|/)(\.github/workflows/|\.circleci/|\.husky/)"
    r"|(^|/)(Makefile|package\.json|pyproject\.toml|setup\.cfg|tox\.ini|pytest\.ini|noxfile\.py|conftest\.py"
    r"|\.coveragerc|lefthook\.yml|\.gitlab-ci\.yml|\.pre-commit-config\.yaml)$"
    r"|(^|/)(tsconfig[^/]*\.json|jest\.config\.[^/]+|vitest\.config\.[^/]+|\.eslintrc[^/]*|eslint\.config\.[^/]+"
    r"|\.markdownlint[^/]*|\.(eslint|prettier|stylelint)ignore)$"
)
JUNK = re.compile(
    r"(^|/)(__pycache__|node_modules|\.venv|dist|build|\.DS_Store)(/|$)|\.pyc$"
    r"|(^|/)\.env(\.(?!example$|sample$|template$)[^/]*)?$|\.pem$|(^|/)id_rsa"
)


def owns(task: dict, path: str) -> bool:
    for entry in task["files"]:
        owned = entry["path"].rstrip("/")
        if path == owned or path.startswith(owned + "/"):
            return True
        if any(ch in owned for ch in "*?[") and fnmatch.fnmatch(path, owned):
            return True
    return False


def check_commit(data: dict, tid: str, ref: str) -> tuple[list[str], list[str]]:
    """Return (failures, notes) for what a commit, or a base..tip range, changed relative to the task's card."""
    task = data["tasks"][tid]
    if ".." in ref:
        base, tip = ref.split("..", 1)
        code, out = git("diff", "--name-status", "--no-renames", base, tip)
    else:
        code, out = git("show", "--name-status", "--format=", "--no-renames", ref)
    if code != 0:
        return [f"cannot read {ref}: {out}"], []
    failures, notes = [], []
    changed = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changed.append((parts[0][:1], parts[-1]))
    if not changed:
        failures.append(f"{ref} changes no files")
    for status, path in changed:
        if owns(task, path):
            if JUNK.search(path):
                notes.append(f"{path}: looks like build output or an environment file, but the card owns it")
            continue
        if JUNK.search(path):
            failures.append(f"{path}: build output, cache, or environment/credential file committed")
        elif status in ("M", "D") and TEST_PATH.search(path):
            verb = "deletes" if status == "D" else "changes"
            failures.append(f"{path}: {verb} an existing test that the card does not own")
        elif CHECK_CONFIG.search(path):
            failures.append(f"{path}: changes a check or its configuration, which the card does not own")
        else:
            notes.append(f"{path}: {'added' if status == 'A' else 'deleted' if status == 'D' else 'changed'} outside the card's Files")
    touched = {path for _, path in changed}
    for entry in task["files"]:
        owned = entry["path"].rstrip("/")
        if not any(ch in owned for ch in "*?[") and not any(p == owned or p.startswith(owned + "/") for p in touched):
            notes.append(f"{owned}: listed in the card's Files but not changed")
    return failures, notes


def preflight(data: dict) -> tuple[list[str], list[str]]:
    """Compare the cards with the repository as it is now. Returns (problems, notes)."""
    problems, notes = [], []
    tasks = data["tasks"]
    code, top = git("rev-parse", "--show-toplevel")
    if code != 0:
        return ["not inside a git repository"], []
    root = Path(top)
    created = {}
    for tid, task in tasks.items():
        for entry in task["files"]:
            if re.match(r"\s*(new|create|add)", entry["change"].lower()):
                created.setdefault(entry["path"].rstrip("/"), []).append(tid)

    def ancestors(tid: str, seen=None) -> set:
        seen = seen or set()
        for dep in tasks[tid]["depends_on"]:
            if dep in tasks and dep not in seen:
                seen.add(dep)
                ancestors(dep, seen)
        return seen

    for tid, task in tasks.items():
        earlier = ancestors(tid)
        for entry in task["files"]:
            path, change = entry["path"].rstrip("/"), entry["change"].lower()
            if any(ch in path for ch in "*?["):
                continue
            exists = (root / path).exists()
            if re.match(r"\s*(modify|edit|update|delete|remove|move|rename)", change) and not exists:
                if not any(c in earlier for c in created.get(path, [])):
                    problems.append(f"{tid}: `{path}` is marked ({entry['change']}) but does not exist")
            elif re.match(r"\s*(new|create|add)", change) and exists:
                problems.append(f"{tid}: `{path}` is marked (new) but already exists")
    base = data["base"].split("@", 1)[-1].strip()
    if not base:
        notes.append("the plan records no base commit, so it cannot be compared with the repository")
    else:
        code, out = git("diff", "--name-only", f"{base}..HEAD")
        if code != 0:
            notes.append(f"the plan's base `{data['base']}` is not a commit in this repository; the plan may have been written elsewhere")
        else:
            moved = set(out.splitlines())
            for tid, task in tasks.items():
                hit = sorted(p for p in moved if owns(task, p))
                if hit:
                    notes.append(f"{tid}: changed since the plan's base ({base}): {', '.join(hit)}")
    return problems, notes


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def gate_passed(data: dict, ledger: dict, tid: str) -> dict:
    """The recorded approval for a gated task, if it was given for the card as it is now."""
    approval = ledger["tasks"].get(tid, {}).get("gate_approved") or {}
    return approval if approval.get("card_hash") == data["tasks"][tid]["card_hash"] else {}


def brief(data: dict, tid: str, ledger=None) -> str:
    task = data["tasks"][tid]
    out = [f"TASK {tid} — {task['title']}", f"(part of the plan: {data['title']})", ""]
    if task["gate"]:
        # The parallel-wave script refuses any briefing that carries a line starting "GATE".
        approval = gate_passed(data, ledger, tid) if ledger else {}
        if approval:
            out += [f"GATE (passed): {task['gate']}", f"The user confirmed it on {approval['at'][:10]}: \"{approval['answer']}\". This task runs alone.", ""]
        else:
            out += [f"GATE (not yet confirmed): {task['gate']}", "This briefing is a preview. It must not be given to a task agent until the user has passed the gate.", ""]
    if task["reversibility"] and not re.match(r"(?i)\s*safe\b", task["reversibility"]):
        out += [f"WHAT CANNOT BE UNDONE: {task['reversibility']}", ""]
    out += ["WHAT TO DO", task["do"], ""]
    if task["files"]:
        out.append("FILES THIS TASK OWNS")
        out += [f"- {f['path']}" + (f" ({f['change']})" if f["change"] else "") for f in task["files"]]
        out.append("")
    if task["covers"]:
        out.append("WHAT THIS TASK CONTRIBUTES TO")
        out.append("(The plan's own words. Where WHAT TO DO delivers only part of one, do only that part. The only check you run is the one under HOW IT IS VERIFIED.)")
        out += [f"- {data['ids'][ref]}" for ref in task["covers"] if ref in data["ids"]]
        out.append("")
    out += ["HOW IT IS VERIFIED", task["verify"], ""]
    if data["conventions"]:
        out += ["CONVENTIONS FOR EVERY TASK", data["conventions"], ""]
    setup = data["verification"].get("setup", "")
    if setup:
        out += ["SETUP FOR A FRESH CHECKOUT", setup, ""]
    rules = RULES.format(
        commit_rule=COMMIT_RULE if task["changes_files"] else NO_COMMIT_RULE,
        result_fields="the commit sha, " if task["changes_files"] else "your answer, ",
    )
    out.append(rules.rstrip())
    return "\n".join(out).rstrip() + "\n"


def write_brief(data: dict, tid: str, plan: Path, ledger=None) -> Path:
    target = run_dir(plan) / run_key(plan) / f"{tid}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(brief(data, tid, ledger), encoding="utf-8")
    return target


def worktrees() -> dict[str, str]:
    """Map each linked worktree path to its branch (the main worktree is left out)."""
    code, out = git("worktree", "list", "--porcelain")
    found, path, first = {}, None, True
    for line in out.splitlines() if code == 0 else []:
        if line.startswith("worktree "):
            path = None if first else line[len("worktree "):]
            first = False
        elif line.startswith("branch ") and path:
            found[path] = line[len("branch "):].replace("refs/heads/", "")
    return found


def protected_branches(ledger: dict) -> set:
    names = {ledger["run"].get("branch", ""), ledger["run"].get("origin", ""), "main", "master"}
    return {n for n in names if n}


def on_run_branch(ledger: dict) -> str:
    """Empty when the run's recorded branch is checked out (or none is recorded); otherwise why not."""
    wanted = ledger["run"].get("branch")
    if not wanted:
        return ""
    code, current = git("rev-parse", "--abbrev-ref", "HEAD")
    if code == 0 and current != wanted:
        return f"the run is on branch `{wanted}` but `{current}` is checked out; switch back before continuing"
    return ""


def print_summary(data: dict) -> None:
    tasks = data["tasks"]
    print(f"Plan: {data['title']}")
    print(f"Approval: {data['approval']} · base: {data['base'] or 'not recorded'} · format: {data['plan_format'] or 'not recorded'}")
    if tasks and not data["has_cycle"]:
        for n, wave in enumerate(waves(tasks), 1):
            notes = []
            if len(wave) > 1:
                notes.append("independent")
            gated = [t for t in wave if tasks[t]["gate"]]
            if gated:
                notes.append("gated: " + ", ".join(gated))
            print(f"Wave {n}: {', '.join(wave)}" + (f"  ({'; '.join(notes)})" if notes else ""))
    for tid, task in tasks.items():
        deps = ", ".join(task["depends_on"]) or "none"
        print(f"- {tid} [{task['kind'] or 'kind?'} · {task['size'] or '?'}] {task['title']} — depends on: {deps}" + ("  — GATE" if task["gate"] else ""))
        if task["gate"]:
            print(f"    gate: {task['gate']}")
        print("    verify: " + task["verify"].replace("\n", "\n            "))
    review = [t for t in tasks if tasks[t]["kind"] in ("security", "migration", "infra")]
    print(f"Agents: {len(tasks)} task agent(s)" + (f", {len(review)} task review(s) ({', '.join(review)})" if review else "") + ", 1 review of the whole change")
    for label in ("setup", "commands", "baseline", "final check"):
        if data["verification"].get(label):
            print(f"{label.capitalize()}: {data['verification'][label]}")
    if data["problems"]:
        print("\nProblems that stop execution:")
        for problem in data["problems"]:
            print(f"  - {problem}")


def print_next(data: dict, result: dict) -> None:
    tasks = data["tasks"]
    counts = ", ".join(f"{n} {s}" for s, n in result["counts"].items() if n)
    print(f"Ledger: {counts or 'empty'}")
    if result["running"]:
        print("Marked running (finish or reset these first): " + ", ".join(result["running"]))
    if result["ready"]:
        how = "can run in parallel" if len(result["ready"]) > 1 else "run it"
        print(f"Ready ({how}): " + ", ".join(result["ready"]))
    for tid, other in result["ready_after"].items():
        print(f"Ready after {other} (same file, a full wave, or a question that must be answered first): {tid}")
    for tid in result["gated"]:
        print(f"Ready, behind a gate (ask the user, run alone): {tid} — {tasks[tid]['gate']}")
    for tid, cause in result["unreachable"].items():
        print(f"Not runnable: {tid} depends on {cause}, which is {state_of_from(result, cause)}")
    if result["waiting"]:
        print("Waiting on earlier tasks: " + ", ".join(result["waiting"]))
    if result["finished"]:
        print("Nothing left to run: " + ("every task is done." if result["all_done"] else "some tasks did not complete; report them."))


def state_of_from(result: dict, tid: str) -> str:
    return result.get("_states", {}).get(tid, "stopped")


def changed_cards(data: dict, ledger: dict) -> list[str]:
    """Tasks whose card was edited after the ledger recorded them, or ledger entries with no card."""
    out = []
    for tid, entry in ledger["tasks"].items():
        if tid not in data["tasks"]:
            out.append(f"{tid}: in the ledger but no longer in the plan")
        elif entry.get("card_hash") and entry["card_hash"] != data["tasks"][tid]["card_hash"] and entry.get("state") in ("running", "done"):
            out.append(f"{tid}: its card changed after it was marked {entry['state']}")
    return out


def refuse(message: str) -> int:
    print(f"REFUSED  {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Read a ship-better-plans plan for execution")
    parser.add_argument("plan", type=Path)
    parser.add_argument("command", choices=("summary", "preflight", "next", "wave", "brief", "check", "approve", "mark", "set", "ledger", "cleanup", "clear"))
    parser.add_argument("task", nargs="?")
    parser.add_argument("state", nargs="?")
    parser.add_argument("--commit", default="")
    parser.add_argument("--verified", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--worktree", default="")
    parser.add_argument("--out", action="store_true", help="brief: write the briefing to a file and print its path")
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.plan.is_file():
        print(f"plan_tasks: {args.plan} is not a file", file=sys.stderr)
        return 2
    plan = args.plan.resolve()
    data = parse(plan)
    tasks = data["tasks"]
    ledger_path = args.ledger or default_ledger(plan)

    if args.command == "summary":
        if args.json:
            out = {k: v for k, v in data.items() if k != "has_cycle"}
            out["waves"] = waves(tasks) if tasks and not data["has_cycle"] else []
            out["ledger"] = str(ledger_path)
            print(json.dumps(out, indent=2))
        else:
            print_summary(data)
            print(f"Ledger file: {ledger_path}")
        return 1 if data["problems"] else 0

    if args.command == "preflight":
        problems, notes = preflight(data)
        for line in problems:
            print(f"PROBLEM  {line}")
        for line in notes:
            print(f"NOTE     {line}")
        if not problems and not notes:
            print("OK       the cards match the repository, and nothing they name has changed since the plan's base")
        return 1 if problems else 0

    if args.command == "brief":
        if args.task not in tasks:
            print(f"plan_tasks: no task '{args.task}' in this plan (tasks: {', '.join(tasks) or 'none'})", file=sys.stderr)
            return 2
        try:
            current = load_ledger(ledger_path)
        except LedgerError as error:
            print(f"plan_tasks: {error}", file=sys.stderr)
            return 1
        if args.out:
            if tasks[args.task]["gate"] and not gate_passed(data, current, args.task):
                return refuse(f"{args.task} has a gate that has not been passed, so its briefing cannot be handed to an agent. "
                              f"Ask the user, then record the answer with `approve`.")
            print(write_brief(data, args.task, plan, current))
        else:
            print(brief(data, args.task, current), end="")
        return 0

    if args.command == "check":
        if args.task not in tasks or not args.state:
            print("plan_tasks: usage: check <task id> <commit | base..tip>", file=sys.stderr)
            return 2
        if not tasks[args.task]["changes_files"]:
            print(f"OK    {args.task}: the card changes no files, so there is no commit to check")
            return 0
        failures, notes = check_commit(data, args.task, args.state)
        for line in failures:
            print(f"FAIL  {line}")
        for line in notes:
            print(f"NOTE  {line}")
        if not failures and not notes:
            print(f"OK    {args.task}: the change touches exactly the files the card owns")
        return 1 if failures else 0

    if args.command == "clear":
        briefs = run_dir(plan) / run_key(plan)
        removed = []
        if ledger_path.is_file():
            ledger_path.unlink()
            removed.append(str(ledger_path))
        if briefs.is_dir():
            shutil.rmtree(briefs)
            removed.append(str(briefs))
        print("Removed: " + (", ".join(removed) if removed else "nothing (no ledger for this plan)"))
        return 0

    try:
        ledger = load_ledger(ledger_path)
    except LedgerError as error:
        print(f"plan_tasks: {error}", file=sys.stderr)
        return 1

    def deps_done(tid: str) -> list[str]:
        return [d for d in tasks[tid]["depends_on"] if d in tasks and state_of(ledger, d) != "done"]

    if args.command == "approve":
        if args.task not in tasks:
            print("plan_tasks: usage: approve <task id> --note <the user's answer>", file=sys.stderr)
            return 2
        if not tasks[args.task]["gate"]:
            return refuse(f"{args.task} has no gate to approve")
        if not args.note:
            return refuse("give --note with the user's answer; a gate is passed by the user, not by the executor")
        entry = ledger["tasks"].setdefault(args.task, {})
        entry["gate_approved"] = {"at": now(), "answer": args.note, "card_hash": tasks[args.task]["card_hash"], "gate": tasks[args.task]["gate"]}
        save_ledger(ledger_path, ledger)
        print(f"{args.task}: gate recorded as passed")
        return 0

    if args.command == "mark":
        if args.task not in tasks or args.state not in STATES:
            print(f"plan_tasks: usage: mark <task id> <{'|'.join(STATES)}>", file=sys.stderr)
            return 2
        task = tasks[args.task]
        entry = ledger["tasks"].setdefault(args.task, {})
        if args.state in ("running", "done"):
            waiting = deps_done(args.task)
            if waiting:
                return refuse(f"{args.task} depends on {', '.join(waiting)}, which {'is' if len(waiting) == 1 else 'are'} not done")
            if task["gate"] and not gate_passed(data, ledger, args.task):
                why = "its card changed since the gate was passed" if entry.get("gate_approved") else "its gate has not been passed"
                return refuse(f"{args.task}: {why}. Ask the user, then record the answer with `approve`.")
            off_branch = on_run_branch(ledger)
            if off_branch:
                return refuse(off_branch)
        if args.worktree or args.branch:
            linked = worktrees()
            if args.worktree and args.worktree not in linked:
                return refuse(f"{args.worktree} is not a linked worktree of this repository (see `git worktree list`)")
            if args.branch and args.branch in protected_branches(ledger):
                return refuse(f"`{args.branch}` is the run's own branch or a main branch, not a task's throwaway branch")
            if args.worktree and args.branch and linked[args.worktree] != args.branch:
                return refuse(f"{args.worktree} is on branch `{linked[args.worktree]}`, not `{args.branch}`")
        if args.state == "done":
            if not args.verified:
                return refuse("give --verified with the check you ran on the execution branch and its result")
            if task["changes_files"]:
                if not args.commit:
                    return refuse(f"{args.task} changes files, so `done` needs --commit with its commit on the execution branch")
                if git("cat-file", "-e", f"{args.commit}^{{commit}}")[0] != 0:
                    return refuse(f"commit {args.commit} does not exist in this repository")
                if git("merge-base", "--is-ancestor", args.commit, "HEAD")[0] != 0:
                    return refuse(f"commit {args.commit} is not on the current branch; use the sha the cherry-pick created")
                start = ledger["run"].get("start")
                if start and git("merge-base", "--is-ancestor", args.commit, start)[0] == 0:
                    return refuse(f"commit {args.commit} was already there when the run started ({start}); it is not this task's work")
        if args.state != "done" and args.state != "running":
            entry.pop("gate_approved", None)  # a gate is passed for one dispatch, not for good
        entry["state"] = args.state
        entry["at"] = now()
        entry["card_hash"] = task["card_hash"]
        for key, value in (("commit", args.commit), ("verified", args.verified), ("note", args.note),
                           ("branch", args.branch), ("worktree", args.worktree)):
            if value:
                entry[key] = value
        ledger["plan"] = data["plan"]
        save_ledger(ledger_path, ledger)
        print(f"{args.task}: {args.state}" + (f" ({args.commit})" if args.commit else ""))
        return 0

    if args.command == "cleanup":
        if args.task not in tasks:
            print("plan_tasks: usage: cleanup <task id>", file=sys.stderr)
            return 2
        entry = ledger["tasks"].get(args.task, {})
        path, branch = entry.get("worktree", ""), entry.get("branch", "")
        if entry.get("state") != "done":
            return refuse(f"{args.task} is not done; its worktree may hold the only copy of its work. Nothing was removed.")
        if not path:
            print(f"{args.task}: no worktree recorded; nothing to remove")
            return 0
        linked = worktrees()
        if path not in linked:
            print(f"{args.task}: {path} is no longer a worktree; nothing to remove")
        elif "/.claude/worktrees/" not in path.replace(os.sep, "/"):
            return refuse(f"{path} is not under .claude/worktrees/, so this run did not create it. Remove it yourself if it is yours.")
        elif linked[path] in protected_branches(ledger) or (branch and linked[path] != branch):
            return refuse(f"{path} is on branch `{linked[path]}`, which is not the throwaway branch recorded for {args.task}")
        else:
            branch = linked[path]
            code, out = git("worktree", "remove", "--force", path)
            if code != 0:
                return refuse(f"could not remove {path}: {out}")
            git("branch", "-D", branch)
            print(f"{args.task}: removed worktree {path} and branch {branch}")
        entry.pop("worktree", None)
        entry.pop("branch", None)
        save_ledger(ledger_path, ledger)
        return 0

    if args.command == "set":
        if not args.task or args.state is None:
            print("plan_tasks: usage: set <key> <value>", file=sys.stderr)
            return 2
        ledger["run"][args.task] = args.state
        ledger["plan"] = data["plan"]
        save_ledger(ledger_path, ledger)
        print(f"{args.task} = {args.state}")
        return 0

    if args.command == "ledger":
        if args.json:
            print(json.dumps(ledger, indent=2))
        else:
            for key, value in ledger["run"].items():
                print(f"{key}: {value}")
            for tid in tasks:
                entry = ledger["tasks"].get(tid, {})
                extra = " · ".join(
                    f"{label}{entry[key]}" for key, label in (("commit", ""), ("verified", "verified: "), ("worktree", "worktree: "),
                                                              ("branch", "branch: "), ("note", "note: ")) if entry.get(key))
                gate = " · gate passed" if entry.get("gate_approved") else ""
                print(f"{tid}: {entry.get('state', 'pending')}" + (f" — {extra}" if extra else "") + gate)
            for line in changed_cards(data, ledger):
                print(f"WARNING  {line}")
            print(f"Ledger file: {ledger_path}")
        return 0

    # next, wave
    if data["problems"]:
        print("plan_tasks: the plan has problems that stop execution; run `summary`.", file=sys.stderr)
        return 1
    result = compute_next(data, ledger)

    if args.command == "wave":
        off_branch = on_run_branch(ledger)
        if off_branch:
            return refuse(off_branch)
        if len(result["ready"]) < 2:
            print("plan_tasks: fewer than two tasks are ready to run together; dispatch the ready task on its own.", file=sys.stderr)
            return 1
        code, head = git("rev-parse", "--short", "HEAD")
        print(json.dumps({
            "startCommit": head if code == 0 else "",
            "tasks": [{"id": tid, "briefPath": str(write_brief(data, tid, plan, ledger)), "noCommit": not tasks[tid]["changes_files"]}
                      for tid in result["ready"]],
        }, indent=2))
        return 0

    result["changed_cards"] = changed_cards(data, ledger)
    result["_states"] = {tid: state_of(ledger, tid) for tid in tasks}
    if args.json:
        result.pop("_states")
        print(json.dumps(result, indent=2))
    else:
        print_next(data, result)
        for line in result["changed_cards"]:
            print(f"WARNING  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
