"""Check Git-intended files against bounded publication-safety heuristics.

The patterns catch selected high-risk shapes and formatting violations.
They are not a comprehensive secret scanner or a semantic privacy review.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
MULTIPLE_SENTENCE_PATTERN = re.compile(r"[.!?]\s*(?:\|\s*)?(?=[A-Z`])")
SENSITIVE_PATTERNS = {
    "personal macOS path": re.compile("/" + "Users" + r"/[^\s]+"),
    "personal Linux path": re.compile("/" + "home" + r"/[^\s]+/"),
    "personal Windows path": re.compile(r"[A-Za-z]:[\\/]+" + "Users" + r"[\\/]+[^\s]+"),
    "AWS access key shape": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub legacy token shape": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "GitHub fine-grained token shape": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    "OpenAI-style token shape": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "Google API key shape": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "Slack token shape": re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    "bearer token assignment": re.compile(r"(?i)authorization\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    "credential assignment": re.compile(
        r"(?i)['\"]?\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret|token)\b['\"]?"
        r"\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=-]{8,}"
    ),
    "private key block": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
}


@dataclass(frozen=True)
class ScanResult:
    files: int
    markdown_files: int
    failures: tuple[str, ...]


class BoundaryError(RuntimeError):
    """Raised when the Git-derived publication boundary cannot be enumerated."""


def git_intended_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BoundaryError(f"git ls-files failed with exit code {result.returncode}: {detail}")
    try:
        names = result.stdout.decode("utf-8").split("\0")
    except UnicodeDecodeError as exc:
        raise BoundaryError(f"Git returned a non-UTF-8 path name: {exc}") from exc
    return [root / name for name in names if name]


def _markdown_failures(path: Path, text: str, root: Path) -> list[str]:
    failures: list[str] = []
    in_fence = False
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        prose = re.sub(r"^\s*\d+\.\s+", "", line)
        if not in_fence and MULTIPLE_SENTENCE_PATTERN.search(prose):
            failures.append(
                f"{path.relative_to(root)}:{line_number}: multiple full sentences on one line"
            )
    return failures


def _content_failures(path: Path, text: str, root: Path) -> list[str]:
    relative = path.relative_to(root)
    failures: list[str] = []
    if "\N{EM DASH}" in text:
        failures.append(f"{relative}: contains an em dash")
    if "\0" in text:
        failures.append(f"{relative}: contains NUL bytes and is not publishable text")
    for label, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(text):
            failures.append(f"{relative}: contains {label}")
    return failures


def scan_repository(root: Path = ROOT) -> ScanResult:
    root = root.resolve()
    failures: list[str] = []
    markdown_files = 0
    paths = git_intended_paths(root)
    for path in paths:
        relative = path.relative_to(root)
        if path.is_symlink():
            failures.append(f"{relative}: symlinks are not scanned as publishable text")
            continue
        if not path.is_file():
            failures.append(f"{relative}: Git-intended path is missing or not a regular file")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{relative}: is not valid UTF-8: {exc}")
            continue
        except OSError as exc:
            failures.append(f"{relative}: could not be read: {exc}")
            continue
        failures.extend(_content_failures(path, text, root))
        if path.suffix.lower() == ".md":
            markdown_files += 1
            failures.extend(_markdown_failures(path, text, root))
    return ScanResult(
        files=len(paths),
        markdown_files=markdown_files,
        failures=tuple(failures),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check Git-intended files against bounded publication rules."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root to scan",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = scan_repository(args.root)
    except BoundaryError as exc:
        print(f"Publication boundary error: {exc}")
        return 2
    if result.failures:
        print(f"Publication rule check failed with {len(result.failures)} error(s).")
        for failure in result.failures:
            print(f"  - {failure}")
        return 1
    print(
        f"Publication rule check passed for {result.markdown_files} Markdown file(s) "
        f"and {result.files} Git-intended file(s)."
    )
    print(
        "SCOPE NOTICE: this heuristic check does not replace a comprehensive secret scan "
        "or human privacy review."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
