from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.primitives.legacy_args import firmware_path_for_legacy_arguments


class TestLegacyArgumentPaths(unittest.TestCase):
    def test_finds_in_place_generic_firmware_argument(self) -> None:
        self.assertEqual("fw.bin", firmware_path_for_legacy_arguments(["CRC_Enable", "fw.bin", "block.bin", "0", "0", "0"]))

    def test_finds_normal_family_firmware_argument(self) -> None:
        self.assertEqual(
            "fw.bin",
            firmware_path_for_legacy_arguments(["NT51932BASED_NORMAL_MODE", "CRC8", "out.bin", "fw.bin", "block.bin", "0", "0", "0"]),
        )

    def test_returns_none_for_non_map_modes_and_incomplete_arguments(self) -> None:
        self.assertIsNone(firmware_path_for_legacy_arguments(["MERGE_MODE", "out.bin"]))
        self.assertIsNone(firmware_path_for_legacy_arguments(["NT51932BASED_NORMAL_MODE", "CRC8"]))
