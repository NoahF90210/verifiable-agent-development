"""Check repository-local Markdown links without third-party dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".rpiv", ".venv", "__pycache__"}
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
    )


def local_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if not target or target.startswith(("#", "http://", "https://", "mailto:")):
        return None
    if " " in target:
        target = target.split(" ", 1)[0]
    return unquote(target.split("#", 1)[0])


def main() -> int:
    failures: list[str] = []
    checked_links = 0
    files = markdown_files()
    for markdown_path in files:
        text = markdown_path.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(text):
            target = local_target(match.group(1))
            if target is None:
                continue
            checked_links += 1
            resolved = (markdown_path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                failures.append(
                    f"{markdown_path.relative_to(ROOT)}: link leaves repository: {target}"
                )
                continue
            if not resolved.exists():
                failures.append(
                    f"{markdown_path.relative_to(ROOT)}: missing target: {target}"
                )

    if failures:
        print(f"Markdown link check failed with {len(failures)} error(s).")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"Markdown link check passed for {checked_links} local link(s) in {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
