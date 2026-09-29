from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from nvt_combiner.primitives.crc import crc8_alg, crc32_alg, legacy_crc8_alg


class LegacyCrc8AlgTests(unittest.TestCase):
    """Function-level vectors characterized with Combiner 1.13.0.0."""

    def test_ilm_crc8_vector_is_bit_for_bit_compatible(self) -> None:
        # Legacy reference fixture: bytes at 0x10000..0x1000F are 00..0F,
        # and the caller passes size code 0x0F (inclusive endpoint).
        self.assertEqual(0xA97AFF4D, crc8_alg(0, 0x0F, bytes(range(0x10))))

    def test_dlm_crc8_vector_is_bit_for_bit_compatible(self) -> None:
        # Legacy reference fixture: bytes at 0x11000..0x1100F are A0..AF.
        self.assertEqual(0x3C1D5899, crc8_alg(0, 0x0F, bytes(range(0xA0, 0xB0))))

    def test_all_ones_and_alternating_bit_vectors_are_compatible(self) -> None:
        self.assertEqual(0xA79C3203, crc8_alg(0, 0x0F, b"\xFF" * 16))
        self.assertEqual(0xF8FD261C, crc8_alg(0, 0x0F, b"\x55" * 16))

    def test_descending_high_and_low_nibbles_are_compatible(self) -> None:
        self.assertEqual(0x5BCBEF86, crc8_alg(0, 0x0F, bytes(range(0xFF, 0xEF, -1))))
        self.assertEqual(0x841F9BB8, crc8_alg(0, 0x0F, bytes(range(0x0F, -1, -1))))

    def test_address_offset_does_not_change_the_processed_sequence(self) -> None:
        payload = bytes(range(0x10))
        self.assertEqual(0xA97AFF4D, crc8_alg(1, 0x0F, b"\xFF" + payload))

    def test_clean_implementation_matches_the_frozen_legacy_state_machine(self) -> None:
        cases = (
            (0, 0xFF, bytes(range(0x100))),
            (3, 0x40, b"\x5A" * 3 + bytes(range(0x41))),
            (2, 0x1F, b"\x00\xFF" + b"\xAA\x55" * 16),
        )

        for address, size_code, buffer in cases:
            with self.subTest(address=address, size_code=size_code):
                self.assertEqual(
                    crc8_alg(address, size_code, buffer),
                    legacy_crc8_alg(address, size_code, buffer),
                )

    def test_crc32_full_little_endian_words_are_compatible(self) -> None:
        self.assertEqual(0x081B46CA, crc32_alg(0, 16, bytes(range(0x10))))
        self.assertEqual(0x9D7CE11E, crc32_alg(0, 16, bytes(range(0xA0, 0xB0))))

    def test_crc32_zero_pads_an_incomplete_final_word(self) -> None:
        self.assertEqual(0x151D1CA7, crc32_alg(0, 2, b"\x00\x01"))
        self.assertEqual(0x92EF2E79, crc32_alg(0, 3, b"\xA0\xA1\xA2"))
