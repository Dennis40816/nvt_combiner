from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.module.test_normal_overlay import MAP
from tests.module.test_nt51930 import MODE, write_case


ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE


def run(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=environment)


def write_overlay_case(directory: Path) -> None:
    write_case(directory)
    firmware = bytearray((directory / "fw.bin").read_bytes())
    firmware[0x11004:0x11008] = (4).to_bytes(4, "little")
    firmware[0x11008:0x1100C] = (0x18000).to_bytes(4, "little")
    firmware[0x18000:0x18004] = bytes(range(0xA0, 0xA4))
    (directory / "fw.bin").write_bytes(firmware)
    (directory / "map.txt").write_text(MAP, encoding="ascii")


class TestNt51930Overlay(unittest.TestCase):
    def test_matches_reference_for_crc8_and_crc32(self) -> None:
        for method in ("CRC8", "CRC32"):
            with self.subTest(method=method), tempfile.TemporaryDirectory() as temporary:
                temporary_path = Path(temporary)
                reference_dir = temporary_path / "reference"
                python_dir = temporary_path / "python"
                reference_dir.mkdir()
                python_dir.mkdir()
                write_overlay_case(reference_dir)
                write_overlay_case(python_dir)
                arguments = [MODE, method, "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"]

                reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
                environment = os.environ.copy()
                environment["PYTHONPATH"] = str(ROOT / "src")
                candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

                self.assertEqual(reference.returncode, candidate.returncode)
                self.assertEqual(reference.stdout, candidate.stdout)
                self.assertEqual(
                    (reference_dir / "out.bin").read_bytes(),
                    (python_dir / "out.bin").read_bytes(),
                )
