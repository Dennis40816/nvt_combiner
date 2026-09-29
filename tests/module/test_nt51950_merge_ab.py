from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE
MODE = "NT51950BASED_MERGE_AB_MODE"


def write_success_fixture(directory: Path, crc_method: str) -> list[str]:
    a_code = bytes(index % 251 for index in range(0x100))
    b_code = bytearray(0xA140)
    b_code[0xA100:0xA104] = (0x2000).to_bytes(4, "little")
    b_code[0xA110:0xA114] = (0x3000).to_bytes(4, "little")
    (directory / "a.bin").write_bytes(a_code)
    (directory / "b.bin").write_bytes(b_code)
    return [MODE, crc_method, "a.bin", "b.bin", "output.bin", "0x100"]


def run(command: list[str], directory: Path, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=directory, text=True, capture_output=True, check=False, env=environment)


class Nt51950MergeAbModuleTests(unittest.TestCase):
    def test_python_merge_ab_matches_reference_for_crc8_and_crc32(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for crc_method in ("CRC8", "CRC32"):
                with self.subTest(crc_method=crc_method):
                    reference_directory = root / crc_method / "reference"
                    python_directory = root / crc_method / "python"
                    reference_directory.mkdir(parents=True)
                    python_directory.mkdir(parents=True)
                    arguments = write_success_fixture(reference_directory, crc_method)
                    write_success_fixture(python_directory, crc_method)

                    reference = run([str(REFERENCE_EXE), *arguments], reference_directory)
                    environment = os.environ.copy()
                    environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
                    candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_directory, environment)

                    self.assertEqual(0, reference.returncode, reference.stdout + reference.stderr)
                    self.assertEqual(reference.returncode, candidate.returncode, candidate.stdout + candidate.stderr)
                    self.assertEqual(reference.stdout, candidate.stdout)
                    self.assertEqual(reference.stderr, candidate.stderr)
                    self.assertEqual((reference_directory / "output.bin").read_bytes(), (python_directory / "output.bin").read_bytes())

    def test_python_overlap_failure_matches_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_directory = root / "reference"
            python_directory = root / "python"
            reference_directory.mkdir()
            python_directory.mkdir()
            for directory in (reference_directory, python_directory):
                (directory / "a.bin").write_bytes(b"\x00" * 0x101)
                (directory / "b.bin").write_bytes(b"\x00" * 0xA140)
            arguments = [MODE, "CRC8", "a.bin", "b.bin", "output.bin", "0x100"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_directory)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_directory, environment)

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertFalse((reference_directory / "output.bin").exists())
            self.assertFalse((python_directory / "output.bin").exists())
