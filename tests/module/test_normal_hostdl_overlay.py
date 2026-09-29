from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.module.test_normal_overlay import MULTI_MAP, REFERENCE_EXE, run, write_case


ROOT = Path(__file__).resolve().parents[2]
HOST_DLM_SUFFIX = "OverlayDLMaddr\n0123456789012345670x00000184\nskip\nskip\n"


def write_hostdl_case(directory: Path) -> None:
    write_case(directory, True)
    firmware = bytearray((directory / "fw.bin").read_bytes())
    firmware[0x28] = 0x10
    (directory / "fw.bin").write_bytes(firmware)
    (directory / "map.txt").write_text(MULTI_MAP + HOST_DLM_SUFFIX, encoding="ascii")


class TestGenericNormalHostDlOverlay(unittest.TestCase):
    def test_matches_reference_for_crc8_and_crc32(self) -> None:
        for mode in ("CRC_Enable", "CRC32_Enable"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                temporary_path = Path(temporary)
                reference_dir = temporary_path / "reference"
                python_dir = temporary_path / "python"
                reference_dir.mkdir()
                python_dir.mkdir()
                write_hostdl_case(reference_dir)
                write_hostdl_case(python_dir)
                arguments = [mode, "fw.bin", "block.bin", "0x110", "0", "0"]

                reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
                environment = os.environ.copy()
                environment["PYTHONPATH"] = str(ROOT / "src")
                candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

                self.assertEqual(reference.returncode, candidate.returncode)
                self.assertEqual(reference.stdout, candidate.stdout)
                self.assertEqual(
                    (reference_dir / "fw.bin").read_bytes(),
                    (python_dir / "fw.bin").read_bytes(),
                )
