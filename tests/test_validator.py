from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from vadf.validator import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
VALID_EXAMPLE = ROOT / "examples" / "verified_handoff.json"
INVALID_EXAMPLE = ROOT / "examples" / "invalid_handoff.json"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class ManifestValidationTests(unittest.TestCase):
    def test_valid_example_has_no_errors(self) -> None:
        self.assertEqual(validate_manifest(load_json(VALID_EXAMPLE)), [])

    def test_invalid_example_reports_multiple_contract_failures(self) -> None:
        errors = validate_manifest(load_json(INVALID_EXAMPLE))
        paths = [error.path for error in errors]
        self.assertGreaterEqual(len(errors), 12)
        self.assertEqual(
            paths[:4],
            [
                "$.schema_version",
                "$.handoff_id",
                "$.implementation_owner.role",
                "$.implementation_owner.worker_handle",
            ],
        )
        self.assertIn("$.implementation_owner.exclusive", paths)
        self.assertIn("$.verification.checks[0].outcome", paths)
        self.assertIn("$.claims[0].included_in_output", paths)
        self.assertIn("$.privacy_review.status", paths)

    def test_non_object_manifest_is_rejected(self) -> None:
        errors = validate_manifest([])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].path, "$")

    def test_empty_path_segment_is_rejected(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["artifacts"][0]["path"] = "vadf//validator.py"
        errors = validate_manifest(manifest)
        self.assertIn("$.artifacts[0].path", {error.path for error in errors})

    def test_drive_qualified_path_is_rejected(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["artifacts"][0]["path"] = "C:/workspace/output.json"
        errors = validate_manifest(manifest)
        self.assertIn("$.artifacts[0].path", {error.path for error in errors})

    def test_supported_claim_requires_evidence(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["claims"][0]["evidence"] = []
        errors = validate_manifest(manifest)
        self.assertIn("$.claims[0].evidence", {error.path for error in errors})

    def test_limited_claim_requires_limitation(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["claims"][0]["status"] = "limited"
        errors = validate_manifest(manifest)
        self.assertIn("$.claims[0].limitation", {error.path for error in errors})

    def test_claim_artifact_reference_must_be_declared(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["claims"][0]["evidence"] = ["artifact:missing-artifact"]
        errors = validate_manifest(manifest)
        self.assertIn("must reference a declared artifact id", {error.message for error in errors})

    def test_claim_check_reference_must_be_declared(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["claims"][0]["evidence"] = ["check:missing-check"]
        errors = validate_manifest(manifest)
        self.assertIn(
            "must reference a declared verification check id",
            {error.message for error in errors},
        )

    def test_claim_path_reference_must_be_repository_relative(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["claims"][0]["evidence"] = ["path:../private/evidence.txt"]
        errors = validate_manifest(manifest)
        self.assertIn("$.claims[0].evidence[0]", {error.path for error in errors})

    def test_claim_evidence_requires_a_reference_prefix(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["claims"][0]["evidence"] = ["vadf/validator.py"]
        errors = validate_manifest(manifest)
        self.assertIn(
            "must use artifact:<id>, check:<id>, or path:<repository-relative-path>",
            {error.message for error in errors},
        )

    def test_unknown_fields_are_rejected(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["unexpected"] = True
        errors = validate_manifest(manifest)
        self.assertIn("$.unexpected", {error.path for error in errors})

    def test_recovery_mode_and_outcome_must_agree(self) -> None:
        manifest = copy.deepcopy(load_json(VALID_EXAMPLE))
        manifest["recovery"] = {
            "mode": "not_needed",
            "outcome": "recovered",
            "notes": "This pair is deliberately contradictory.",
        }
        errors = validate_manifest(manifest)
        self.assertIn("$.recovery.outcome", {error.path for error in errors})


class CommandLineTests(unittest.TestCase):
    def run_cli(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "vadf", "validate", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_cli_returns_zero(self) -> None:
        result = self.run_cli(VALID_EXAMPLE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CONTRACT VALID:", result.stdout)
        self.assertIn("ATTESTATION NOTICE:", result.stdout)

    def test_invalid_cli_returns_one_with_human_readable_errors(self) -> None:
        result = self.run_cli(INVALID_EXAMPLE)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("CONTRACT INVALID:", result.stdout)
        self.assertIn("must be false when claim status is blocked", result.stdout)

    def test_malformed_json_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.json"
            path.write_text("{not-json", encoding="utf-8")
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("INPUT ERROR:", result.stdout)

    def test_duplicate_root_key_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate-root.json"
            path.write_text('{"schema_version":"1.0","schema_version":"1.0"}', encoding="utf-8")
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("duplicate object key: 'schema_version'", result.stdout)

    def test_duplicate_nested_key_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate-nested.json"
            path.write_text(
                '{"outer":{"items":[{"id":"first","id":"second"}]}}',
                encoding="utf-8",
            )
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("duplicate object key: 'id'", result.stdout)

    def test_non_utf8_input_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "non-utf8.json"
            path.write_bytes(b'{"text":"\xff"}')
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("is not valid UTF-8", result.stdout)


if __name__ == "__main__":
    unittest.main()
