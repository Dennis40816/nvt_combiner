from __future__ import annotations

import hashlib
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE


def write_fixture(directory: Path, map_text: bytes, crc_method: str = "CRC8") -> list[str]:
    firmware = bytearray(0x40000)
    firmware[0x702B] = 1
    firmware[0x7038:0x703C] = (0x30000).to_bytes(4, "little")
    firmware[0x7164:0x7168] = (0x10000).to_bytes(4, "little")
    firmware[0x7108:0x710C] = (0x0F).to_bytes(4, "little")
    firmware[0x7168:0x716C] = (0x11000).to_bytes(4, "little")
    firmware[0x7114:0x7118] = (0x0F).to_bytes(4, "little")
    firmware[0x716C:0x7170] = (0x12000).to_bytes(4, "little")
    firmware[0x7120:0x7122] = (0).to_bytes(2, "little")
    firmware[0x10000:0x10010] = bytes(range(0x10))
    firmware[0x11000:0x11010] = bytes(range(0xA0, 0xB0))
    firmware[0x12000] = 0x5A
    firmware[0x30000:0x31000] = bytes(index % 251 for index in range(4096))

    (directory / "fw.bin").write_bytes(firmware)
    (directory / "block.bin").write_bytes(bytes(range(0xC0, 0xD0)))
    (directory / "map.txt").write_bytes(map_text)
    return [MODE, crc_method, "output.bin", "fw.bin", "block.bin", "0x0", "0x20000", "16"]


MODE = "NT51932BASED_NORMAL_MODE"


def run(command: list[str], directory: Path, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=directory, text=True, capture_output=True, check=False, env=environment)


class Nt51932NoOverlayModuleTests(unittest.TestCase):
    def test_reference_empty_and_textual_no_overlay_maps_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            empty_directory = root / "empty"
            textual_directory = root / "textual"
            empty_directory.mkdir()
            textual_directory.mkdir()

            empty = run([str(REFERENCE_EXE), *write_fixture(empty_directory, b"")], empty_directory)
            textual = run(
                [str(REFERENCE_EXE), *write_fixture(textual_directory, b"T01 no-overlay map metadata\n")],
                textual_directory,
            )

            self.assertEqual(0, empty.returncode, empty.stdout + empty.stderr)
            self.assertEqual(0, textual.returncode, textual.stdout + textual.stderr)
            self.assertEqual((empty_directory / "output.bin").read_bytes(), (textual_directory / "output.bin").read_bytes())

    def test_python_crc_modules_match_reference_exit_console_and_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for crc_method in ("CRC8", "CRC32"):
                with self.subTest(crc_method=crc_method):
                    reference_directory = root / crc_method / "reference"
                    python_directory = root / crc_method / "python"
                    reference_directory.mkdir(parents=True)
                    python_directory.mkdir(parents=True)
                    arguments = write_fixture(reference_directory, b"", crc_method)
                    write_fixture(python_directory, b"", crc_method)

                    reference = run([str(REFERENCE_EXE), *arguments], reference_directory)
                    environment = os.environ.copy()
                    environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
                    candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_directory, environment)

                    self.assertEqual(0, reference.returncode, reference.stdout + reference.stderr)
                    self.assertEqual(reference.returncode, candidate.returncode, candidate.stdout + candidate.stderr)
                    self.assertEqual(reference.stdout, candidate.stdout)
                    self.assertEqual(reference.stderr, candidate.stderr)
                    reference_output = (reference_directory / "output.bin").read_bytes()
                    candidate_output = (python_directory / "output.bin").read_bytes()
                    self.assertEqual(reference_output, candidate_output)
                    self.assertEqual(hashlib.sha256(reference_output).digest(), hashlib.sha256(candidate_output).digest())
