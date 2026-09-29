from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE


def run(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=environment)


class TestGenericNormalMissingBlock(unittest.TestCase):
    def test_missing_block_file_matches_reference_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            python_dir = root / "python"
            reference_dir.mkdir()
            python_dir.mkdir()
            for directory in (reference_dir, python_dir):
                (directory / "fw.bin").write_bytes(b"0123456789")
                (directory / "map.txt").write_bytes(b"")
            arguments = ["CRC_Disable", "fw.bin", "missing.bin", "0x0", "0x4", "4"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual((reference_dir / "fw.bin").read_bytes(), (python_dir / "fw.bin").read_bytes())
