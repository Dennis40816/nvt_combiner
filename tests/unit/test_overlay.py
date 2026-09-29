from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.primitives.c_semantics import read_u32_le
from nvt_combiner.primitives.overlay import calculate_overlay_crc, inspect_map, write_host_dlm_addresses, write_overlay_count


MAP = """?TEXT_SIZE: 0x0 0x2000)
_ovly_table =
entry 0x0 0x0 0x1000 end
size 0x0 0x0 0x10 end
skip
skip
_novlys = end
"""

MULTI_MAP = """?TEXT_SIZE: 0x0 0x3000)
_ovly_table =
entry 0x0 0x0 0x1000 end
size 0x0 0x0 0x10 end
skip
skip
entry 0x0 0x0 0x1100 end
size 0x0 0x0 0x20 end
skip
skip
_novlys = end
"""

OVER_LIMIT_MAP = """?TEXT_SIZE: 0x0 0x1010)
_ovly_table =
entry 0x0 0x0 0x1000 end
size 0x0 0x0 0x10 end
skip
skip
_novlys = end
"""

DLM_OVERLAY_MAP = """?TEXT_SIZE: 0x0 0x1000)
_ovly_table =
entry 0x0 0x0 0x1000 end
size 0x0 0x0 0x10 end
skip
skip
_novlys = end
"""

MISSING_TEXT_SIZE_VALUE_MAP = "?TEXT_SIZE: 0x0\n"
TEXT_SIZE_NO_OVERLAY_MAP = "?TEXT_SIZE: 0x0 0x2000)\n"
INVALID_TEXT_SIZE_VALUE_MAP = "?TEXT_SIZE: 0x0 0xZZ)\n"


def overlay_map_with_entry(entry: str) -> str:
    return f"?TEXT_SIZE: 0x0 0x2000)\n_ovly_table =\n{entry}\n"


class TestOverlayFunctions(unittest.TestCase):
    def test_inspects_a_valid_single_overlay_table(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            info = inspect_map(MAP)

        self.assertIsNotNone(info)
        assert info is not None
        self.assertEqual((1, True), (info.count, info.has_overlay))
        self.assertEqual(
            "ILM_LimitSize = 0x2000\n"
            "RAM_BaseAddr  = 1000\n"
            "section size  = 10\n"
            "RAM_BaseAddr + Section_size = 1010\n"
            "FW pass overlay check.\n",
            output.getvalue(),
        )

    def test_marks_overlay_count_and_writes_crc8_descriptor(self) -> None:
        buffer = bytearray(0x200)
        buffer[0x28] = 0xA0
        buffer[12:16] = (0x100).to_bytes(4, "little")
        buffer[0x104:0x108] = (4).to_bytes(4, "little")
        buffer[0x108:0x10C] = (0x180).to_bytes(4, "little")
        buffer[0x180:0x184] = bytes(range(0xA0, 0xA4))
        write_overlay_count(buffer, 0x28, 1)
        output = StringIO()

        with redirect_stdout(output):
            calculate_overlay_crc("CRC8", buffer, 12, 1)

        self.assertEqual(0xA1, buffer[0x28])
        self.assertEqual(3, read_u32_le(buffer, 0x104))
        self.assertEqual(0xA321D916, read_u32_le(buffer, 0x10C))
        self.assertEqual(
            "--------------------------------------\n"
            "OverlayAddr  Size   CRC\n"
            " 180           3    a321d916\n",
            output.getvalue(),
        )

    def test_overlay_count_write_wraps_to_a_legacy_byte(self) -> None:
        buffer = bytearray(b"\xA5")

        write_overlay_count(buffer, 0, 0x100)

        self.assertEqual(0xA0, buffer[0])

    def test_inspects_multiple_overlay_descriptors(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            info = inspect_map(MULTI_MAP)

        self.assertIsNotNone(info)
        assert info is not None
        self.assertEqual((2, True), (info.count, info.has_overlay))
        self.assertEqual(
            "ILM_LimitSize = 0x3000\n"
            "RAM_BaseAddr  = 1000\n"
            "section size  = 10\n"
            "RAM_BaseAddr + Section_size = 1010\n"
            "RAM_BaseAddr  = 1100\n"
            "section size  = 20\n"
            "RAM_BaseAddr + Section_size = 1120\n"
            "FW pass overlay check.\n",
            output.getvalue(),
        )

    def test_writes_host_dlm_address_at_legacy_table_offset(self) -> None:
        buffer = bytearray(0x200)
        buffer[12:16] = (0x100).to_bytes(4, "little")
        buffer[0x28] = 0x10
        write_overlay_count(buffer, 0x28, 2)
        map_text = "OverlayDLMaddr\n0123456789012345670x00000184\nskip\nskip\n"
        output = StringIO()

        with redirect_stdout(output):
            write_host_dlm_addresses(buffer, 0x28, map_text)

        self.assertEqual(0x12, buffer[0x28])
        self.assertEqual(1, read_u32_le(buffer, 0x110))
        self.assertEqual("OverlayDLMaddr1 : 1\n", output.getvalue())

    def test_rejects_overlay_at_or_beyond_ilm_limit(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            info = inspect_map(OVER_LIMIT_MAP)

        self.assertIsNone(info)
        self.assertEqual(
            "ILM_LimitSize = 0x1010\n"
            "RAM_BaseAddr  = 1000\n"
            "section size  = 10\n"
            "RAM_BaseAddr + Section_size = 1010\n"
            "FW size overflow\n",
            output.getvalue(),
        )

    def test_skips_dlm_overlay_limit_check(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            info = inspect_map(DLM_OVERLAY_MAP)

        self.assertEqual((1, True), (info.count, info.has_overlay))
        self.assertEqual(
            "ILM_LimitSize = 0x1000\n"
            "RAM_BaseAddr  = 1000\n"
            "section size  = 10\n"
            "RAM_BaseAddr(0x1000) >= ILM_LimitSize(0x1000) ==> skip checking this overlay section.\n"
            "FW pass overlay check.\n",
            output.getvalue(),
        )

    def test_reports_missing_second_text_size_hex_value(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            info = inspect_map(MISSING_TEXT_SIZE_VALUE_MAP)

        self.assertIsNone(info)
        self.assertEqual(
            "Can't find the second hex value when decode IlmLimitSize, please check the format of map.txt: \n"
            "?TEXT_SIZE: 0x0\n\n",
            output.getvalue(),
        )

    def test_splits_long_map_lines_like_legacy_fgets(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            info = inspect_map("A" * 500 + "?TEXT_SIZE:\n")

        self.assertIsNone(info)
        self.assertEqual(
            "Can't find the first hex value when decode IlmLimitSize, please check the format of map.txt: \n"
            "A?TEXT_SIZE:\n\n",
            output.getvalue(),
        )

    def test_reports_ilm_limit_then_no_overlay(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            info = inspect_map(TEXT_SIZE_NO_OVERLAY_MAP)

        self.assertEqual((0, False), (info.count, info.has_overlay))
        self.assertEqual("ILM_LimitSize = 0x2000\nThis FW has no overlay.\n", output.getvalue())

    def test_uses_legacy_strtol_for_invalid_text_size_value(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            info = inspect_map(INVALID_TEXT_SIZE_VALUE_MAP)

        self.assertEqual((0, False), (info.count, info.has_overlay))
        self.assertEqual("ILM_LimitSize = 0x0\nThis FW has no overlay.\n", output.getvalue())

    def test_reports_which_overlay_hex_value_is_missing(self) -> None:
        cases = (("entry", "first"), ("entry 0x0", "second"), ("entry 0x0 0x0", "third"))
        for entry, ordinal in cases:
            with self.subTest(entry=entry):
                output = StringIO()
                with redirect_stdout(output):
                    info = inspect_map(overlay_map_with_entry(entry))

                self.assertIsNone(info)
                self.assertEqual(
                    "ILM_LimitSize = 0x2000\n"
                    f"Can't find the {ordinal} hex value when decode overlay info, please check the format of map.txt: \n"
                    f"{entry}\n\n",
                    output.getvalue(),
                )
