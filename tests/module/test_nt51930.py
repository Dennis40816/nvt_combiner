from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE
MODE = "NT51930BASED_NORMAL_MODE"


def run(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=environment)


def write_case(directory: Path) -> None:
    firmware = bytearray(0x40000)
    for offset, value in (
        (0x7038, 0x30000), (0x7198, 0x10000), (0x7108, 0xF),
        (0x719C, 0x11000), (0x7114, 0xF), (0x71A0, 0x12000),
    ):
        firmware[offset : offset + 4] = value.to_bytes(4, "little")
    firmware[0x7120:0x7122] = (0xF).to_bytes(2, "little")
    firmware[0x7123] = 2
    for start in (0x10000, 0x11000, 0x12000):
        firmware[start : start + 16] = bytes(range(16))
    firmware[0x30000 : 0x31000] = bytes(index % 251 for index in range(4096))
    (directory / "fw.bin").write_bytes(firmware)
    (directory / "block.bin").write_bytes(b"")
    (directory / "map.txt").write_bytes(b"")


class TestNt51930(unittest.TestCase):
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
