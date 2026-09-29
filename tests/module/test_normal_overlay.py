from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

from tests.support.differential import REFERENCE_EXE, python_environment, run_process as run

MAP = """?TEXT_SIZE: 0x0 0x2000)
_ovly_table =
entry 0x0 0x0 0x1000 end
size 0x0 0x0 0x10 end
skip
skip
_novlys = end
"""

MULTI_MAP = """?TEXT_SIZE: 0x0 0x3000)
_ovly_table =
entry 0x0 0x0 0x1000 end
size 0x0 0x0 0x10 end
skip
skip
entry 0x0 0x0 0x1100 end
size 0x0 0x0 0x20 end
skip
skip
_novlys = end
"""


def write_case(directory: Path, multiple: bool = False) -> None:
    firmware = bytearray(0x200)
    for offset, value in ((0, 0x80), (8, 3), (12, 0x100), (20, 3), (0x34, 0x7F), (0x104, 4), (0x108, 0x180)):
        firmware[offset : offset + 4] = value.to_bytes(4, "little")
    firmware[0x80:0x84] = bytes(range(0x40, 0x44))
    firmware[0x180:0x184] = bytes(range(0xA0, 0xA4))
    if multiple:
        firmware[0x114:0x118] = (4).to_bytes(4, "little")
        firmware[0x118:0x11C] = (0x184).to_bytes(4, "little")
        firmware[0x184:0x188] = bytes(range(0xB0, 0xB4))
    (directory / "fw.bin").write_bytes(firmware)
    (directory / "block.bin").write_bytes(b"")
    (directory / "map.txt").write_text(MULTI_MAP if multiple else MAP, encoding="ascii")


class TestGenericNormalOverlay(unittest.TestCase):
    def test_matches_reference_for_crc8_and_crc32(self) -> None:
        for mode in ("CRC_Enable", "CRC32_Enable"):
            for multiple in (False, True):
                with self.subTest(mode=mode, multiple=multiple), tempfile.TemporaryDirectory() as temporary:
                    temporary_path = Path(temporary)
                    reference_dir = temporary_path / "reference"
                    python_dir = temporary_path / "python"
                    reference_dir.mkdir()
                    python_dir.mkdir()
                    write_case(reference_dir, multiple)
                    write_case(python_dir, multiple)
                    arguments = [mode, "fw.bin", "block.bin", "0x110", "0", "0"]

                    reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
                    candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, python_environment())

                    self.assertEqual(reference.returncode, candidate.returncode)
                    self.assertEqual(reference.stdout, candidate.stdout)
                    self.assertEqual(
                        (reference_dir / "fw.bin").read_bytes(),
                        (python_dir / "fw.bin").read_bytes(),
                    )
