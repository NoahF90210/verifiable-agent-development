from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import check_markdown_links


class MarkdownLinkTests(unittest.TestCase):
    def run_checker(self, root: Path) -> tuple[int, str]:
        output = io.StringIO()
        with mock.patch.object(check_markdown_links, "ROOT", root.resolve()):
            with contextlib.redirect_stdout(output):
                status = check_markdown_links.main()
        return status, output.getvalue()

    def test_existing_local_link_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "README.md").write_text(
                "Read the [guide](docs/guide.md).\n",
                encoding="utf-8",
            )
            status, output = self.run_checker(root)
        self.assertEqual(status, 0)
        self.assertIn("Markdown link check passed", output)

    def test_missing_local_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "Read the [missing guide](docs/missing.md).\n",
                encoding="utf-8",
            )
            status, output = self.run_checker(root)
        self.assertEqual(status, 1)
        self.assertIn("missing target: docs/missing.md", output)

    def test_repository_escape_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "Read the [outside file](../outside.md).\n",
                encoding="utf-8",
            )
            status, output = self.run_checker(root)
        self.assertEqual(status, 1)
        self.assertIn("link leaves repository: ../outside.md", output)


if __name__ == "__main__":
    unittest.main()
