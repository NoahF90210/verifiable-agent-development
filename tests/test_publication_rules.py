from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.check_publication_rules import main, scan_repository


def initialize_repository(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "README.md").write_text("# Fixture\n\nSafe publication text.\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)


class PublicationRuleTests(unittest.TestCase):
    def test_clean_git_intended_boundary_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            result = scan_repository(root)
        self.assertEqual(result.failures, ())
        self.assertEqual(result.files, 1)
        self.assertEqual(result.markdown_files, 1)

    def test_tracked_file_in_formerly_excluded_directory_is_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            path = root / ".rpiv" / "public.md"
            path.parent.mkdir()
            em_dash = chr(0x2014)
            path.write_text(f"This tracked file contains an em dash {em_dash} and must fail.\n", encoding="utf-8")
            subprocess.run(["git", "add", "-f", ".rpiv/public.md"], cwd=root, check=True)
            result = scan_repository(root)
        self.assertTrue(any(".rpiv/public.md: contains an em dash" in item for item in result.failures))

    def test_non_utf8_git_intended_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            (root / "binary.dat").write_bytes(b"public-prefix\xffprivate-suffix")
            result = scan_repository(root)
        self.assertTrue(any("binary.dat: is not valid UTF-8" in item for item in result.failures))

    def test_high_risk_secret_shapes_fail(self) -> None:
        fixtures = {
            "GitHub fine-grained token shape": "github" + "_pat_" + "A" * 24,
            "OpenAI-style token shape": "sk" + "-" + "A" * 24,
            "Google API key shape": "AI" + "za" + "A" * 35,
            "credential assignment": "password" + "=" + "A" * 12,
            "quoted credential assignment": '"' + "api_key" + '": "' + "A" * 12 + '"',
            "private key block": "-----BEGIN " + "PRIVATE KEY-----",
        }
        for expected_label, fixture in fixtures.items():
            with self.subTest(expected_label=expected_label):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    initialize_repository(root)
                    (root / "candidate.txt").write_text(fixture, encoding="utf-8")
                    result = scan_repository(root)
                label = "credential assignment" if expected_label == "quoted credential assignment" else expected_label
                self.assertTrue(
                    any(label in item for item in result.failures),
                    result.failures,
                )

    def test_unreadable_git_intended_file_fails_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            candidate = root / "candidate.txt"
            candidate.write_text("Content that will become unreadable.\n", encoding="utf-8")
            original_read_text = Path.read_text

            def read_text(path: Path, *args: object, **kwargs: object) -> str:
                if path.resolve() == candidate.resolve():
                    raise PermissionError("fixture denied")
                return original_read_text(path, *args, **kwargs)

            with mock.patch.object(Path, "read_text", read_text):
                result = scan_repository(root)
        self.assertTrue(
            any("candidate.txt: could not be read" in item for item in result.failures),
            result.failures,
        )

    def test_main_returns_one_and_prints_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            em_dash = chr(0x2014)
            (root / "candidate.txt").write_text(
                f"Unsafe {em_dash} publication text.\n",
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["--root", str(root)])
        self.assertEqual(status, 1)
        self.assertIn("Publication rule check failed", output.getvalue())
        self.assertIn("candidate.txt: contains an em dash", output.getvalue())

    def test_main_returns_two_when_git_boundary_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(["--root", directory])
        self.assertEqual(status, 2)
        self.assertIn("Publication boundary error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
