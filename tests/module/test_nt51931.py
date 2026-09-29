from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE
MODE = "NT51931BASED_NORMAL_MODE"


def run(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=environment)


def write_case(directory: Path) -> None:
    firmware = bytearray(0x400)
    for offset, value in (
        (0, 0x80), (8, 3), (12, 0x100), (20, 3),
        (0x34, 3), (0x38, 0x120), (0x44, 3), (0x48, 0x130),
        (0x54, 3), (0x58, 0x140), (0x60, 0x150), (0xF4, 7), (0xF8, 0x160),
    ):
        firmware[offset : offset + 4] = value.to_bytes(4, "little")
    firmware[0x68:0x6A] = (3).to_bytes(2, "little")
    firmware[0x6B] = 2
    for start in (0x80, 0x100, 0x120, 0x130, 0x140, 0x150, 0x154, 0x160):
        for index in range(4):
            firmware[start + index] = (start + index) & 0xFF
    (directory / "fw.bin").write_bytes(firmware)
    (directory / "block.bin").write_bytes(b"")
    (directory / "map.txt").write_bytes(b"")


class TestNt51931(unittest.TestCase):
    def test_matches_reference_for_crc8_and_crc32(self) -> None:
        for method in ("CRC8", "CRC32"):
            with self.subTest(method=method), tempfile.TemporaryDirectory() as temporary:
                temporary_path = Path(temporary)
                reference_dir = temporary_path / "reference"
                python_dir = temporary_path / "python"
                reference_dir.mkdir()
                python_dir.mkdir()
                write_case(reference_dir)
                write_case(python_dir)
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
