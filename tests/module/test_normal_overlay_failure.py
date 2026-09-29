from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.module.test_normal_overlay import REFERENCE_EXE, run, write_case
from tests.unit.test_overlay import OVER_LIMIT_MAP


ROOT = Path(__file__).resolve().parents[2]


class TestGenericNormalOverlayFailure(unittest.TestCase):
    def test_over_limit_map_matches_reference_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            python_dir = root / "python"
            reference_dir.mkdir()
            python_dir.mkdir()
            write_case(reference_dir)
            write_case(python_dir)
            for directory in (reference_dir, python_dir):
                (directory / "map.txt").write_text(OVER_LIMIT_MAP, encoding="ascii")
            arguments = ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual((reference_dir / "fw.bin").read_bytes(), (python_dir / "fw.bin").read_bytes())
