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


def write_case(directory: Path) -> None:
    firmware = bytearray(0x1200)
    for offset, value in ((0, 0x80), (8, 3), (12, 0x100), (20, 3), (0x34, 0x7F)):
        firmware[offset : offset + 4] = value.to_bytes(4, "little")
    firmware[0x28] = 0xA5
    firmware[0x80:0x84] = bytes(range(0x40, 0x44))
    firmware[0x100 + 12 : 0x100 + 16] = (1).to_bytes(4, "little")
    (directory / "fw.bin").write_bytes(firmware)
    (directory / "block.bin").write_bytes(b"")

    descriptor = "entry 0x0 0x0 0x1000 end\nsize 0x0 0x0 0x1 end\nskip\nskip\n"
    overlay_map = "?TEXT_SIZE: 0x0 0x1000)\n_ovly_table =\n" + descriptor * 256 + "_novlys = end\n"
    (directory / "map.txt").write_text(overlay_map, encoding="ascii")


class TestGenericNormalOverlayCountWrap(unittest.TestCase):
    def test_256_overlay_count_wraps_like_legacy_char_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            python_dir = root / "python"
            reference_dir.mkdir()
            python_dir.mkdir()
            write_case(reference_dir)
            write_case(python_dir)
            arguments = ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual(0xA0, (reference_dir / "fw.bin").read_bytes()[0x28])
            self.assertEqual(
                (reference_dir / "fw.bin").read_bytes(),
                (python_dir / "fw.bin").read_bytes(),
            )
