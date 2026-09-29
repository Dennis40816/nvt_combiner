from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.module.test_normal_crc_disable import EXE as REFERENCE_EXE, run
from tests.unit.test_overlay import TEXT_SIZE_NO_OVERLAY_MAP


ROOT = Path(__file__).resolve().parents[2]


class TestGenericNormalTextSizeNoOverlay(unittest.TestCase):
    def test_text_size_map_matches_reference_no_overlay_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            python_dir = root / "python"
            reference_dir.mkdir()
            python_dir.mkdir()
            for directory in (reference_dir, python_dir):
                (directory / "fw.bin").write_bytes(b"0123456789")
                (directory / "block.bin").write_bytes(b"WXYZ")
                (directory / "map.txt").write_text(TEXT_SIZE_NO_OVERLAY_MAP, encoding="ascii")
            arguments = ["CRC_Disable", "fw.bin", "block.bin", "0x0", "0x4", "4"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual((reference_dir / "fw.bin").read_bytes(), (python_dir / "fw.bin").read_bytes())
