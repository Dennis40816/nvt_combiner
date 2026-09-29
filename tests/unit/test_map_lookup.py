from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import os
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.modes.legacy_io import open_legacy_map, read_legacy_blocks


class TestLegacyMapLookup(unittest.TestCase):
    def test_falls_back_to_output_map_txt(self) -> None:
        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "fw.bin").write_bytes(b"")
            (directory / "output").mkdir()
            (directory / "output" / "map.txt").write_bytes(b"")
            output = StringIO()
            try:
                os.chdir(directory)
                with redirect_stdout(output):
                    map_file = open_legacy_map("fw.bin")
            finally:
                os.chdir(original_directory)

        self.assertEqual(Path("output") / "map.txt", map_file)
        self.assertEqual(
            "Open map.txt at \"map.txt\" failed.\n"
            "Success to open map.txt at \"output\\map.txt\".\n"
            "--------------------------------------\n",
            output.getvalue(),
        )

    def test_block_reader_reports_legacy_open_failure(self) -> None:
        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = StringIO()
            try:
                os.chdir(directory)
                with redirect_stdout(output):
                    blocks = read_legacy_blocks(["missing.bin", "0x0", "0x0", "1"])
            finally:
                os.chdir(original_directory)

        self.assertIsNone(blocks)
        self.assertEqual(
            "--------------------------------------\n"
            "Start to read other bins.\n"
            "Source\t\tDest\t\tLength\t\tFileName\n"
            "file open failure\n",
            output.getvalue(),
        )

    def test_block_reader_emits_each_row_when_loaded(self) -> None:
        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "block.bin").write_bytes(b"012345")
            output = StringIO()
            try:
                os.chdir(directory)
                with redirect_stdout(output):
                    blocks = read_legacy_blocks(["block.bin", "0x1", "0x4", "3"])
            finally:
                os.chdir(original_directory)

        self.assertIsNotNone(blocks)
        assert blocks is not None
        self.assertEqual(b"123", blocks[0].data)
        self.assertEqual(
            "--------------------------------------\n"
            "Start to read other bins.\n"
            "Source\t\tDest\t\tLength\t\tFileName\n"
            "0x1\t\t0x4\t\t3\t\tblock.bin\n",
            output.getvalue(),
        )
