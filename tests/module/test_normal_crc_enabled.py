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


def write_case(directory: Path, cascade: bool) -> None:
    firmware = bytearray(0x200)
    firmware[0:4] = (0x80).to_bytes(4, "little")
    firmware[8:12] = (3).to_bytes(4, "little")
    firmware[12:16] = (0x100 if not cascade else 0x150).to_bytes(4, "little")
    firmware[20:24] = (3).to_bytes(4, "little")
    firmware[0x34:0x38] = (0x7F).to_bytes(4, "little")
    if cascade:
        firmware[0x20] = 2
        firmware[0x80:0x84] = (0x160).to_bytes(4, "little")
        firmware[0x88:0x8C] = (3).to_bytes(4, "little")
        firmware[0x8C:0x90] = (0x170).to_bytes(4, "little")
        firmware[0x94:0x98] = (3).to_bytes(4, "little")
        firmware[0xB4:0xB8] = (0x7F).to_bytes(4, "little")
        data_start = 0x140
    else:
        data_start = 0x80
    for index in range(32):
        firmware[data_start + index] = 0x40 + index
        firmware[data_start + 0x80 + index] = 0x80 + index

    (directory / "fw.bin").write_bytes(firmware)
    (directory / "block.bin").write_bytes(b"")
    (directory / "map.txt").write_bytes(b"")


class TestGenericNormalCrcEnabled(unittest.TestCase):
    def test_matches_reference_for_crc8_crc32_and_cascade_headers(self) -> None:
        cases = (("CRC_Enable", False), ("CRC32_Enable", False), ("CRC_Enable", True))
        for mode, cascade in cases:
            with self.subTest(mode=mode, cascade=cascade), tempfile.TemporaryDirectory() as temporary:
                temporary_path = Path(temporary)
                reference_dir = temporary_path / "reference"
                python_dir = temporary_path / "python"
                reference_dir.mkdir()
                python_dir.mkdir()
                write_case(reference_dir, cascade)
                write_case(python_dir, cascade)
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
