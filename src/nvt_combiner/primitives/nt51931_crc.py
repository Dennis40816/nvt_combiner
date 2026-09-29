"""Function-level port of the NT51931 header and DLM-diff CRC routine."""

from __future__ import annotations

from nvt_combiner.primitives.c_semantics import read_u16_le, read_u32_le, write_u32_le
from nvt_combiner.primitives.checksum import cal_crc


_U32_BYTES = 4

# NT51931 common-header layout.
_SECTION_TABLE_FIRST_OFFSET = 0x30
_SECTION_TABLE_LAST_OFFSET = 0x50
_SECTION_TABLE_ENTRY_SIZE = 0x10
_SECTION_SIZE_OFFSET = 0x04
_SECTION_START_OFFSET = 0x08
_SECTION_CRC_OFFSET = 0x0C
_DLM_DIFF_START_OFFSET = 0x60
_DLM_DIFF_SIZE_CODE_OFFSET = 0x68
_IC_NUMBER_OFFSET = 0x6B
_DLM_DIFF_CRC_TABLE_OFFSET = 0x6C
_FW_HEADER_CRC_OFFSET = 0xFC
_FW_HEADER_START_OFFSET = 0xF8
_FW_HEADER_SIZE_CODE_OFFSET = 0xF4
_FW_HEADER_SIZE_EXCLUDED_CRC_BYTES = 4
_FW_HEADER_LOG_OFFSET = 0xF0


def calculate_diff_dlm_and_fw_header_crc(method: str, buffer: bytearray) -> None:
    """Port ``CalculateNt51931BasedDiffDlmCrcAndFwHeaderCrc``."""
    print("--------------------------------------")
    print("FW_HEADER_SECTIONADDRESS\tSIZE\t\tCRC")
    for offset in range(
        _SECTION_TABLE_FIRST_OFFSET,
        _SECTION_TABLE_LAST_OFFSET + 1,
        _SECTION_TABLE_ENTRY_SIZE,
    ):
        start_address = read_u32_le(buffer, offset + _SECTION_START_OFFSET)
        size = read_u32_le(buffer, offset + _SECTION_SIZE_OFFSET) + 1
        crc = cal_crc(method, start_address, size - 1, buffer)
        write_u32_le(buffer, offset + _SECTION_CRC_OFFSET, crc)
        print(f"0x{offset:02X}\t\t\t0x{start_address:08X}\t0x{size - 1:08X}\t0x{crc:08X}")

    diff_start_address = read_u32_le(buffer, _DLM_DIFF_START_OFFSET)
    diff_size = read_u16_le(buffer, _DLM_DIFF_SIZE_CODE_OFFSET) + 1
    ic_number = buffer[_IC_NUMBER_OFFSET]
    print("--------------------------------------")
    for index in range(ic_number):
        crc = cal_crc(method, diff_start_address + diff_size * index, diff_size - 1, buffer)
        write_u32_le(buffer, _DLM_DIFF_CRC_TABLE_OFFSET + _U32_BYTES * index, crc)
        print(f"DLM{index + 1:2d} CRC: 0x{crc:08X}")

    header_start_address = read_u32_le(buffer, _FW_HEADER_START_OFFSET)
    header_size_code = read_u32_le(buffer, _FW_HEADER_SIZE_CODE_OFFSET)
    if header_size_code == 0:
        print("size of header is ZERO  , bypass the Header CRC ")
        return

    header_size = header_size_code + 1 - _FW_HEADER_SIZE_EXCLUDED_CRC_BYTES
    header_crc = cal_crc(method, header_start_address, header_size - 1, buffer)
    write_u32_le(buffer, _FW_HEADER_CRC_OFFSET, header_crc)
    print("--------------------------------------")
    print("FW_HEADER\t\tADDRESS\t\tSIZE\t\tCRC")
    print(
        f"0x{_FW_HEADER_LOG_OFFSET:02X}\t\t\t0x{header_start_address:08X}"
        f"\t0x{header_size - 1:08X}\t0x{header_crc:08X}"
    )
    print()
