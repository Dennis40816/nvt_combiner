from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.primitives.c_semantics import read_u32_le
from nvt_combiner.primitives.nt51931_crc import calculate_diff_dlm_and_fw_header_crc


def fixture() -> bytearray:
    buffer = bytearray(0x400)
    for offset, value in (
        (0x34, 3), (0x38, 0x120), (0x44, 3), (0x48, 0x130),
        (0x54, 3), (0x58, 0x140), (0x60, 0x150), (0xF4, 7), (0xF8, 0x160),
    ):
        buffer[offset : offset + 4] = value.to_bytes(4, "little")
    buffer[0x68:0x6A] = (3).to_bytes(2, "little")
    buffer[0x6B] = 2
    for start in (0x120, 0x130, 0x140, 0x150, 0x154, 0x160):
        for index in range(4):
            buffer[start + index] = (start + index) & 0xFF
    return buffer


class TestNt51931CrcFunction(unittest.TestCase):
    def test_writes_section_diff_and_header_crc8_fields(self) -> None:
        buffer = fixture()
        output = StringIO()

        with redirect_stdout(output):
            calculate_diff_dlm_and_fw_header_crc("CRC8", buffer)

        self.assertEqual(0x02119FFD, read_u32_le(buffer, 0x3C))
        self.assertEqual(0xB4CF3A4D, read_u32_le(buffer, 0x4C))
        self.assertEqual(0xB9956484, read_u32_le(buffer, 0x5C))
        self.assertEqual(0x0F4BC134, read_u32_le(buffer, 0x6C))
        self.assertEqual(0x22FC6858, read_u32_le(buffer, 0x70))
        self.assertEqual(0xD0E93253, read_u32_le(buffer, 0xFC))
        self.assertEqual(
            "--------------------------------------\n"
            "FW_HEADER_SECTIONADDRESS\tSIZE\t\tCRC\n"
            "0x30\t\t\t0x00000120\t0x00000003\t0x02119FFD\n"
            "0x40\t\t\t0x00000130\t0x00000003\t0xB4CF3A4D\n"
            "0x50\t\t\t0x00000140\t0x00000003\t0xB9956484\n"
            "--------------------------------------\n"
            "DLM 1 CRC: 0x0F4BC134\n"
            "DLM 2 CRC: 0x22FC6858\n"
            "--------------------------------------\n"
            "FW_HEADER\t\tADDRESS\t\tSIZE\t\tCRC\n"
            "0xF0\t\t\t0x00000160\t0x00000003\t0xD0E93253\n\n",
            output.getvalue(),
        )

    def test_bypasses_zero_size_fw_header(self) -> None:
        buffer = fixture()
        buffer[0xF4:0xF8] = b"\0\0\0\0"
        output = StringIO()

        with redirect_stdout(output):
            calculate_diff_dlm_and_fw_header_crc("CRC8", buffer)

        self.assertEqual(0, read_u32_le(buffer, 0xFC))
        self.assertTrue(output.getvalue().endswith("size of header is ZERO  , bypass the Header CRC \n"))
