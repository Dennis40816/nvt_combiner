from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.unit.test_overlay import INVALID_TEXT_SIZE_VALUE_MAP, MISSING_TEXT_SIZE_VALUE_MAP, overlay_map_with_entry


ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE


def run(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=environment)


class TestGenericNormalMalformedMap(unittest.TestCase):
    def test_long_map_line_matches_legacy_fgets_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            python_dir = root / "python"
            reference_dir.mkdir()
            python_dir.mkdir()
            for directory in (reference_dir, python_dir):
                (directory / "fw.bin").write_bytes(b"0123456789")
                (directory / "block.bin").write_bytes(b"WXYZ")
                (directory / "map.txt").write_text("A" * 500 + "?TEXT_SIZE:\n", encoding="ascii")
            arguments = ["CRC_Disable", "fw.bin", "block.bin", "0x0", "0x4", "4"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual((reference_dir / "fw.bin").read_bytes(), (python_dir / "fw.bin").read_bytes())

    def test_missing_text_size_value_matches_reference_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            python_dir = root / "python"
            reference_dir.mkdir()
            python_dir.mkdir()
            for directory in (reference_dir, python_dir):
                (directory / "fw.bin").write_bytes(b"0123456789")
                (directory / "block.bin").write_bytes(b"WXYZ")
                (directory / "map.txt").write_text(MISSING_TEXT_SIZE_VALUE_MAP, encoding="ascii")
            arguments = ["CRC_Disable", "fw.bin", "block.bin", "0x0", "0x4", "4"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual((reference_dir / "fw.bin").read_bytes(), (python_dir / "fw.bin").read_bytes())

    def test_missing_overlay_hex_values_match_reference_failure(self) -> None:
        for entry in ("entry", "entry 0x0", "entry 0x0 0x0"):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                reference_dir = root / "reference"
                python_dir = root / "python"
                reference_dir.mkdir()
                python_dir.mkdir()
                for directory in (reference_dir, python_dir):
                    (directory / "fw.bin").write_bytes(b"0123456789")
                    (directory / "block.bin").write_bytes(b"WXYZ")
                    (directory / "map.txt").write_text(overlay_map_with_entry(entry), encoding="ascii")
                arguments = ["CRC_Disable", "fw.bin", "block.bin", "0x0", "0x4", "4"]

                reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
                environment = os.environ.copy()
                environment["PYTHONPATH"] = str(ROOT / "src")
                candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

                self.assertEqual(reference.returncode, candidate.returncode)
                self.assertEqual(reference.stdout, candidate.stdout)
                self.assertEqual(reference.stderr, candidate.stderr)
                self.assertEqual((reference_dir / "fw.bin").read_bytes(), (python_dir / "fw.bin").read_bytes())

    def test_invalid_text_size_hex_value_follows_legacy_strtol(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            python_dir = root / "python"
            reference_dir.mkdir()
            python_dir.mkdir()
            for directory in (reference_dir, python_dir):
                (directory / "fw.bin").write_bytes(b"0123456789")
                (directory / "block.bin").write_bytes(b"WXYZ")
                (directory / "map.txt").write_text(INVALID_TEXT_SIZE_VALUE_MAP, encoding="ascii")
            arguments = ["CRC_Disable", "fw.bin", "block.bin", "0x0", "0x4", "4"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual((reference_dir / "fw.bin").read_bytes(), (python_dir / "fw.bin").read_bytes())
