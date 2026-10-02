#!/usr/bin/env python3
"""
Lint a ship-better-plans plan file: the mechanical checks a model should not
be trusted to do by eye on a long document.

Usage:
  python3 lint_plan.py <plan.md> [--repo <root>] [--no-paths] [--revising]
  python3 lint_plan.py <plan.md> --dag

Checks (errors fail the run; warnings are for the planner to fix or justify):

  STRUCTURE     required sections present and non-empty; no placeholders or
                template comments standing in for content; approval state
  TRACEABILITY  every success criterion is carried by a requirement, an
                acceptance criterion, a task or the final check; every FR has
                an AC and a task; every AC has an owner; no undefined ids
  TASKS         every card has Depends on / Covers / Files / Do / Verify /
                Reversibility; dependencies parse, exist and are acyclic; a
                task that is not `safe` to reverse names its Gate; the pasted
                execution order matches the cards
  PARALLEL      two tasks whose files overlap (same path, a directory and a
                file under it, or a glob) must be ordered by a dependency
  GROUNDING     files marked (modify)/(delete) exist; files marked (new) do
                not; `path:line` evidence points at a real, non-blank line;
                paths and package scripts named in Do / Verify exist

--dag prints the execution order computed from the task cards (a Mermaid
graph, parallel waves and the critical path; one line for a sequential plan),
so the order in the plan is derived, never hand-drawn.

--revising is for a plan that has been partly executed: files marked (new)
are allowed to exist already.

Standard library only. Exit codes: 0 clean (warnings allowed), 1 errors, 2 usage.
"""

from __future__ import annotations

import argparse
import fnmatch
import glob as globlib
import json
import posixpath
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("Summary", ("summary",)),
    ("Context", ("context",)),
    ("Success criteria", ("success criteria",)),
    ("Non-goals", ("non-goals", "non goals")),
    ("Constraints", ("constraints",)),
    ("Facts and assumptions", ("facts",)),
    ("Approach", ("approach",)),
    ("Risks and rollback", ("risks",)),
    ("Specification", ("specification",)),
    ("Verification", ("verification",)),
    ("Tasks", ("tasks",)),
    ("Open questions", ("open questions",)),
    ("Audit", ("audit",)),
    ("Status", ("status",)),
]
REQUIRED_TASK_FIELDS = ("depends on", "covers", "files", "do", "verify", "reversibility")
KINDS = {"code", "test", "docs", "config", "infra", "migration", "security"}
EXTENSIONLESS = {"Makefile", "Dockerfile", "Procfile", "Gemfile", "Rakefile", "Justfile", "Jenkinsfile"}

H2 = re.compile(r"^##\s+(.+?)\s*$")
HEADING = re.compile(r"^#{1,6}\s")
TASK_HEADING = re.compile(r"^###\s+(T\d+[a-z]?)\b\s*(?:[—–:-]\s*)?(.*)$")
FIELD = re.compile(
    r"^\s*[-*]\s+\*{0,2}(Depends on|Covers|Files|Do|Verify|Kind|Size|Reversibility|Gate)"
    r"\*{0,2}\s*:\s*\*{0,2}\s*(.*)$",
    re.I,
)
INLINE_FIELD = re.compile(r"\*{0,2}(Kind|Size|Reversibility|Gate)\*{0,2}\s*:\s*\*{0,2}\s*([^·\n]+)", re.I)
ID_DEF = re.compile(r"^\s*(?:[-*]|\|)\s*\*{0,2}((?:SC|FR|AC|OQ)-\d+)\b")
NOTE_DEF = re.compile(r"^\s*[-*]\s*\*{0,2}([FA]-\d+)\b")
ID_REF = re.compile(r"\b(?:SC|FR|AC|OQ)-\d+\b")
TASK_REF = re.compile(r"\bT\d+[a-z]?\b")
DEPENDS = re.compile(r"T\d+[a-z]?(?:\s*,\s*T\d+[a-z]?)*")
FILE_ENTRY = re.compile(r"`([^`\n]+)`(?:\s*\(([^)]*)\))?")
EVIDENCE = re.compile(r"`([\w./@+-]+):(\d+)(?:-\d+)?`")
PATH_TOKEN = re.compile(r"`((?:[\w@.+-]+/)+[\w@+-]+\.[A-Za-z0-9]{1,6})(?::\d+(?:-\d+)?)?`")
RUN_SCRIPT = re.compile(r"\b(?:npm|pnpm|yarn)\s+run\s+([\w:.-]+)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
ANYWHERE_PLACEHOLDERS = (
    (re.compile(r"\bTBD\b"), "TBD"),
    (re.compile(r"\?\?\?"), "???"),
    (re.compile(r"\{(?:title|task title)\}"), "{title}"),
    (re.compile(r"YYYY-MM-DD"), "YYYY-MM-DD"),
    (re.compile(r"<(?:branch|short-sha|agent-id)>"), "<template placeholder>"),
)
WHOLE_VALUE_PLACEHOLDER = re.compile(r"(?:TODO|TBD|…|\.\.\.)[.:]?")
NEW_WORDS = ("new", "create", "created", "add", "added")
EXISTING_WORDS = ("modify", "modified", "edit", "update", "delete", "remove", "move", "rename")
ORDER_LINE = re.compile(r"-->|^- (?:Wave \d+|Critical path|Sequential):|^T\d+[a-z]?\[")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, category: str, message: str) -> None:
        self.errors.append(f"[{category}] {message}")

    def warn(self, category: str, message: str) -> None:
        self.warnings.append(f"[{category}] {message}")


def mask_fences(lines: list[str]) -> list[str]:
    """Blank out fenced code blocks so their contents are not parsed as plan structure."""
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


def frontmatter(raw: list[str]) -> dict[str, str]:
    if not raw or raw[0].strip() != "---":
        return {}
    out = {}
    for line in raw[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep:
            out[key.strip()] = value.strip()
    return out


def split_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Map lower-cased H2 title -> (first body line, end line) as indexes into lines."""
    heads = [(i, H2.match(line).group(1)) for i, line in enumerate(lines) if H2.match(line)]
    sections = {}
    for n, (i, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        sections[title.strip().lower()] = (i + 1, end)
    return sections


def find_section(sections: dict, aliases: tuple[str, ...]):
    for title, span in sections.items():
        if any(title.startswith(alias) for alias in aliases):
            return span
    return None


def body_text(lines: list[str], span: tuple[int, int]) -> str:
    """Section text without headings and HTML comments (template guidance is not content)."""
    kept = [ln for ln in lines[span[0]:span[1]] if not HEADING.match(ln)]
    return re.sub(r"<!--.*?-->", "", "\n".join(kept), flags=re.S).strip()


def placeholder_cells(line: str) -> list[str]:
    """The values on a line that could be a bare placeholder: table cells, or a list item's value."""
    stripped = line.strip()
    if stripped.startswith("|"):
        return [cell.strip() for cell in stripped.strip("|").split("|")]
    item = re.sub(r"^[-*]\s+", "", stripped)
    values = [item]
    if ":" in item:
        values.append(item.rsplit(":", 1)[1])
    return [v.strip().strip("*").strip() for v in values]


def kind_of(note: str) -> str:
    first = re.match(r"\s*([a-z]+)", note)
    word = first.group(1) if first else ""
    if word in NEW_WORDS:
        return "new"
    if word in EXISTING_WORDS:
        return "existing"
    return "unknown"


def normalise(path: str) -> str:
    return posixpath.normpath(path) + ("/" if path.endswith("/") else "")


def is_glob(path: str) -> bool:
    return any(ch in path for ch in "*?[")


def overlaps(a: str, b: str) -> bool:
    """True when two Files entries can name the same file: equal, directory/child, or glob."""
    if a == b:
        return True
    for x, y in ((a, b), (b, a)):
        if is_glob(x):
            static = re.split(r"[*?\[]", x, maxsplit=1)[0]
            if fnmatch.fnmatch(y, x) or (is_glob(y) and y.startswith(static)):
                return True
        elif y.startswith(x.rstrip("/") + "/"):
            return True
    return False


def parse_tasks(lines: list[str], span: tuple[int, int], report: Report) -> dict[str, dict]:
    tasks: dict[str, dict] = {}
    current, field = None, None
    for i in range(span[0], span[1]):
        line = lines[i]
        heading = TASK_HEADING.match(line)
        if heading:
            if heading.group(1) in tasks:
                report.error("TASKS", f"line {i + 1}: task id {heading.group(1)} is used twice")
            current = {"title": heading.group(2).strip(), "line": i + 1, "fields": {}}
            tasks[heading.group(1)] = current
            field = None
            continue
        if HEADING.match(line):
            current, field = None, None
            continue
        if current is None:
            continue
        match = FIELD.match(line)
        if match:
            field = match.group(1).lower()
            current["fields"][field] = match.group(2).strip()
        elif field and line.strip():
            current["fields"][field] += "\n" + line.strip()
    for tid, task in tasks.items():
        fields = task["fields"]
        for name in ("kind", "size", "reversibility", "gate"):
            for key, value in INLINE_FIELD.findall(fields.get(name, "")):
                fields.setdefault(key.lower(), value.strip())
            if name in fields:
                fields[name] = fields[name].split("·")[0].strip()
        depends = fields.get("depends on", "").strip().rstrip(".")
        if depends and not re.fullmatch(r"(?i)none", depends) and not DEPENDS.fullmatch(depends):
            report.error(
                "TASKS",
                f"{tid}: 'Depends on' must be `none` or task ids separated by commas (got '{depends}'); "
                f"anything else would be read as no dependency",
            )
        task["deps"] = [] if re.fullmatch(r"(?i)none", depends) else TASK_REF.findall(depends)
        covers = fields.get("covers", "")
        task["covers"] = set() if re.match(r"(?i)\s*none\b", covers) else set(ID_REF.findall(covers))
        task["files"] = {}
        for path, note in FILE_ENTRY.findall(fields.get("files", "")):
            task["files"][normalise(path.strip())] = (note or "").strip().lower()
    return tasks


def ancestors(tasks: dict[str, dict]) -> dict[str, set[str]]:
    memo: dict[str, set[str]] = {}

    def walk(tid: str, stack: tuple[str, ...]) -> set[str]:
        if tid in memo:
            return memo[tid]
        found: set[str] = set()
        for dep in tasks[tid]["deps"]:
            if dep in tasks and dep not in stack:
                found.add(dep)
                found |= walk(dep, stack + (tid,))
        memo[tid] = found
        return found

    for tid in tasks:
        walk(tid, ())
    return memo


def find_cycle(tasks: dict[str, dict]):
    state: dict[str, int] = {}

    def visit(tid: str, path: list[str]):
        state[tid] = 1
        for dep in tasks[tid]["deps"]:
            if dep not in tasks:
                continue
            if state.get(dep) == 1:
                return path[path.index(dep):] + [dep] if dep in path else [tid, dep]
            if state.get(dep) is None:
                cycle = visit(dep, path + [dep])
                if cycle:
                    return cycle
        state[tid] = 2
        return None

    for tid in tasks:
        if state.get(tid) is None:
            cycle = visit(tid, [tid])
            if cycle:
                return cycle
    return None


def levels(tasks: dict[str, dict]) -> dict[str, int]:
    memo: dict[str, int] = {}

    def level(tid: str) -> int:
        if tid not in memo:
            deps = [d for d in tasks[tid]["deps"] if d in tasks]
            memo[tid] = 1 + max((level(d) for d in deps), default=0)
        return memo[tid]

    for tid in tasks:
        level(tid)
    return memo


def emit_dag(tasks: dict[str, dict]) -> str:
    lvl = levels(tasks)
    waves: dict[int, list[str]] = {}
    for tid in tasks:
        waves.setdefault(lvl[tid], []).append(tid)
    if all(len(members) == 1 for members in waves.values()):
        return "- Sequential: " + " → ".join(waves[n][0] for n in sorted(waves))
    out = ["```mermaid", "graph TD"]
    for tid, task in tasks.items():
        label = f"{tid}: {task['title']}".replace('"', "'")
        out.append(f'  {tid}["{label}"]')
    for tid, task in tasks.items():
        for dep in task["deps"]:
            if dep in tasks:
                out.append(f"  {dep} --> {tid}")
    out.append("```")
    for n in sorted(waves):
        gated = [t for t in waves[n] if tasks[t]["fields"].get("gate", "").strip()]
        free = len(waves[n]) - len(gated)
        note = " (can run in parallel)" if free > 1 else ""
        if gated and len(waves[n]) > 1:
            note += f" ({', '.join(gated)} waits for its gate and runs alone)"
        out.append(f"- Wave {n}: {', '.join(waves[n])}{note}")
    path, tid = [], max(lvl, key=lvl.get)
    while tid:
        path.append(tid)
        deps = [d for d in tasks[tid]["deps"] if d in tasks]
        tid = max(deps, key=lvl.get) if deps else None
    out.append("- Critical path: " + " → ".join(reversed(path)))
    return "\n".join(out)


def order_lines(text_lines: list[str]) -> list[str]:
    return [ln.strip() for ln in text_lines if ORDER_LINE.search(ln.strip())]


def package_scripts(repo: Path):
    manifest = repo / "package.json"
    if not manifest.is_file():
        return None
    try:
        return set(json.loads(manifest.read_text(encoding="utf-8")).get("scripts", {}))
    except (ValueError, OSError):
        return None


def lint(plan: Path, repo: Path, check_paths: bool, revising: bool, report: Report) -> tuple[dict[str, dict], str]:
    raw = plan.read_text(encoding="utf-8").split("\n")
    lines = mask_fences(raw)
    prose = [INLINE_CODE.sub(lambda m: " " * len(m.group(0)), ln) for ln in lines]
    sections = split_sections(lines)
    meta = frontmatter(raw)
    approval = meta.get("approval", "").lower()

    # STRUCTURE
    for name, aliases in REQUIRED_SECTIONS:
        span = find_section(sections, aliases)
        if span is None:
            report.error("STRUCTURE", f"missing required section '## {name}'")
            continue
        body = body_text(lines, span)
        has_fenced_content = any(raw[i].strip() and not lines[i].strip() for i in range(span[0], span[1]))
        if not body and not has_fenced_content:
            report.error("STRUCTURE", f"section '## {name}' is empty (write the content, or 'N/A — <reason>')")
        elif re.fullmatch(r"(?i)n/?a\.?", body):
            report.warn("STRUCTURE", f"section '## {name}' says N/A without a reason")
    for i, line in enumerate(prose):
        if re.match(r"\s*[-*]\s+\*{0,2}Request\b", line):
            continue
        for pattern, label in ANYWHERE_PLACEHOLDERS:
            if pattern.search(line):
                report.error("STRUCTURE", f"line {i + 1}: placeholder {label} left in the plan")
        if line.strip() and any(WHOLE_VALUE_PLACEHOLDER.fullmatch(cell) for cell in placeholder_cells(line)):
            report.error("STRUCTURE", f"line {i + 1}: unfilled value ('…' or TODO) left in the plan")
    if approval not in ("draft", "approved"):
        report.warn("STRUCTURE", "frontmatter has no `approval: draft | approved`; an executor cannot tell whether this plan may be built")
    span = find_section(sections, ("approach",))
    if span and "deciding factor" not in body_text(lines, span).lower() and "n/a" not in body_text(lines, span).lower():
        report.warn("STRUCTURE", "Approach does not name the deciding factor")

    # Ids
    defs: dict[str, tuple[int, str]] = {}
    current_id = None
    for i, line in enumerate(lines):
        match = ID_DEF.match(line)
        if match:
            current_id = match.group(1)
            if current_id in defs:
                report.error("TRACEABILITY", f"line {i + 1}: {current_id} is defined twice")
            defs[current_id] = (i + 1, line)
        elif current_id and line.startswith((" ", "\t")) and line.strip():
            defs[current_id] = (defs[current_id][0], defs[current_id][1] + " " + line.strip())
        else:
            current_id = None
    by_kind = {k: sorted((d for d in defs if d.startswith(k + "-")), key=lambda x: int(x.split("-")[1]))
               for k in ("SC", "FR", "AC", "OQ")}
    seen_undefined: set[str] = set()
    for i, line in enumerate(prose):
        for ref in ID_REF.findall(line):
            if ref not in defs and ref not in seen_undefined:
                seen_undefined.add(ref)
                report.error("TRACEABILITY", f"line {i + 1}: {ref} is referenced but never defined")

    span = find_section(sections, ("tasks",))
    tasks = parse_tasks(lines, span, report) if span else {}

    # The final check line(s) in the Verification section can own criteria that no single task proves.
    final_check = ""
    span_v = find_section(sections, ("verification",))
    if span_v:
        collecting = False
        for line in lines[span_v[0]:span_v[1]]:
            if re.search(r"(?i)\bfinal check\b", line):
                collecting = True
            elif collecting and re.match(r"[-*]\s+\*{0,2}[A-Z]", line):
                collecting = False
            if collecting:
                final_check += " " + line

    # TRACEABILITY
    ac_to_fr: dict[str, set[str]] = {}
    for ac in by_kind["AC"]:
        refs = set(ID_REF.findall(defs[ac][1])) - {ac}
        ac_to_fr[ac] = {r for r in refs if r.startswith("FR-")}
        if not any(r.startswith(("FR-", "SC-")) for r in refs):
            report.error("TRACEABILITY", f"{ac} does not name the requirement or success criterion it verifies")
        if "verif" not in defs[ac][1].lower() and "`" not in defs[ac][1]:
            report.warn("TRACEABILITY", f"{ac} does not say how it is verified (a command, a named test, or what to observe)")
    covered: set[str] = set()
    for task in tasks.values():
        covered |= task["covers"]
    fr_with_ac = {fr for refs in ac_to_fr.values() for fr in refs}
    fr_with_task = {r for r in covered if r.startswith("FR-")}
    fr_with_task |= {fr for ac, refs in ac_to_fr.items() if ac in covered for fr in refs}
    for fr in by_kind["FR"]:
        if fr not in fr_with_ac:
            report.error("TRACEABILITY", f"{fr} has no acceptance criterion")
        if fr not in fr_with_task:
            report.error("TRACEABILITY", f"{fr} is not covered by any task")
    for ac in by_kind["AC"]:
        if ac not in covered and not re.search(rf"\b{ac}\b", final_check):
            report.error("TRACEABILITY", f"{ac} has no owner: it is in no task's Covers and not on the Final check line")
    carriers = " ".join(defs[d][1] for d in by_kind["FR"] + by_kind["AC"]) + final_check + " " + " ".join(sorted(covered))
    if not by_kind["SC"]:
        report.error("TRACEABILITY", "no success criteria (SC-n) defined")
    for sc in by_kind["SC"]:
        if not re.search(rf"\b{sc}\b", carriers):
            report.error("TRACEABILITY", f"{sc} is not carried by any requirement, acceptance criterion, task or the Final check")
    for oq in by_kind["OQ"]:
        text = defs[oq][1].lower()
        if "blocking" in text and "non-blocking" not in text:
            if approval == "approved":
                report.error("OPEN-QUESTION", f"{oq} is blocking but the plan is marked approved")
            else:
                report.warn("OPEN-QUESTION", f"{oq} is blocking: the plan is not ready to approve until it is answered")

    # Facts and assumptions
    span_f = find_section(sections, ("facts",))
    if span_f:
        note_id, note_text, notes = None, "", []
        for line in lines[span_f[0]:span_f[1]]:
            match = NOTE_DEF.match(line)
            if match:
                if note_id:
                    notes.append((note_id, note_text))
                note_id, note_text = match.group(1), line
            elif note_id and line.strip():
                note_text += " " + line.strip()
        if note_id:
            notes.append((note_id, note_text))
        for note_id, text in notes:
            if note_id.startswith("F-") and not EVIDENCE.search(text) and "ran:" not in text.lower():
                report.warn("GROUNDING", f"{note_id} has no evidence (`path:line`, or 'ran: <command> → <result>')")
            if note_id.startswith("A-") and not ("if wrong" in text.lower() and "settled by" in text.lower()):
                report.warn("GROUNDING", f"{note_id} does not say what breaks if it is wrong and what settles it")

    # TASKS
    if not tasks:
        report.error("TASKS", "no task cards found (expected '### T1 — title' headings under '## Tasks')")
        return tasks, approval
    for tid, task in tasks.items():
        fields = task["fields"]
        for name in REQUIRED_TASK_FIELDS:
            if not fields.get(name, "").strip():
                report.error("TASKS", f"{tid} (line {task['line']}): field '{name.capitalize()}' is missing or empty")
        for dep in task["deps"]:
            if dep == tid:
                report.error("TASKS", f"{tid} depends on itself")
            elif dep not in tasks:
                report.error("TASKS", f"{tid} depends on {dep}, which is not a task")
        covers = fields.get("covers", "")
        if covers and not task["covers"] and not re.search(r"(?i)^\s*none\b.*(enabling|spike)", covers, re.S):
            report.error("TASKS", f"{tid}: 'Covers' names no SC/FR/AC; if this is groundwork write 'none — enabling: <what it unblocks>'")
        files = fields.get("files", "")
        if files and not task["files"] and not re.search(r"(?i)\bnone\b", files):
            report.error("TASKS", f"{tid}: 'Files' lists no backticked path")
        leftover = re.sub(r"\([^)]*\)", "", INLINE_CODE.sub("", files))
        if task["files"] and re.search(r"[\w.-]+/[\w./-]+|\b[\w-]+\.[A-Za-z]{1,5}\b", leftover):
            report.warn("TASKS", f"{tid}: 'Files' has a path outside backticks; it is ignored by the collision check")
        verify = fields.get("verify", "")
        if verify and "`" not in verify and not re.search(r"(?i)manual|observe|inspect", verify):
            report.warn("TASKS", f"{tid}: 'Verify' has no runnable command; give one, or say what to observe by hand")
        if fields.get("do") and len(fields["do"].split()) < 12:
            report.warn("TASKS", f"{tid}: 'Do' is very short; the task agent sees little beyond this card, so it must stand alone")
        reversibility = fields.get("reversibility", "")
        if reversibility and not re.match(r"(?i)\s*safe\b", reversibility) and not fields.get("gate", "").strip():
            report.error("TASKS", f"{tid}: reversibility is '{reversibility}', not `safe`, but the card has no 'Gate' (what a person confirms before it runs)")
        kind = fields.get("kind", "").lower()
        if kind not in KINDS:
            report.warn("TASKS", f"{tid}: 'Kind' should be one of {', '.join(sorted(KINDS))} (the executor picks its reviewer from it)")
        if re.match(r"(?i)\s*(l|xl|large)\b", fields.get("size", "")):
            report.warn("TASKS", f"{tid}: size L; split it so one fresh agent can finish and verify it in one sitting")
    seen_task_refs: set[str] = set()
    for i, line in enumerate(prose):
        for ref in TASK_REF.findall(line):
            if ref not in tasks and ref not in seen_task_refs:
                seen_task_refs.add(ref)
                report.warn("TASKS", f"line {i + 1}: {ref} is mentioned but is not a task")
    cycle = find_cycle(tasks)
    if cycle:
        report.error("TASKS", "dependency cycle: " + " → ".join(cycle))
    anc = ancestors(tasks)

    # Execution order must match what the cards derive.
    if not cycle and span:
        start = next((i for i in range(span[0], span[1]) if re.match(r"^###\s+Execution order", lines[i], re.I)), None)
        if start is None:
            report.warn("TASKS", "no '### Execution order' subsection; paste the output of --dag")
        else:
            end = next((i for i in range(start + 1, span[1]) if HEADING.match(lines[i])), span[1])
            pasted = order_lines(raw[start + 1:end])
            if not pasted:
                report.warn("TASKS", "'Execution order' is empty; paste the output of --dag")
            elif pasted != order_lines(emit_dag(tasks).split("\n")):
                report.error("TASKS", "'Execution order' does not match the task cards; paste the current output of --dag")

    # PARALLEL (ancestry is meaningless while there is a cycle)
    ids = [] if cycle else list(tasks)
    for a_index, a in enumerate(ids):
        for b in ids[a_index + 1:]:
            if a in anc[b] or b in anc[a]:
                continue
            shared = sorted({pa if pa == pb else f"{pa} / {pb}"
                             for pa in tasks[a]["files"] for pb in tasks[b]["files"] if overlaps(pa, pb)})
            if shared:
                report.error(
                    "PARALLEL",
                    f"{a} and {b} both touch {', '.join('`' + s + '`' for s in shared)} but neither depends on the "
                    f"other, so an executor may run them at the same time; add a dependency or move the change",
                )

    # GROUNDING
    if check_paths:
        created_by: dict[str, list[str]] = {}
        for tid, task in tasks.items():
            for path, note in task["files"].items():
                if kind_of(note) == "new":
                    created_by.setdefault(path, []).append(tid)

        def on_disk(path: str) -> bool:
            return bool(globlib.glob(str(repo / path))) if is_glob(path) else (repo / path).exists()

        def creators_of(path: str) -> list[str]:
            """Tasks that create this file, or a file under this directory."""
            if path in created_by:
                return created_by[path]
            prefix = path.rstrip("/") + "/"
            return sorted({c for p, cs in created_by.items() if p.startswith(prefix) for c in cs})

        for tid, task in tasks.items():
            for path, note in task["files"].items():
                kind = kind_of(note)
                if kind == "unknown":
                    report.warn("GROUNDING", f"{tid}: `{path}` is not marked (new), (modify) or (delete)")
                elif kind == "new" and on_disk(path) and not is_glob(path) and not revising:
                    report.error("GROUNDING", f"{tid}: `{path}` is marked (new) but already exists")
                elif kind == "existing" and not on_disk(path):
                    creators = [c for c in creators_of(path) if c != tid]
                    if not creators:
                        report.error("GROUNDING", f"{tid}: `{path}` is marked ({note}) but does not exist in {repo}")
                    elif not any(c in anc[tid] for c in creators):
                        report.error("GROUNDING", f"{tid}: `{path}` is created by {', '.join(creators)}, which {tid} does not depend on")
            for name in ("do", "verify"):
                for token in sorted(set(PATH_TOKEN.findall(task["fields"].get(name, "")))):
                    path = normalise(token)
                    if on_disk(path):
                        continue
                    creators = creators_of(path)
                    if not creators:
                        report.warn("GROUNDING", f"{tid}: '{name.capitalize()}' names `{token}`, which does not exist and no task creates")
                    elif not any(c == tid or c in anc[tid] for c in creators):
                        consequence = ("the check cannot pass where this task runs" if name == "verify"
                                       else "add the dependency if the task needs that file")
                        report.warn(
                            "GROUNDING",
                            f"{tid}: '{name.capitalize()}' needs `{token}`, created by {', '.join(creators)}, "
                            f"which {tid} does not depend on; {consequence}",
                        )
        for i, line in enumerate(lines):
            for path, line_no in EVIDENCE.findall(line):
                if "/" not in path and "." not in path and path not in EXTENSIONLESS:
                    continue
                target = repo / path
                if not target.is_file():
                    if not creators_of(normalise(path)):
                        report.error("GROUNDING", f"line {i + 1}: evidence `{path}:{line_no}` points at a file that does not exist")
                    continue
                try:
                    content = target.read_text(encoding="utf-8", errors="replace").split("\n")
                except OSError:
                    continue
                if int(line_no) > len(content) or int(line_no) < 1:
                    report.error("GROUNDING", f"line {i + 1}: evidence `{path}:{line_no}` is past the end of the file ({len(content)} lines)")
                elif not content[int(line_no) - 1].strip():
                    report.warn("GROUNDING", f"line {i + 1}: evidence `{path}:{line_no}` points at a blank line")
        scripts = package_scripts(repo)
        if scripts is not None:
            scoped = re.compile(r"(?:^|\s)(?:-w|--workspace|--filter|--prefix|-C|cd)\b")
            texts = [task["fields"].get("verify", "") for task in tasks.values()]
            if span_v:
                texts += raw[span_v[0]:span_v[1]]
            # A command scoped to a workspace or directory uses that package's scripts, which are not checked here.
            named = {s for text in texts for line in text.split("\n") if not scoped.search(line) for s in RUN_SCRIPT.findall(line)}
            edits_manifest = any("package.json" in task["files"] for task in tasks.values())
            for script in sorted(named - scripts):
                if not edits_manifest:
                    report.warn("GROUNDING", f"`npm run {script}` is used, but package.json has no '{script}' script and no task edits package.json")
    return tasks, approval


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a ship-better-plans plan file")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="repository root for path checks (default: cwd)")
    parser.add_argument("--no-paths", action="store_true", help="skip file-existence and evidence checks")
    parser.add_argument("--revising", action="store_true", help="plan is partly executed: files marked (new) may already exist")
    parser.add_argument("--dag", action="store_true", help="print the execution order derived from the task cards")
    args = parser.parse_args()

    if not args.plan.is_file():
        print(f"lint_plan: {args.plan} is not a file", file=sys.stderr)
        return 2

    report = Report()
    tasks, approval = lint(args.plan, args.repo.resolve(), not args.no_paths, args.revising, report)

    if args.dag:
        blocking = [e for e in report.errors
                    if any(s in e for s in ("dependency cycle", "is not a task", "no task cards", "'Depends on' must be", "used twice"))]
        if blocking:
            print("lint_plan: cannot derive the execution order until these are fixed:", file=sys.stderr)
            for message in blocking:
                print("  " + message, file=sys.stderr)
            return 1
        print(emit_dag(tasks))
        return 0

    for message in report.errors:
        print("ERROR " + message)
    for message in report.warnings:
        print("WARN  " + message)
    print(f"\n{len(report.errors)} error(s), {len(report.warnings)} warning(s), {len(tasks)} task(s), approval: {approval or 'not set'}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
