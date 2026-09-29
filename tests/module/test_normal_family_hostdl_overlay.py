from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.module.test_normal_overlay import MAP, write_case as write_generic_case
from tests.module.test_nt51928b_overlay import write_overlay_case as write_nt51928b_case
from tests.module.test_nt51930_overlay import write_overlay_case as write_nt51930_case
from tests.module.test_nt51931_overlay import write_overlay_case as write_nt51931_case
from tests.module.test_nt51932_overlay import write_overlay_case as write_nt51932_case
from tests.module.test_nt51950_overlay import write_overlay_case as write_nt51950_case


ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE
HOST_DLM_SUFFIX = "OverlayDLMaddr\n0123456789012345670x00000184\nskip\nskip\n"


def run(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=environment)


def set_hostdl(directory: Path, info_index: int, map_text: str) -> None:
    firmware = bytearray((directory / "fw.bin").read_bytes())
    firmware[info_index] |= 0x10
    (directory / "fw.bin").write_bytes(firmware)
    (directory / "map.txt").write_text(map_text + HOST_DLM_SUFFIX, encoding="ascii")


class TestNormalFamilyHostDlOverlay(unittest.TestCase):
    def test_crc8_hostdl_overlay_matches_reference_for_all_map_families(self) -> None:
        cases = (
            ("generic", lambda directory: self._generic(directory), "fw.bin"),
            ("nt51931", lambda directory: self._nt51931(directory), "out.bin"),
            ("nt51930", lambda directory: self._nt51930(directory), "out.bin"),
            ("nt51932", lambda directory: self._nt51932(directory), "output.bin"),
            ("nt51950", lambda directory: self._nt51950(directory), "output.bin"),
            ("nt51928b", lambda directory: self._nt51928b(directory), "out.bin"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, prepare, output_name in cases:
                with self.subTest(name=name):
                    reference_dir = root / name / "reference"
                    python_dir = root / name / "python"
                    reference_dir.mkdir(parents=True)
                    python_dir.mkdir(parents=True)
                    arguments = prepare(reference_dir)
                    prepare(python_dir)

                    reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
                    environment = os.environ.copy()
                    environment["PYTHONPATH"] = str(ROOT / "src")
                    candidate = run([sys.executable, "-m", "nvt_combiner", *arguments], python_dir, environment)

                    self.assertEqual(reference.returncode, candidate.returncode)
                    self.assertEqual(reference.stdout, candidate.stdout)
                    self.assertEqual(reference.stderr, candidate.stderr)
                    self.assertEqual(
                        (reference_dir / output_name).read_bytes(),
                        (python_dir / output_name).read_bytes(),
                    )

    @staticmethod
    def _generic(directory: Path) -> list[str]:
        write_generic_case(directory, True)
        set_hostdl(directory, 0x28, MAP)
        return ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"]

    @staticmethod
    def _nt51931(directory: Path) -> list[str]:
        write_nt51931_case(directory)
        set_hostdl(directory, 0x28, MAP)
        return ["NT51931BASED_NORMAL_MODE", "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"]

    @staticmethod
    def _nt51930(directory: Path) -> list[str]:
        write_nt51930_case(directory)
        set_hostdl(directory, 0x7028, MAP)
        return ["NT51930BASED_NORMAL_MODE", "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"]

    @staticmethod
    def _nt51932(directory: Path) -> list[str]:
        arguments = write_nt51932_case(directory, "CRC8")
        set_hostdl(directory, 0x7028, MAP)
        return arguments

    @staticmethod
    def _nt51950(directory: Path) -> list[str]:
        arguments = write_nt51950_case(directory, "CRC8")
        set_hostdl(directory, 0xA028, MAP)
        return arguments

    @staticmethod
    def _nt51928b(directory: Path) -> list[str]:
        write_nt51928b_case(directory)
        set_hostdl(directory, 0xD028, MAP)
        return ["NT51928BBASED_NORMAL_MODE", "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"]
