#!/usr/bin/env python3
"""
Verify that relative links in skill documentation resolve on disk.

Walks every `.md` file under skills/ and checks:
  - markdown link targets: [text](path/to/file.md)
  - markdown image targets: ![alt](path/to/file.png)
  - explicit inline backtick references that start with ./ (relative-to-current-dir)

Skipped:
  - http://, https://, mailto:, ftp:// — external links
  - #anchor — same-document anchors (target verification is complex)
  - things in fenced code blocks (illustrative, not real links)
  - things inside single-backtick inline code spans (e.g. `[text](missing.md)`
    used to document markdown link syntax — not a real link)
  - bare `../parent` strings in backticks (too noisy — appears in security
    examples like `../../etc/passwd`, TypeScript path-alias illustrations, etc.)

Exit code:
  0 - all targets resolve
  1 - one or more broken links
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Match [text](target) but not ![alt](target)
MARKDOWN_LINK = re.compile(r"(?<!!)\[(?P<text>[^\]]+)\]\((?P<target>[^)]+)\)")

# Match ![alt](target) for image links
MARKDOWN_IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)")

# Match inline code spans (single-backtick wrapped, single line)
INLINE_CODE = re.compile(r"`[^`\n]+`")

# Match backtick file references that look like paths (heuristic — contains
# `/` or a known extension)
INLINE_FILE_REF = re.compile(
    r"`(?P<path>[a-zA-Z0-9_\-./]+(?:/[a-zA-Z0-9_\-./]+|\.(?:md|py|sh|ts|tsx|js|jsx|json|yml|yaml|toml))(?:[a-zA-Z0-9_\-./]*))`"
)

EXTERNAL_SCHEMES = (
    "http://",
    "https://",
    "mailto:",
    "ftp://",
    "git@",
    "ssh://",
)


def strip_fenced_blocks(text: str) -> str:
    """Remove ```...``` fenced blocks so links inside them aren't checked.

    Preserves line count so character offsets after stripping still map to
    correct line numbers.
    """
    result: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            result.append("")
            continue
        if in_fence:
            result.append("")
        else:
            result.append(line)
    return "\n".join(result)


def strip_inline_code(text: str) -> str:
    """Blank out inline `code spans` by replacing the spanned characters with
    spaces. Preserves length so offsets and line numbers stay aligned."""

    def blank(match: re.Match) -> str:
        return " " * (match.end() - match.start())

    return INLINE_CODE.sub(blank, text)


def is_external(target: str) -> bool:
    return target.startswith(EXTERNAL_SCHEMES)


def is_anchor(target: str) -> bool:
    return target.startswith("#")


def strip_anchor(target: str) -> str:
    """Remove `#anchor` and `?query` fragments."""
    return target.split("#")[0].split("?")[0]


def check_file(md_path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, link_target, reason) for broken links."""
    text = md_path.read_text(encoding="utf-8")
    stripped = strip_inline_code(strip_fenced_blocks(text))
    broken: list[tuple[int, str, str]] = []

    def line_no(idx: int) -> int:
        return stripped[:idx].count("\n") + 1

    def check_target(idx: int, target: str, kind: str) -> None:
        if not target or is_external(target) or is_anchor(target):
            return
        # Skip mailto-like and javascript: schemes
        if ":" in target.split("/")[0]:
            return
        resolved = (md_path.parent / strip_anchor(target)).resolve()
        try:
            resolved.relative_to(REPO_ROOT)
        except ValueError:
            broken.append((line_no(idx), target, f"resolves outside repo ({kind})"))
            return
        if not resolved.exists():
            broken.append((line_no(idx), target, f"does not exist ({kind})"))

    for m in MARKDOWN_LINK.finditer(stripped):
        check_target(m.start(), m.group("target").strip(), "link")

    for m in MARKDOWN_IMAGE.finditer(stripped):
        check_target(m.start(), m.group("target").strip(), "image")

    # Inline backtick file references — only flag explicit `./relative` references
    fenced_only = strip_fenced_blocks(text)
    for m in INLINE_FILE_REF.finditer(fenced_only):
        path = m.group("path").strip()
        if not path.startswith("./"):
            continue
        resolved = (md_path.parent / path).resolve()
        try:
            resolved.relative_to(REPO_ROOT)
        except ValueError:
            broken.append(
                (fenced_only[: m.start()].count("\n") + 1, path, "resolves outside repo (inline)")
            )
            continue
        if not resolved.exists():
            broken.append(
                (fenced_only[: m.start()].count("\n") + 1, path, "does not exist (inline)")
            )

    return broken


def main() -> int:
    parser = argparse.ArgumentParser(description="Check relative links in skill docs")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not SKILLS_DIR.is_dir():
        print("[WARN] skills/ directory not found")
        return 0

    md_files = sorted(SKILLS_DIR.rglob("*.md"))
    total_broken = 0
    files_with_errors = 0

    for md in md_files:
        if args.verbose:
            print(f"Checking {md.relative_to(REPO_ROOT)}...")
        broken = check_file(md)
        if broken:
            files_with_errors += 1
            print(f"\n{md.relative_to(REPO_ROOT)}:")
            for line, target, reason in broken:
                print(f"  L{line}: [{target}] -> {reason}")
                total_broken += 1

    if total_broken == 0:
        print(f"[OK] {len(md_files)} markdown file(s) checked; all relative links resolve.")
        return 0
    print(
        f"\n[FAIL] {total_broken} broken link(s) across {files_with_errors} file(s)."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
