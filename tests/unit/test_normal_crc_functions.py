from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.primitives.c_semantics import read_u32_le
from nvt_combiner.primitives.normal_crc import calculate_dlm_crc, calculate_ilm0_dlm0_crc


def fixture() -> bytearray:
    buffer = bytearray(0x200)
    buffer[0:4] = (0x80).to_bytes(4, "little")
    buffer[8:12] = (3).to_bytes(4, "little")
    buffer[12:16] = (0x100).to_bytes(4, "little")
    buffer[20:24] = (3).to_bytes(4, "little")
    buffer[0x34:0x38] = (0x7F).to_bytes(4, "little")
    for index in range(32):
        buffer[0x80 + index] = 0x40 + index
        buffer[0x100 + index] = 0x80 + index
    return buffer


class TestGenericNormalCrcFunctions(unittest.TestCase):
    def test_calculates_ilm_and_dlm_crc8_fields(self) -> None:
        buffer = fixture()
        output = StringIO()

        with redirect_stdout(output):
            calculate_ilm0_dlm0_crc("CRC8", buffer, 0)

        self.assertEqual(0xB9956484, read_u32_le(buffer, 0x18))
        self.assertEqual(0xCA5D8FC1, read_u32_le(buffer, 0x1C))
        self.assertEqual(
            "--------------------------------------\n"
            "ILM0 CRC :b9956484\n"
            "DLM0 CRC :ca5d8fc1\n",
            output.getvalue(),
        )

    def test_calculates_dlm_table_crc_and_bypasses_zero_header_crc(self) -> None:
        buffer = fixture()
        with redirect_stdout(StringIO()):
            calculate_ilm0_dlm0_crc("CRC8", buffer, 0)
        output = StringIO()

        with redirect_stdout(output):
            calculate_dlm_crc("CRC8", buffer, 0, 0x80)

        self.assertEqual(0x02F4E7D0, read_u32_le(buffer, 0x3C))
        self.assertEqual(
            "--------------------------------------\n"
            "DLM_BinAddr  Size   CRC\n"
            "   0          7f    2f4e7d0\n"
            "--------------------------------------\n"
            "HeaderBinAddr  Size   CRC\n"
            "size of header is ZERO  , bypass the Header CRC \n",
            output.getvalue(),
        )
