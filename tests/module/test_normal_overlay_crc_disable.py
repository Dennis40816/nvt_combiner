from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.module.test_normal_overlay import REFERENCE_EXE, run, write_case


ROOT = Path(__file__).resolve().parents[2]


class TestGenericNormalOverlayCrcDisable(unittest.TestCase):
    def test_overlay_map_does_not_write_crc_fields_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            python_dir = root / "python"
            reference_dir.mkdir()
            python_dir.mkdir()
            write_case(reference_dir)
            write_case(python_dir)
            arguments = ["CRC_Disable", "fw.bin", "block.bin", "0x110", "0", "0"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual((reference_dir / "fw.bin").read_bytes(), (python_dir / "fw.bin").read_bytes())
