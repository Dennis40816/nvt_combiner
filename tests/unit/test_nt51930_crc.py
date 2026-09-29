from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.primitives.c_semantics import read_u32_le
from nvt_combiner.primitives.nt51930_crc import calculate_crc_fields


def fixture() -> bytearray:
    buffer = bytearray(0x40000)
    for offset, value in (
        (0x7198, 0x10000), (0x7108, 0xF), (0x719C, 0x11000),
        (0x7114, 0xF), (0x71A0, 0x12000),
    ):
        buffer[offset : offset + 4] = value.to_bytes(4, "little")
    buffer[0x7120:0x7122] = (0xF).to_bytes(2, "little")
    buffer[0x7123] = 2
    for start in (0x10000, 0x11000, 0x12000):
        for index in range(16):
            buffer[start + index] = index
    return buffer


class TestNt51930CrcFunction(unittest.TestCase):
    def test_writes_ilm_dlm_diff_and_header_crc8_fields(self) -> None:
        buffer = fixture()
        output = StringIO()

        with redirect_stdout(output):
            calculate_crc_fields("CRC8", buffer)

        self.assertEqual(0xA97AFF4D, read_u32_le(buffer, 0x710C))
        self.assertEqual(0xA97AFF4D, read_u32_le(buffer, 0x7118))
        self.assertEqual(0xA97AFF4D, read_u32_le(buffer, 0x7128))
        self.assertEqual(0x77FCBC16, read_u32_le(buffer, 0x7100))
        self.assertEqual(
            "--------------------------------------\n"
            "ILM0 CRC :a97aff4d\n"
            "DLM0 CRC :a97aff4d\n"
            "DLM 1 CRC: 0xA97AFF4D\n"
            "--------------------------------------\n"
            "HEADER CRC: 0x77FCBC16\n\n",
            output.getvalue(),
        )

    def test_skips_dlm_diff_when_there_is_one_ic(self) -> None:
        buffer = fixture()
        buffer[0x7123] = 1

        with redirect_stdout(StringIO()):
            calculate_crc_fields("CRC8", buffer)

        self.assertEqual(0, read_u32_le(buffer, 0x7128))
