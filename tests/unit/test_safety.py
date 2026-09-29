from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from nvt_combiner.primitives.safety import (
    InputValidationError,
    copy_exact,
    validate_non_negative,
    validate_range,
)


class RangeValidationTests(unittest.TestCase):
    def test_rejects_a_negative_cli_number_with_its_field_name(self) -> None:
        with self.assertRaisesRegex(
            InputValidationError,
            r"block\[0\]: destination must be >= 0; destination=-1",
        ):
            validate_non_negative(-1, context="block[0]", field_name="destination")

    def test_accepts_an_exact_range_and_returns_its_slice(self) -> None:
        self.assertEqual(slice(2, 6), validate_range(8, 2, 4, context="block", range_name="source"))

    def test_accepts_a_zero_length_legacy_no_op_beyond_the_buffer(self) -> None:
        self.assertEqual(slice(272, 272), validate_range(0, 272, 0, context="block", range_name="source"))

    def test_rejects_negative_start_with_actionable_context(self) -> None:
        with self.assertRaisesRegex(
            InputValidationError,
            r"block: source start must be >= 0; start=-1, length=4, buffer_size=8",
        ):
            validate_range(8, -1, 4, context="block", range_name="source")

    def test_rejects_negative_length_with_actionable_context(self) -> None:
        with self.assertRaisesRegex(
            InputValidationError,
            r"block: source length must be >= 0; start=0, length=-1, buffer_size=8",
        ):
            validate_range(8, 0, -1, context="block", range_name="source")

    def test_rejects_a_range_past_the_end_with_available_size(self) -> None:
        with self.assertRaisesRegex(
            InputValidationError,
            r"block: source range out of bounds; start=6, length=4, end=10, "
            r"buffer_size=8, available=2",
        ):
            validate_range(8, 6, 4, context="block", range_name="source")


class ExactCopyTests(unittest.TestCase):
    def test_replaces_only_the_requested_range_without_resizing(self) -> None:
        destination = bytearray(b"ABCDEFGH")

        copy_exact(destination, 2, b"wxyz", 0, 4, context="block[0]")

        self.assertEqual(8, len(destination))
        self.assertEqual(b"ABwxyzGH", destination)

    def test_short_source_rejects_without_mutating_destination(self) -> None:
        destination = bytearray(b"ABCDEFGH")

        with self.assertRaisesRegex(InputValidationError, r"block\[0\]: source range out of bounds"):
            copy_exact(destination, 2, b"xy", 0, 4, context="block[0]")

        self.assertEqual(b"ABCDEFGH", destination)

    def test_past_end_destination_rejects_without_appending(self) -> None:
        destination = bytearray(b"ABCDEFGH")

        with self.assertRaisesRegex(InputValidationError, r"config: destination range out of bounds"):
            copy_exact(destination, 8, b"xy", 0, 2, context="config")

        self.assertEqual(b"ABCDEFGH", destination)

    def test_zero_length_copy_with_legacy_addresses_is_a_no_op(self) -> None:
        destination = bytearray(b"ABCDEFGH")

        copy_exact(destination, 272, b"", 272, 0, context="empty block")

        self.assertEqual(b"ABCDEFGH", destination)


if __name__ == "__main__":
    unittest.main()
