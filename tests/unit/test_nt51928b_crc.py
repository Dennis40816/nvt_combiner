from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.primitives.c_semantics import read_u32_le
from nvt_combiner.primitives.nt51928b_crc import calculate_header_crc, calculate_ilm_dlm_crc


def fixture() -> bytearray:
    buffer = bytearray(0x21000)
    for offset, value in ((0xD100, 0x10000), (0xD108, 3), (0xD110, 0x20000), (0xD118, 3)):
        buffer[offset : offset + 4] = value.to_bytes(4, "little")
    buffer[0x10000:0x10004] = b"ILM!"
    buffer[0x20000:0x20004] = b"DLM!"
    return buffer


class TestNt51928bCrcFunctions(unittest.TestCase):
    def test_writes_ilm_and_dlm_crc8_fields(self) -> None:
        buffer = fixture()
        output = StringIO()

        with redirect_stdout(output):
            calculate_ilm_dlm_crc("CRC8", buffer)

        self.assertEqual(0x8CCDDC4B, read_u32_le(buffer, 0xD10C))
        self.assertEqual(0xD5BF92F3, read_u32_le(buffer, 0xD11C))
        self.assertEqual(
            "--------------------------------------\nILM0 CRC :8ccddc4b\nDLM0 CRC :d5bf92f3\n",
            output.getvalue(),
        )

    def test_writes_header_crc_after_ilm_dlm_fields(self) -> None:
        buffer = fixture()
        with redirect_stdout(StringIO()):
            calculate_ilm_dlm_crc("CRC8", buffer)
        output = StringIO()

        with redirect_stdout(output):
            calculate_header_crc("CRC8", buffer)

        self.assertEqual(0x4FA116C4, read_u32_le(buffer, 0xD130))
        self.assertEqual("--------------------------------------\nHEADER CRC: 0x4FA116C4\n\n", output.getvalue())
