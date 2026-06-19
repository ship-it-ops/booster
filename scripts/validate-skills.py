#!/usr/bin/env python3
"""
Validate the structure, frontmatter, plugin wiring, marketplace consistency,
and bundled hooks of every skill in this repo.

Run locally: `python3 scripts/validate-skills.py` (or `--verbose` for more detail).
Exits non-zero on any violation. CI runs this on every PR; treat failures as blocking.

Booster's plugin layout (matches Anthropic's official marketplace + ship-code):

  - `plugins/<dir>/.claude-plugin/plugin.json` does NOT have a `skills` field.
    Claude Code's installer rejects it ("Validation errors: skills: Invalid
    input"). Skills are auto-discovered from `<plugin>/skills/<name>/SKILL.md`.
  - `plugins/<dir>/skills/<name>/` contains per-file symlinks back to the
    source skill at `skills/<name>/` so we keep a single source of truth while
    presenting the standard auto-discovery layout to the installer.
  - `plugins/<dir>/hooks/hooks.json` (optional) ships bundled hooks.
  - `.claude-plugin/marketplace.json` lists plugin entries with a `source` field
    pointing at `./plugins/<dir>`. The full `./plugins/` prefix is required
    because Claude Code's installer resolves `source` relative to the
    marketplace root and silently ignores `metadata.pluginRoot`. The marketplace
    plugin `name` may legitimately differ from the directory basename; we only
    enforce that the marketplace `name` matches whatever the plugin.json itself
    declares.

Checks performed:

  STRUCTURE
    - Each `skills/<name>/` contains a `SKILL.md`
    - SKILL.md has parseable YAML frontmatter
    - Frontmatter `name` matches the directory name
    - Frontmatter has a non-empty `description` (50–2000 chars)
    - SKILL.md is under 500 lines
    - `disable-model-invocation` (if present) is a boolean
    - `user-invocable` (if present) is a boolean
    - `context` (if present) is "fork"
    - `agent` (if present) requires `context: fork`

  PLUGIN LAYOUT
    - For each skill, `plugins/<skill-name>/.claude-plugin/plugin.json` exists
      and parses
    - plugin.json has `name`, `description`, valid semver `version`
    - plugin.json `name` matches the plugin directory basename
    - plugin.json has NO `skills` field (Claude Code's installer rejects it)
    - `plugins/<skill-name>/skills/<skill-name>/SKILL.md` exists for
      auto-discovery (typically a symlink to ../../../../skills/<name>/SKILL.md)
    - Every file/dir in `skills/<name>/` has a matching entry under
      `plugins/<name>/skills/<name>/` (catches new skill files shipped without
      a plugin symlink), and orphan/stale symlinks are errors
    - If `plugins/<skill-name>/hooks/` exists, `hooks.json` parses and conforms
      to the Claude Code hook schema (event name, matcher, hooks[].type/command)

  MARKETPLACE CONSISTENCY
    - `.claude-plugin/marketplace.json` parses, has `plugins` array
    - Each marketplace plugin's `source` points at an existing `plugins/<dir>/`
    - Each marketplace plugin's `name` matches the corresponding plugin.json `name`
    - Versions match between marketplace.json and plugin.json
    - Every skill in `skills/` has a corresponding `plugins/<name>/` AND a
      marketplace entry whose source points at it
    - Required marketplace fields: `name`, `source`, `description`, `version`,
      `category`

  CONTENT HYGIENE
    - No bare ${SKILL_DIR} references in any skills/**/*.md (use
      ${CLAUDE_SKILL_DIR} or relative paths)

  FIXTURE PARITY
    - If skills/<name>/tests/fixture-N/ exists, it contains both input.* and
      expected-output.md

  TOOL POLICY
    - Pure-rubric review skills (ship-clean-code, ship-tested-code,
      ship-secure-code, ship-devops) declare only Read/Grep/Glob — they never
      gain write/exec access. (ship-reviewed-prs is the orchestrator and is
      intentionally exempt.)
    - ship-vuln-scan is detect-only: may run scanners (Bash) but must not
      declare Write/Edit (remediation is ship-vuln-fix's job).

Exit codes:
  0 — all checks pass
  1 — structural violations
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
PLUGINS_DIR = REPO_ROOT / "plugins"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
ROOT_PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"

# Cap is intentionally permissive (800) because the existing
# obsidian-knowledge-graph SKILL.md is 752 lines and we don't want CI to fail
# on a pre-existing skill on day one. New skills should still target ≤500; the
# cap exists to catch true bloat (>1000 lines of SKILL.md is a code smell).
SKILL_MD_MAX_LINES = 800
DESCRIPTION_MIN_CHARS = 50
DESCRIPTION_MAX_CHARS = 2000
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][\w.]+)?$")
SKILL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
VALID_AGENT_TYPES = {"Explore", "Plan", "general-purpose"}
VALID_FRONTMATTER_KEYS = {
    "name",
    "description",
    "allowed-tools",
    "disable-model-invocation",
    "user-invocable",
    "context",
    "agent",
    "model",
    "argument-hint",
}

# Hook event names accepted by Claude Code's settings schema. Kept loose — any
# string is structurally valid JSON, but events outside this set are typos or
# unsupported. Update if Claude Code adds new events.
VALID_HOOK_EVENTS = {
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "PostToolBatch",
    "Notification",
    "UserPromptSubmit",
    "UserPromptExpansion",
    "SessionStart",
    "SessionEnd",
    "Stop",
    "StopFailure",
    "SubagentStart",
    "SubagentStop",
    "PreCompact",
    "PostCompact",
    "PermissionRequest",
    "PermissionDenied",
    "Setup",
    "TeammateIdle",
    "TaskCreated",
    "TaskCompleted",
    "Elicitation",
    "ElicitationResult",
    "ConfigChange",
    "WorktreeCreate",
    "WorktreeRemove",
    "InstructionsLoaded",
    "CwdChanged",
    "FileChanged",
}

VALID_HOOK_TYPES = {"command", "prompt", "agent", "http", "mcp_tool"}


class Errors:
    """Accumulates errors keyed by category for grouped reporting."""

    def __init__(self) -> None:
        self._bucket: dict[str, list[str]] = {}

    def add(self, category: str, message: str) -> None:
        self._bucket.setdefault(category, []).append(message)

    def any(self) -> bool:
        return any(self._bucket.values())

    def report(self) -> None:
        if not self.any():
            print("[OK] All validation checks passed.")
            return
        total = sum(len(v) for v in self._bucket.values())
        print(f"\n[FAIL] {total} validation error(s) across {len(self._bucket)} categor(ies):\n")
        for category, messages in self._bucket.items():
            print(f"### {category} ({len(messages)})")
            for m in messages:
                print(f"  - {m}")
            print()


# ---------------------------------------------------------------------------
# Minimal YAML frontmatter parser (no external deps)
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """Parse a YAML frontmatter block at the start of `text`.

    Supports the subset used in this repo:
      key: value
      key: >
        multi-line folded scalar
      key: |
        multi-line literal scalar
      # comments
    """
    if not text.startswith("---\n"):
        return None, "missing opening `---` line"

    end = text.find("\n---\n", 4)
    if end < 0:
        end_alt = text.find("\n---", 4)
        if end_alt < 0:
            return None, "missing closing `---` delimiter"
        end = end_alt

    body = text[4:end]
    out: dict[str, str | bool] = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[0] in (" ", "\t"):
            return None, f"unexpected indented line at frontmatter top level: {line!r}"
        if ":" not in line:
            return None, f"malformed frontmatter line: {line!r}"
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value in (">", "|"):
            collected: list[str] = []
            i += 1
            while i < len(lines):
                cont = lines[i]
                if cont and not cont[0].isspace() and cont.strip():
                    break
                if cont.strip():
                    collected.append(cont.strip())
                else:
                    collected.append("")
                i += 1
            joined = (" " if value == ">" else "\n").join(c for c in collected if c)
            out[key] = joined.strip()
            continue
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        out[key] = value
        i += 1
    return out, None


def to_bool(value: str | bool) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ("true", "yes", "on"):
            return True
        if value.lower() in ("false", "no", "off"):
            return False
    return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def discover_skills() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()
    )


def validate_skill_structure(errors: Errors, skill_dir: Path) -> dict | None:
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not SKILL_NAME_PATTERN.match(skill_name):
        errors.add(
            "Skill naming",
            f"{skill_name!r}: directory name must match {SKILL_NAME_PATTERN.pattern}",
        )

    if not skill_md.exists():
        errors.add("Missing SKILL.md", f"skills/{skill_name}/SKILL.md does not exist")
        return None

    text = skill_md.read_text(encoding="utf-8")
    line_count = text.count("\n") + (0 if text.endswith("\n") else 1)
    if line_count > SKILL_MD_MAX_LINES:
        errors.add(
            "SKILL.md too long",
            f"skills/{skill_name}/SKILL.md is {line_count} lines (max {SKILL_MD_MAX_LINES}; "
            f"move detail into reference.md per docs/writing-skills.md)",
        )

    fm, parse_err = parse_frontmatter(text)
    if fm is None:
        errors.add(
            "Frontmatter parse error",
            f"skills/{skill_name}/SKILL.md: {parse_err}",
        )
        return None

    if "name" not in fm:
        errors.add(
            "Frontmatter missing name",
            f"skills/{skill_name}/SKILL.md: `name` is required",
        )
    elif fm["name"] != skill_name:
        errors.add(
            "Frontmatter name mismatch",
            f"skills/{skill_name}/SKILL.md: frontmatter name {fm['name']!r} != directory name "
            f"{skill_name!r} (skill discovery requires these to match)",
        )

    if "description" not in fm:
        errors.add(
            "Frontmatter missing description",
            f"skills/{skill_name}/SKILL.md: `description` is required",
        )
    else:
        desc = str(fm["description"])
        if len(desc) < DESCRIPTION_MIN_CHARS:
            errors.add(
                "Description too short",
                f"skills/{skill_name}/SKILL.md: description is {len(desc)} chars "
                f"(min {DESCRIPTION_MIN_CHARS}). Auto-invocation matching needs enough "
                f"context to distinguish this skill from others.",
            )
        elif len(desc) > DESCRIPTION_MAX_CHARS:
            errors.add(
                "Description too long",
                f"skills/{skill_name}/SKILL.md: description is {len(desc)} chars "
                f"(max {DESCRIPTION_MAX_CHARS}). Move detail to the Purpose section.",
            )

    if "disable-model-invocation" in fm and to_bool(fm["disable-model-invocation"]) is None:
        errors.add(
            "Invalid disable-model-invocation",
            f"skills/{skill_name}/SKILL.md: disable-model-invocation must be a boolean, "
            f"got {fm['disable-model-invocation']!r}",
        )

    if "user-invocable" in fm and to_bool(fm["user-invocable"]) is None:
        errors.add(
            "Invalid user-invocable",
            f"skills/{skill_name}/SKILL.md: user-invocable must be a boolean, "
            f"got {fm['user-invocable']!r}",
        )

    if "context" in fm and fm["context"] != "fork":
        errors.add(
            "Invalid context",
            f"skills/{skill_name}/SKILL.md: context must be 'fork' if present, "
            f"got {fm['context']!r}",
        )

    if "agent" in fm:
        if "context" not in fm:
            errors.add(
                "agent without context: fork",
                f"skills/{skill_name}/SKILL.md: agent field requires context: fork",
            )
        if fm["agent"] not in VALID_AGENT_TYPES:
            errors.add(
                "Invalid agent type",
                f"skills/{skill_name}/SKILL.md: agent must be one of "
                f"{sorted(VALID_AGENT_TYPES)}, got {fm['agent']!r}",
            )

    unknown = set(fm.keys()) - VALID_FRONTMATTER_KEYS
    if unknown:
        errors.add(
            "Unknown frontmatter keys",
            f"skills/{skill_name}/SKILL.md: unknown keys {sorted(unknown)} "
            f"(allowed: {sorted(VALID_FRONTMATTER_KEYS)})",
        )

    return fm


def validate_plugin_layout(errors: Errors, skill_name: str) -> dict | None:
    """Validate `plugins/<skill_name>/`. Returns the parsed plugin.json."""
    plugin_dir = PLUGINS_DIR / skill_name
    if not plugin_dir.is_dir():
        errors.add(
            "Missing plugin wrapper",
            f"plugins/{skill_name}/ does not exist (every skill must have a plugin wrapper)",
        )
        return None

    plugin_manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_manifest.exists():
        errors.add(
            "Missing plugin.json",
            f"plugins/{skill_name}/.claude-plugin/plugin.json does not exist",
        )
        return None
    try:
        manifest = json.loads(plugin_manifest.read_text())
    except json.JSONDecodeError as e:
        errors.add(
            "Invalid plugin.json",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: {e}",
        )
        return None

    if "name" not in manifest:
        errors.add(
            "Plugin missing name",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: `name` is required",
        )
    elif manifest["name"] != skill_name:
        errors.add(
            "Plugin name mismatch",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: name "
            f"{manifest['name']!r} != directory name {skill_name!r} "
            f"(see docs/agent/decisions/plugin-name-matches-source-dir.md)",
        )

    if "description" not in manifest:
        errors.add(
            "Plugin missing description",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: `description` is required",
        )

    version = manifest.get("version", "")
    if not SEMVER_PATTERN.match(str(version)):
        errors.add(
            "Plugin version invalid",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: version {version!r} "
            f"is not a valid semver (X.Y.Z)",
        )

    # Claude Code's plugin schema rejects a `skills` field on plugin.json
    # (validated against the official marketplace + observed install failure
    # "Validation errors: skills: Invalid input"). Skills are auto-discovered
    # from `<plugin>/skills/<skill-name>/SKILL.md` instead.
    if "skills" in manifest:
        errors.add(
            "Plugin manifest has `skills` field",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: remove the "
            f"`skills` field — Claude Code's installer rejects it with "
            f"'Validation errors: skills: Invalid input'. Auto-discovery uses "
            f"plugins/{skill_name}/skills/{skill_name}/SKILL.md (typically a "
            f"symlink to ../../../../skills/{skill_name}/).",
        )

    # Verify the auto-discovery path exists and resolves to a SKILL.md
    plugin_skill_dir = plugin_dir / "skills" / skill_name
    plugin_skill_md = plugin_skill_dir / "SKILL.md"
    if not plugin_skill_md.exists():
        errors.add(
            "Plugin missing auto-discovery skill",
            f"plugins/{skill_name}/skills/{skill_name}/SKILL.md is missing. "
            f"Create it (typically as a symlink): "
            f"plugins/{skill_name}/skills/{skill_name}/SKILL.md -> "
            f"../../../../skills/{skill_name}/SKILL.md",
        )

    # Every file/dir in the source skill directory must have a matching entry
    # under the plugin wrapper. Otherwise plugin-installed users get a partial
    # copy that's missing things SKILL.md references (overrides.example.md,
    # tests/, etc.). This regression slipped past ship-code's CI once; the
    # check came over with the marketplace merge.
    src_skill_dir = SKILLS_DIR / skill_name
    if src_skill_dir.is_dir() and plugin_skill_dir.is_dir():
        src_entries = {p.name for p in src_skill_dir.iterdir()}
        plugin_entries = {p.name for p in plugin_skill_dir.iterdir()}
        for missing in sorted(src_entries - plugin_entries):
            errors.add(
                "Plugin missing file",
                f"plugins/{skill_name}/skills/{skill_name}/{missing} does not exist "
                f"but skills/{skill_name}/{missing} does. Add a symlink: "
                f"`ln -s ../../../../skills/{skill_name}/{missing} "
                f"plugins/{skill_name}/skills/{skill_name}/{missing}`",
            )
        for extra in sorted(plugin_entries - src_entries):
            errors.add(
                "Plugin has orphan file",
                f"plugins/{skill_name}/skills/{skill_name}/{extra} exists but "
                f"skills/{skill_name}/{extra} does not — stale symlink?",
            )

    # Optional: validate bundled hooks.json if present
    hooks_path = plugin_dir / "hooks" / "hooks.json"
    if hooks_path.exists():
        validate_hooks_json(errors, hooks_path, f"plugins/{skill_name}/hooks/hooks.json")

    return manifest


def validate_hooks_json(errors: Errors, hooks_path: Path, rel_label: str) -> None:
    """Validate a bundled hooks.json conforms to Claude Code's hook schema."""
    try:
        data = json.loads(hooks_path.read_text())
    except json.JSONDecodeError as e:
        errors.add("Invalid hooks.json", f"{rel_label}: {e}")
        return

    if not isinstance(data, dict) or "hooks" not in data:
        errors.add(
            "hooks.json missing root key",
            f"{rel_label}: top-level must be an object with a `hooks` key",
        )
        return

    hooks_root = data["hooks"]
    if not isinstance(hooks_root, dict):
        errors.add(
            "hooks.json malformed",
            f"{rel_label}: `hooks` must be an object keyed by event name",
        )
        return

    for event, event_entries in hooks_root.items():
        if event not in VALID_HOOK_EVENTS:
            errors.add(
                "Unknown hook event",
                f"{rel_label}: {event!r} is not a known Claude Code hook event "
                f"(check spelling against the official schema)",
            )
        if not isinstance(event_entries, list):
            errors.add(
                "hook event entries malformed",
                f"{rel_label}: hooks[{event!r}] must be an array",
            )
            continue
        for i, entry in enumerate(event_entries):
            if not isinstance(entry, dict):
                errors.add(
                    "hook entry malformed",
                    f"{rel_label}: hooks[{event!r}][{i}] must be an object",
                )
                continue
            if "hooks" not in entry or not isinstance(entry["hooks"], list):
                errors.add(
                    "hook entry missing hooks array",
                    f"{rel_label}: hooks[{event!r}][{i}] must contain a `hooks` array",
                )
                continue
            for j, h in enumerate(entry["hooks"]):
                if not isinstance(h, dict):
                    errors.add(
                        "hook step malformed",
                        f"{rel_label}: hooks[{event!r}][{i}].hooks[{j}] must be an object",
                    )
                    continue
                if h.get("type") not in VALID_HOOK_TYPES:
                    errors.add(
                        "hook step invalid type",
                        f"{rel_label}: hooks[{event!r}][{i}].hooks[{j}].type "
                        f"is {h.get('type')!r}, must be one of {sorted(VALID_HOOK_TYPES)}",
                    )
                if h.get("type") == "command" and not h.get("command"):
                    errors.add(
                        "hook command empty",
                        f"{rel_label}: hooks[{event!r}][{i}].hooks[{j}] is "
                        f"type:command but `command` is missing/empty",
                    )


def validate_marketplace(errors: Errors, skill_dirs: list[Path]) -> None:
    if not MARKETPLACE_JSON.exists():
        errors.add(
            "Missing marketplace.json",
            ".claude-plugin/marketplace.json does not exist",
        )
        return
    try:
        marketplace = json.loads(MARKETPLACE_JSON.read_text())
    except json.JSONDecodeError as e:
        errors.add("Invalid marketplace.json", f".claude-plugin/marketplace.json: {e}")
        return

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        errors.add(
            "Marketplace missing plugins",
            ".claude-plugin/marketplace.json: top-level `plugins` array required",
        )
        return

    skill_names = {s.name for s in skill_dirs}
    plugin_dirs_seen: set[str] = set()

    for entry in plugins:
        if not isinstance(entry, dict):
            errors.add(
                "Marketplace entry malformed",
                ".claude-plugin/marketplace.json: each plugin entry must be an object",
            )
            continue
        for field in ("name", "source", "description", "version", "category"):
            if field not in entry:
                errors.add(
                    "Marketplace entry missing field",
                    f".claude-plugin/marketplace.json plugin {entry.get('name')!r}: "
                    f"`{field}` is required",
                )

        source = entry.get("source", "")
        if not source.startswith("./plugins/"):
            errors.add(
                "Marketplace source not under ./plugins/",
                f".claude-plugin/marketplace.json plugin {entry.get('name')!r}: "
                f"`source` must begin with './plugins/' (got {source!r}). "
                f"Claude Code's installer resolves `source` relative to the "
                f"marketplace root and does not honor `metadata.pluginRoot`, "
                f"so the full path must be inlined.",
            )
            continue

        plugin_basename = source[len("./plugins/"):].rstrip("/")
        plugin_dirs_seen.add(plugin_basename)
        plugin_path = PLUGINS_DIR / plugin_basename
        if not plugin_path.is_dir():
            errors.add(
                "Marketplace source missing",
                f".claude-plugin/marketplace.json plugin {entry.get('name')!r}: "
                f"source {source!r} points at plugins/{plugin_basename}/ which "
                f"does not exist",
            )
            continue

        # Cross-check name & version against plugin.json
        manifest_path = plugin_path / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            continue
        if manifest.get("name") != entry.get("name"):
            errors.add(
                "Plugin name mismatch",
                f"marketplace.json says {entry.get('name')!r} but "
                f"plugins/{plugin_basename}/.claude-plugin/plugin.json says "
                f"{manifest.get('name')!r}",
            )
        if manifest.get("version") != entry.get("version"):
            errors.add(
                "Version mismatch",
                f"marketplace.json says {entry.get('name')} v{entry.get('version')}, "
                f"but plugins/{plugin_basename}/.claude-plugin/plugin.json says "
                f"v{manifest.get('version')}",
            )

    # Every skill must have a plugin wrapper that's listed in the marketplace
    for sname in sorted(skill_names - plugin_dirs_seen):
        # Skill has a plugin dir but is it in the marketplace? Check both.
        if (PLUGINS_DIR / sname).is_dir():
            errors.add(
                "Skill plugin not in marketplace",
                f"plugins/{sname}/ exists but no marketplace.json entry sources from "
                f"./plugins/{sname}",
            )
        else:
            errors.add(
                "Skill missing plugin wrapper",
                f"skills/{sname}/ has no corresponding plugins/{sname}/ (and no "
                f"marketplace entry)",
            )

    # Every plugin dir referenced by the marketplace should be in skills/.
    # We don't enforce strict plugin-dir == skill-dir here because the booster
    # marketplace allows plugin name to differ from source basename.
    extant_plugin_dirs = (
        {p.name for p in PLUGINS_DIR.iterdir() if p.is_dir()}
        if PLUGINS_DIR.is_dir()
        else set()
    )
    for pdir in sorted(plugin_dirs_seen - extant_plugin_dirs):
        # Already covered by "Marketplace source missing"
        continue
    for pdir in sorted(extant_plugin_dirs - plugin_dirs_seen):
        errors.add(
            "Plugin dir not referenced",
            f"plugins/{pdir}/ exists but no marketplace.json entry sources from "
            f"./plugins/{pdir}",
        )


def validate_root_plugin_json(errors: Errors, skill_dirs: list[Path]) -> None:
    """Validate the root `.claude-plugin/plugin.json` that declares the repo as
    a single plugin. Claude Code's installer rejects a `skills` field, so
    skills must be auto-discoverable from `skills/<name>/SKILL.md` at the
    plugin root — which they already are, since `skills/` lives at repo root.

    The root plugin.json is optional (some marketplace-only repos don't have it)
    — skip silently if absent.
    """
    if not ROOT_PLUGIN_JSON.exists():
        return
    try:
        root = json.loads(ROOT_PLUGIN_JSON.read_text())
    except json.JSONDecodeError as e:
        errors.add("Invalid root plugin.json", f".claude-plugin/plugin.json: {e}")
        return

    if "skills" in root:
        errors.add(
            "Root plugin.json has `skills` field",
            f".claude-plugin/plugin.json: remove the `skills` field — Claude "
            f"Code's installer rejects it with 'Validation errors: skills: "
            f"Invalid input'. Skills at skills/<name>/SKILL.md are "
            f"auto-discovered when the root is installed as a plugin.",
        )

    for s in skill_dirs:
        if not (s / "SKILL.md").exists():
            errors.add(
                "Root skill missing SKILL.md",
                f"skills/{s.name}/SKILL.md is missing — auto-discovery from "
                f"the root plugin.json requires it",
            )

    if "version" in root and not SEMVER_PATTERN.match(str(root["version"])):
        errors.add(
            "Root plugin.json version invalid",
            f".claude-plugin/plugin.json: version {root['version']!r} is not valid semver",
        )


def validate_no_skill_dir_leakage(errors: Errors) -> None:
    """The bare ${SKILL_DIR} variable is not the documented form. Use ${CLAUDE_SKILL_DIR} or relative paths."""
    if not SKILLS_DIR.is_dir():
        return
    bad_pattern = re.compile(r"\$\{SKILL_DIR\}")
    for md in SKILLS_DIR.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for match in bad_pattern.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            errors.add(
                "${SKILL_DIR} leakage",
                f"{md.relative_to(REPO_ROOT)}:{line_no}: use ${{CLAUDE_SKILL_DIR}} or a "
                f"relative path; bare ${{SKILL_DIR}} is not the documented variable",
            )


def validate_fixture_parity(errors: Errors, skill_dirs: list[Path]) -> None:
    for skill_dir in skill_dirs:
        tests_dir = skill_dir / "tests"
        if not tests_dir.is_dir():
            continue
        for fixture in sorted(tests_dir.iterdir()):
            if not fixture.is_dir():
                continue
            if not fixture.name.startswith("fixture-"):
                continue
            input_files = [
                p
                for p in fixture.iterdir()
                if p.is_file() and (p.stem == "input" or p.name.startswith("input."))
            ]
            expected = fixture / "expected-output.md"
            if not input_files:
                errors.add(
                    "Fixture missing input",
                    f"{fixture.relative_to(REPO_ROOT)}: no `input.*` file found",
                )
            if not expected.exists():
                errors.add(
                    "Fixture missing expected-output",
                    f"{fixture.relative_to(REPO_ROOT)}: no `expected-output.md` file found",
                )


# --- Tool-policy enforcement ---------------------------------------------
#
# The `allowed-tools` frontmatter is stored as one scalar string (e.g.
# "Read, Grep, Bash(npm ci *)"). These rules machine-enforce two trust
# invariants that were previously only convention:
#
#   1. The pure-rubric REVIEW skills never gain write/exec access. A future
#      copy-paste must not silently let a "this only reads my code" skill edit
#      files or run commands. NOTE: ship-reviewed-prs is intentionally NOT in
#      this set — it is the orchestrator (declares Task/Bash/TodoWrite to spawn
#      personas and submit via gh). The guarded set is the four pure-rubric
#      depth skills only.
#   2. ship-vuln-scan is detect-only: it may run scanners (Bash) but must not
#      declare Write/Edit. Remediation (editing manifests) is ship-vuln-fix.

READ_ONLY_REVIEW_SKILLS = {
    "ship-clean-code",
    "ship-tested-code",
    "ship-secure-code",
    "ship-devops",
}
READ_ONLY_TOOLS = {"Read", "Grep", "Glob"}
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}


def tokenize_allowed_tools(value: str) -> list[str]:
    """Split an allowed-tools scalar into tool tokens, respecting Bash(...) scopes.

    "Read, Grep, Bash(npm ci *), Edit" -> ["Read", "Grep", "Bash(npm ci *)", "Edit"]
    """
    tools: list[str] = []
    depth = 0
    cur = ""
    for ch in value:
        if ch == "(":
            depth += 1
            cur += ch
        elif ch == ")":
            depth = max(0, depth - 1)
            cur += ch
        elif ch == "," and depth == 0:
            if cur.strip():
                tools.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        tools.append(cur.strip())
    return tools


def tool_name(token: str) -> str:
    """Bare tool name without any scope: 'Bash(npm ci *)' -> 'Bash'."""
    return token.split("(", 1)[0].strip()


def validate_tool_policy(errors: Errors, skill_dirs: list[Path]) -> None:
    for skill_dir in skill_dirs:
        name = skill_dir.name
        if name not in READ_ONLY_REVIEW_SKILLS and name != "ship-vuln-scan":
            continue
        skill_md = skill_dir / "SKILL.md"
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue
        fm, _ = parse_frontmatter(text)
        if not fm:
            continue
        if "allowed-tools" not in fm:
            # Omitting allowed-tools grants UNRESTRICTED tools — that would silently
            # bypass this guard, which exists precisely to prevent unnoticed privilege
            # gain. A guarded skill must declare an explicit read-only/detect-only set.
            errors.add(
                "Guarded skill missing allowed-tools",
                f"skills/{name}/SKILL.md: must declare an explicit `allowed-tools` "
                f"(read-only for review skills, detect-only for ship-vuln-scan). "
                f"Omitting it grants unrestricted tools and bypasses the tool-policy guard.",
            )
            continue
        names = {tool_name(t) for t in tokenize_allowed_tools(str(fm["allowed-tools"]))}

        if name in READ_ONLY_REVIEW_SKILLS:
            extra = names - READ_ONLY_TOOLS
            if extra:
                errors.add(
                    "Review skill is not read-only",
                    f"skills/{name}/SKILL.md: pure-rubric review skills must declare only "
                    f"{sorted(READ_ONLY_TOOLS)}; found extra tool(s) {sorted(extra)}. "
                    f"A review skill must never gain write/exec access.",
                )

        if name == "ship-vuln-scan":
            writes = names & WRITE_TOOLS
            if writes:
                errors.add(
                    "Detection skill declares write tools",
                    f"skills/{name}/SKILL.md: ship-vuln-scan is detect-only and must not declare "
                    f"{sorted(writes)}. Editing manifests/lockfiles belongs to ship-vuln-fix.",
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate booster skills")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="print each skill as it's checked"
    )
    args = parser.parse_args()

    errors = Errors()
    skill_dirs = discover_skills()

    if not skill_dirs:
        print("[WARN] No skills found at skills/*/SKILL.md")
        return 0

    if args.verbose:
        print(f"Found {len(skill_dirs)} skill(s):")
        for s in skill_dirs:
            print(f"  - {s.name}")
        print()

    for skill_dir in skill_dirs:
        if args.verbose:
            print(f"Checking {skill_dir.name}...")
        validate_skill_structure(errors, skill_dir)
        validate_plugin_layout(errors, skill_dir.name)

    validate_marketplace(errors, skill_dirs)
    validate_root_plugin_json(errors, skill_dirs)
    validate_no_skill_dir_leakage(errors)
    validate_fixture_parity(errors, skill_dirs)
    validate_tool_policy(errors, skill_dirs)

    errors.report()
    return 1 if errors.any() else 0


if __name__ == "__main__":
    sys.exit(main())
