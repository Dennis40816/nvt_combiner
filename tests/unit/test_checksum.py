from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from nvt_combiner.primitives.checksum import cal_crc
from nvt_combiner.primitives.safety import InputValidationError


class LegacyCalCrcFunctionTests(unittest.TestCase):
    def test_crc8_method_uses_inclusive_crc8_algorithm(self) -> None:
        self.assertEqual(0xA97AFF4D, cal_crc("CRC8", 0, 0x0F, bytes(range(0x10))))

    def test_crc32_method_adds_one_to_the_size_code(self) -> None:
        self.assertEqual(0x081B46CA, cal_crc("CRC32", 0, 0x0F, bytes(range(0x10))))

    def test_crc32_method_bypasses_a_zero_size_code(self) -> None:
        self.assertEqual(0, cal_crc("CRC32", 0, 0, b"\xFF"))

    def test_unrecognized_method_follows_legacy_crc32_fallback(self) -> None:
        data = b"\x00\x01"
        self.assertEqual(0x151D1CA7, cal_crc("None", 0, 1, data))

    def test_crc8_rejects_a_range_past_the_buffer_end(self) -> None:
        with self.assertRaisesRegex(
            InputValidationError,
            r"CRC8: input range out of bounds; start=2, length=4, end=6, "
            r"buffer_size=4, available=2",
        ):
            cal_crc("CRC8", 2, 3, b"abcd")

    def test_crc32_rejects_a_range_past_the_buffer_end(self) -> None:
        with self.assertRaisesRegex(InputValidationError, r"CRC32: input range out of bounds"):
            cal_crc("CRC32", 2, 3, b"abcd")

    def test_crc_rejects_negative_size_code(self) -> None:
        with self.assertRaisesRegex(InputValidationError, r"CRC8 CRC: size_code must be >= 0; size_code=-1"):
            cal_crc("CRC8", 0, -1, b"")

        with self.assertRaisesRegex(InputValidationError, r"CRC32 CRC: size_code must be >= 0; size_code=-1"):
            cal_crc("CRC32", 0, -1, b"")
