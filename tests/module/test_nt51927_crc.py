from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE
MODE = "NT51927BASED_GEN_CRC_MODE"

def fixture(directory: Path, method: str) -> list[str]:
    image = bytearray(0x400)
    # Common header at 0x200 and one M-IC flash header at 0x220.
    image[0x220:0x224] = (0x300).to_bytes(4, "little")
    image[0x224:0x228] = (0x10).to_bytes(4, "little")
    image[0x228:0x22C] = (3).to_bytes(4, "little")
    image[0x230:0x234] = (0x304).to_bytes(4, "little")
    image[0x234:0x238] = (0x20).to_bytes(4, "little")
    image[0x238:0x23C] = (3).to_bytes(4, "little")
    image[0x240] = 0x02
    image[0x248:0x24C] = (0xFFFFFFFF).to_bytes(4, "little")
    image[0x300:0x304] = b"ILM!"
    image[0x304:0x308] = b"DLM!"
    (directory / "input.bin").write_bytes(image)
    return [MODE, method, "input.bin", "output.bin"]

def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=env)

class Nt51927CrcModuleTests(unittest.TestCase):
    def test_python_matches_reference_for_crc8_and_crc32(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for method in ("CRC8", "CRC32"):
                with self.subTest(method=method):
                    reference_dir, python_dir = root / method / "ref", root / method / "py"
                    reference_dir.mkdir(parents=True); python_dir.mkdir(parents=True)
                    args = fixture(reference_dir, method); fixture(python_dir, method)
                    reference = run([str(REFERENCE_EXE), *args], reference_dir)
                    env = os.environ.copy(); env["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
                    candidate = run([sys.executable, "-m", "nvt_combiner", *args], python_dir, env)
                    self.assertEqual(reference.returncode, candidate.returncode, candidate.stdout + candidate.stderr)
                    self.assertEqual(reference.stdout, candidate.stdout)
                    self.assertEqual(reference.stderr, candidate.stderr)
                    self.assertEqual((reference_dir / "output.bin").read_bytes(), (python_dir / "output.bin").read_bytes())
