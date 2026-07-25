"""Command-line interface for the handoff manifest validator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .validator import validate_manifest

EXIT_VALID = 0
EXIT_INVALID = 1
EXIT_INPUT_ERROR = 2


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key at any nesting level."""


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vadf",
        description="Check a sanitized handoff manifest against the structural contract.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser(
        "validate",
        help="validate one JSON handoff manifest",
    )
    validate_parser.add_argument("manifest", type=Path, help="path to a JSON manifest")
    return parser


def _load_manifest(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=_reject_duplicate_keys)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "validate":
        parser.error(f"unsupported command: {args.command}")

    try:
        manifest = _load_manifest(args.manifest)
    except OSError as exc:
        print(f"INPUT ERROR: could not read {args.manifest}: {exc}")
        return EXIT_INPUT_ERROR
    except UnicodeDecodeError as exc:
        print(f"INPUT ERROR: {args.manifest} is not valid UTF-8: {exc}")
        return EXIT_INPUT_ERROR
    except DuplicateKeyError as exc:
        print(f"INPUT ERROR: invalid JSON object in {args.manifest}: {exc}")
        return EXIT_INPUT_ERROR
    except json.JSONDecodeError as exc:
        print(
            "INPUT ERROR: invalid JSON in "
            f"{args.manifest} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
        return EXIT_INPUT_ERROR

    errors = validate_manifest(manifest)
    if errors:
        print(f"CONTRACT INVALID: {args.manifest} has {len(errors)} validation error(s).")
        for error in errors:
            print(f"  - {error.path}: {error.message}")
        return EXIT_INVALID

    artifact_count = len(manifest["artifacts"])
    check_count = len(manifest["verification"]["checks"])
    claim_count = len(manifest["claims"])
    print(
        f"CONTRACT VALID: {args.manifest} contains {artifact_count} artifact(s), "
        f"{check_count} recorded passed check(s), and {claim_count} audited claim(s)."
    )
    print(
        "ATTESTATION NOTICE: commands, outcomes, evidence references, and privacy records "
        "were not executed or independently proven by this validator."
    )
    return EXIT_VALID
