"""Release gate: compare every supported selector through the packaged EXE.

Set ``COMBINER_EXE`` to a freshly built PyInstaller executable to run this
test.  It is intentionally separate from normal module discovery so routine
unit/module runs do not require a local PyInstaller build.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.module import test_merge_mode
from tests.module import test_normal_crc_enabled
from tests.module import test_normal_hostdl_overlay
from tests.module import test_normal_overlay
from tests.module import test_nt36672
from tests.module import test_nt51927_crc
from tests.module import test_nt51928b
from tests.module import test_nt51928b_overlay
from tests.module import test_nt51930
from tests.module import test_nt51930_overlay
from tests.module import test_nt51931
from tests.module import test_nt51931_overlay
from tests.module import test_nt51932_merge_ab
from tests.module import test_nt51932_no_overlay
from tests.module import test_nt51932_overlay
from tests.module import test_nt51950_merge_ab
from tests.module import test_nt51950_normal
from tests.module import test_nt51950_overlay


ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE
PACKAGED_EXE = Path(os.environ.get("COMBINER_EXE", ""))


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def write_crc_disable_case(directory: Path) -> tuple[list[str], list[str]]:
    (directory / "fw.bin").write_bytes(b"0123456789")
    (directory / "block.bin").write_bytes(b"WXYZ")
    (directory / "map.txt").write_bytes(b"")
    return ["CRC_Disable", "fw.bin", "block.bin", "0x0", "0x4", "4"], ["fw.bin"]


def write_generic_crc_case(directory: Path) -> tuple[list[str], list[str]]:
    test_normal_crc_enabled.write_case(directory, False)
    return ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"], ["fw.bin"]


def write_generic_overlay_case(directory: Path) -> tuple[list[str], list[str]]:
    test_normal_overlay.write_case(directory)
    return ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"], ["fw.bin"]


def write_generic_multi_overlay_case(directory: Path) -> tuple[list[str], list[str]]:
    test_normal_overlay.write_case(directory, True)
    return ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"], ["fw.bin"]


def write_generic_hostdl_overlay_case(directory: Path) -> tuple[list[str], list[str]]:
    test_normal_hostdl_overlay.write_hostdl_case(directory)
    return ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"], ["fw.bin"]


def write_nt36672_case(directory: Path) -> tuple[list[str], list[str]]:
    test_nt36672.write_case(directory, False)
    return [test_nt36672.MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x110", "0", "0"], ["out.bin"]


def write_nt51927_case(directory: Path) -> tuple[list[str], list[str]]:
    return test_nt51927_crc.fixture(directory, "CRC8"), ["output.bin"]


def write_nt51928b_case(directory: Path) -> tuple[list[str], list[str]]:
    test_nt51928b.write_case(directory)
    return [test_nt51928b.MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"], ["out.bin"]


def write_nt51928b_overlay_case(directory: Path) -> tuple[list[str], list[str]]:
    test_nt51928b_overlay.write_overlay_case(directory)
    return [test_nt51928b_overlay.MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"], ["out.bin"]


def write_nt51930_case(directory: Path) -> tuple[list[str], list[str]]:
    test_nt51930.write_case(directory)
    return [test_nt51930.MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"], ["out.bin"]


def write_nt51930_overlay_case(directory: Path) -> tuple[list[str], list[str]]:
    test_nt51930_overlay.write_overlay_case(directory)
    return [test_nt51930_overlay.MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"], ["out.bin"]


def write_nt51931_case(directory: Path) -> tuple[list[str], list[str]]:
    test_nt51931.write_case(directory)
    return [test_nt51931.MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"], ["out.bin"]


def write_nt51931_overlay_case(directory: Path) -> tuple[list[str], list[str]]:
    test_nt51931_overlay.write_overlay_case(directory)
    return [test_nt51931_overlay.MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"], ["out.bin"]


def write_nt51932_case(directory: Path) -> tuple[list[str], list[str]]:
    return test_nt51932_no_overlay.write_fixture(directory, b"", "CRC8"), ["output.bin"]


def write_nt51932_overlay_case(directory: Path) -> tuple[list[str], list[str]]:
    return test_nt51932_overlay.write_overlay_case(directory, "CRC8"), ["output.bin"]


def write_nt51932_ab_case(directory: Path) -> tuple[list[str], list[str]]:
    return test_nt51932_merge_ab.write_success_fixture(directory), ["output.bin"]


def write_nt51950_case(directory: Path) -> tuple[list[str], list[str]]:
    return test_nt51950_normal.fixture(directory, "CRC8"), ["output.bin"]


def write_nt51950_overlay_case(directory: Path) -> tuple[list[str], list[str]]:
    return test_nt51950_overlay.write_overlay_case(directory, "CRC8"), ["output.bin"]


def write_nt51950_ab_case(directory: Path) -> tuple[list[str], list[str]]:
    return test_nt51950_merge_ab.write_success_fixture(directory, "CRC8"), ["output.bin"]


def write_merge_case(directory: Path) -> tuple[list[str], list[str]]:
    return test_merge_mode.fixture(directory), ["output.bin"]


class TestPackagedSupportedModes(unittest.TestCase):
    @unittest.skipUnless(PACKAGED_EXE.is_file(), "set COMBINER_EXE to run the packaged release gate")
    def test_all_supported_success_cases_match_reference(self) -> None:
        cases = (
            ("crc-disable", write_crc_disable_case),
            ("generic-crc", write_generic_crc_case),
            ("generic-overlay", write_generic_overlay_case),
            ("generic-multi-overlay", write_generic_multi_overlay_case),
            ("generic-hostdl-overlay", write_generic_hostdl_overlay_case),
            ("nt36672", write_nt36672_case),
            ("nt51927", write_nt51927_case),
            ("nt51928b", write_nt51928b_case),
            ("nt51928b-overlay", write_nt51928b_overlay_case),
            ("nt51930", write_nt51930_case),
            ("nt51930-overlay", write_nt51930_overlay_case),
            ("nt51931", write_nt51931_case),
            ("nt51931-overlay", write_nt51931_overlay_case),
            ("nt51932", write_nt51932_case),
            ("nt51932-overlay", write_nt51932_overlay_case),
            ("nt51932-ab", write_nt51932_ab_case),
            ("nt51950", write_nt51950_case),
            ("nt51950-overlay", write_nt51950_overlay_case),
            ("nt51950-ab", write_nt51950_ab_case),
            ("merge", write_merge_case),
        )
        for name, write_case in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                reference_dir = root / "reference"
                packaged_dir = root / "packaged"
                reference_dir.mkdir()
                packaged_dir.mkdir()
                arguments, output_files = write_case(reference_dir)
                packaged_arguments, packaged_output_files = write_case(packaged_dir)
                self.assertEqual(arguments, packaged_arguments)
                self.assertEqual(output_files, packaged_output_files)

                reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
                packaged = run([str(PACKAGED_EXE), *arguments], packaged_dir)

                self.assertEqual(reference.returncode, packaged.returncode)
                self.assertEqual(reference.stdout, packaged.stdout)
                self.assertEqual(reference.stderr, packaged.stderr)
                for output_file in output_files:
                    self.assertEqual(
                        (reference_dir / output_file).read_bytes(),
                        (packaged_dir / output_file).read_bytes(),
                    )
