from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from nvt_combiner.primitives.files import read_file, write_file


class LegacyFileFunctionTests(unittest.TestCase):
    def test_read_file_returns_every_binary_byte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.bin"
            expected = b"\x00\xFF\x7F\x80\x00"
            path.write_bytes(expected)

            status, actual = read_file(path)

            self.assertEqual(0, status)
            self.assertEqual(expected, actual)

    def test_read_file_reports_legacy_open_failure(self) -> None:
        missing = "missing.bin"
        captured = StringIO()
        with redirect_stdout(captured):
            status, actual = read_file(missing)

        self.assertEqual(1, status)
        self.assertIsNone(actual)
        self.assertEqual("Open file fail: missing.bin\n", captured.getvalue())

    def test_write_file_truncates_an_existing_binary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "output.bin"
            path.write_bytes(b"obsolete bytes")

            status = write_file(path, b"\x10\x00\x20")

            self.assertEqual(0, status)
            self.assertEqual(b"\x10\x00\x20", path.read_bytes())

    def test_write_file_reports_legacy_open_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing-parent" / "output.bin"
            captured = StringIO()
            with redirect_stdout(captured):
                status = write_file(path, b"data")

            self.assertEqual(1, status)
            self.assertIn(f'Write file fail: path="{path}"', captured.getvalue())
            self.assertIn("error=", captured.getvalue())

    def test_write_failure_preserves_existing_file_and_removes_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            path = directory / "output.bin"
            path.write_bytes(b"golden")
            captured = StringIO()

            with patch("nvt_combiner.primitives.files.os.replace", side_effect=OSError("simulated replace failure")):
                with redirect_stdout(captured):
                    status = write_file(path, b"replacement")

            self.assertEqual(1, status)
            self.assertEqual(b"golden", path.read_bytes())
            self.assertEqual([path], list(directory.iterdir()))
            self.assertIn("simulated replace failure", captured.getvalue())
