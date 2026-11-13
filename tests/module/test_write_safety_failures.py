from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.module.test_nt51927_crc import fixture as write_nt51927_fixture
from tests.module.test_nt51928b import MODE as NT51928B_MODE, write_case as write_nt51928b_case
from tests.module.test_nt51932_no_overlay import write_fixture as write_nt51932_fixture
from tests.support.differential import run_python


class WriteSafetyFailureModuleTests(unittest.TestCase):
    def test_generic_block_source_overrun_keeps_firmware_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            firmware = root / "fw.bin"
            firmware.write_bytes(b"original firmware")
            (root / "block.bin").write_bytes(b"012345")
            (root / "map.txt").write_bytes(b"")
            original = firmware.read_bytes()

            result = run_python(
                ["CRC_Disable", "fw.bin", "block.bin", "4", "0", "4"],
                root,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn(
                'Validation error: block[0] file="block.bin": source range out of bounds; '
                "start=4, length=4, end=8, buffer_size=6, available=2",
                result.stdout,
            )
            self.assertEqual(original, firmware.read_bytes())
            self.assertFalse(any(root.glob(".fw.bin.*.tmp")))

    def test_merge_mode_source_overrun_does_not_create_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "block.bin").write_bytes(b"012345")

            result = run_python(
                ["MERGE_MODE", "output.bin", "block.bin", "4", "0", "4"],
                root,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn(
                'Validation error: MERGE_MODE block[0] file="block.bin": '
                "source range out of bounds; start=4, length=4, end=8, "
                "buffer_size=6, available=2",
                result.stdout,
            )
            self.assertFalse((root / "output.bin").exists())

    def test_negative_merge_destination_is_named_in_the_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "block.bin").write_bytes(b"0123")

            result = run_python(
                ["MERGE_MODE", "output.bin", "block.bin", "0", "-1", "4"],
                root,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn(
                'Validation error: MERGE_MODE block[0] file="block.bin": '
                "destination must be >= 0; destination=-1",
                result.stdout,
            )
            self.assertFalse((root / "output.bin").exists())

    def test_nt51932_config_overrun_reports_source_and_available_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            arguments = write_nt51932_fixture(root, b"", "None")
            firmware = bytearray((root / "fw.bin").read_bytes())
            firmware[0x7038:0x703C] = (0x3FF00).to_bytes(4, "little")
            (root / "fw.bin").write_bytes(firmware)

            result = run_python(arguments, root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn(
                "Validation error: NT51932 FW config: source range out of bounds; "
                "start=261888, length=4096, end=265984, buffer_size=262144, available=256",
                result.stdout,
            )
            self.assertFalse((root / "output.bin").exists())

    def test_nt51928b_small_firmware_is_rejected_before_any_config_write(self) -> None:
        # The C version writes past its buffer here (undefined behavior).
        cases = (
            (
                0x34000,
                "Validation error: NT51928B FW config: destination range out of bounds; "
                "start=209152, length=4092, end=213244, buffer_size=212992, available=3840",
            ),
            (
                0x340FC,
                "Validation error: NT51928B FW config end flag: destination range out of bounds; "
                "start=213244, length=4, end=213248, buffer_size=213244, available=0",
            ),
        )
        for firmware_size, message in cases:
            with self.subTest(firmware_size=hex(firmware_size)), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_nt51928b_case(root, firmware_size)

                result = run_python(
                    [NT51928B_MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"],
                    root,
                )

                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stdout)
                self.assertFalse((root / "out.bin").exists())

    def test_nt51928b_config_source_overrun_reports_available_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_nt51928b_case(root)
            firmware = bytearray((root / "fw.bin").read_bytes())
            firmware[0xD038:0xD03C] = (0x3E000).to_bytes(4, "little")
            (root / "fw.bin").write_bytes(firmware)

            result = run_python(
                [NT51928B_MODE, "CRC8", "out.bin", "fw.bin", "block.bin", "0x0", "0", "0"],
                root,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn(
                "Validation error: NT51928B FW config: source range out of bounds; "
                "start=253952, length=4092, end=258044, buffer_size=255872, available=1920",
                result.stdout,
            )
            self.assertFalse((root / "out.bin").exists())

    def test_nt51927_header_cycle_stops_before_output_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            arguments = write_nt51927_fixture(root, "CRC8")
            image = bytearray((root / "input.bin").read_bytes())
            image[0x248:0x24C] = (0x220).to_bytes(4, "little")
            (root / "input.bin").write_bytes(image)

            result = run_python(arguments, root)

            self.assertNotEqual(0, result.returncode)
            self.assertIn(
                "Validation error: NT51927 flash-header chain contains a cycle; "
                "header_index=1, header=0x220",
                result.stdout,
            )
            self.assertFalse((root / "output.bin").exists())


if __name__ == "__main__":
    unittest.main()
