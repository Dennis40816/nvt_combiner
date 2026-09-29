from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.modes.legacy_io import (
    Block,
    merge_firmware_and_blocks,
    prepare_map_based_normal_input,
    read_validated_overlay_map,
)
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL


class TestLegacyIoFunctions(unittest.TestCase):
    def test_reads_and_validates_an_empty_legacy_map(self) -> None:
        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "fw.bin").write_bytes(b"")
            (directory / "map.txt").write_bytes(b"")
            output = StringIO()
            try:
                os.chdir(directory)
                with redirect_stdout(output):
                    overlay_map = read_validated_overlay_map("fw.bin")
            finally:
                os.chdir(original_directory)

        self.assertIsNotNone(overlay_map)
        assert overlay_map is not None
        self.assertEqual("", overlay_map.text)
        self.assertEqual((0, False), (overlay_map.info.count, overlay_map.info.has_overlay))
        self.assertEqual(
            'Success to open map.txt at "map.txt".\n'
            "--------------------------------------\n"
            "This FW has no overlay.\n",
            output.getvalue(),
        )

    def test_merges_firmware_and_blocks_without_changing_copy_order(self) -> None:
        block = Block("block.bin", 0, 4, 2, b"XY")

        self.assertEqual(b"ABCDXY", bytes(merge_firmware_and_blocks(b"ABCD", [block])))

    def test_map_read_failure_reports_path_and_os_error(self) -> None:
        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "fw.bin").write_bytes(b"")
            (directory / "map.txt").write_bytes(b"")
            output = StringIO()
            try:
                os.chdir(directory)
                with patch(
                    "nvt_combiner.modes.legacy_io.read_legacy_map_text",
                    side_effect=OSError("simulated read failure"),
                ):
                    with redirect_stdout(output):
                        overlay_map = read_validated_overlay_map("fw.bin")
            finally:
                os.chdir(original_directory)

        self.assertIsNone(overlay_map)
        self.assertIn('Read map.txt fail: path="map.txt"; error=simulated read failure', output.getvalue())

    def test_preparation_opens_map_before_rejecting_invalid_arity(self) -> None:
        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "fw.bin").write_bytes(b"")
            (directory / "map.txt").write_bytes(b"")
            output = StringIO()
            try:
                os.chdir(directory)
                with redirect_stdout(output):
                    preparation = prepare_map_based_normal_input("fw.bin", [], 8, 9)
            finally:
                os.chdir(original_directory)

        self.assertEqual(RUNTIME_FAIL, preparation.status)
        self.assertIsNone(preparation.input)
        self.assertEqual(
            'Success to open map.txt at "map.txt".\n'
            "--------------------------------------\n"
            "This FW has no overlay.\n"
            "Parameter format is error. FW Merge is FAIL\n",
            output.getvalue(),
        )
