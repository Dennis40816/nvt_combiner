from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from nvt_combiner.primitives.c_semantics import read_u16_le, read_u32_le, strtol, write_u32_le
from nvt_combiner.primitives.safety import InputValidationError


class LittleEndianFunctionTests(unittest.TestCase):
    def test_reads_unaligned_little_endian_words(self) -> None:
        buffer = b"\xFF\x34\x12\x78\x56\x34\x12"
        self.assertEqual(0x1234, read_u16_le(buffer, 1))
        self.assertEqual(0x12345678, read_u32_le(buffer, 3))

    def test_write_u32_replaces_only_the_target_word_and_wraps(self) -> None:
        buffer = bytearray(b"\xAA" * 8)
        write_u32_le(buffer, 2, 0x1_12345678)
        self.assertEqual(b"\xAA\xAA\x78\x56\x34\x12\xAA\xAA", bytes(buffer))

    def test_short_word_access_reports_the_exact_range(self) -> None:
        with self.assertRaisesRegex(
            InputValidationError,
            r"read_u32_le: word range out of bounds; start=2, length=4, end=6, "
            r"buffer_size=4, available=2",
        ):
            read_u32_le(b"abcd", 2)

        buffer = bytearray(b"abcd")
        with self.assertRaisesRegex(InputValidationError, r"write_u32_le: word range out of bounds"):
            write_u32_le(buffer, 2, 0x12345678)
        self.assertEqual(b"abcd", buffer)


class StrtolFunctionTests(unittest.TestCase):
    def test_explicit_hex_matches_legacy_block_address_parsing(self) -> None:
        self.assertEqual(0x1FC00, strtol("0x1fc00", 16))
        self.assertEqual(-0x20, strtol("  -20suffix", 16))

    def test_explicit_decimal_stops_at_the_first_non_digit(self) -> None:
        self.assertEqual(18944, strtol("18944 bytes", 10))
        self.assertEqual(0, strtol("not-a-number", 10))

    def test_base_zero_matches_ab_offset_forms(self) -> None:
        self.assertEqual(0x40000, strtol("0x40000", 0))
        self.assertEqual(8, strtol("010", 0))
        self.assertEqual(25, strtol("25", 0))
