"""Function-level port of NT51930 CRC field generation."""

from __future__ import annotations

from nvt_combiner.primitives.c_semantics import read_u16_le, read_u32_le, write_u32_le
from nvt_combiner.primitives.checksum import cal_crc


_U32_BYTES = 4

# NT51930 common-header layout.
_HEADER_CRC_OFFSET = 0x7100
_HEADER_CRC_START_OFFSET = 0x7104
_HEADER_CRC_SIZE_CODE = 0x23
_ILM_SIZE_CODE_OFFSET = 0x7108
_ILM_CRC_OFFSET = 0x710C
_DLM_SIZE_CODE_OFFSET = 0x7114
_DLM_CRC_OFFSET = 0x7118
_DLM_DIFF_SIZE_CODE_OFFSET = 0x7120
_IC_NUMBER_OFFSET = 0x7123
_DLM_DIFF_CRC_TABLE_OFFSET = 0x7128
_ILM_START_OFFSET = 0x7198
_DLM_START_OFFSET = 0x719C
_DLM_DIFF_START_OFFSET = 0x71A0


def calculate_crc_fields(method: str, buffer: bytearray) -> None:
    """Port NT51930 ILM/DLM, DLM-diff and common-header CRC writes."""
    print("--------------------------------------")
    ilm_address = read_u32_le(buffer, _ILM_START_OFFSET)
    ilm_size_code = read_u32_le(buffer, _ILM_SIZE_CODE_OFFSET)
    ilm_crc = cal_crc(method, ilm_address, ilm_size_code, buffer)
    write_u32_le(buffer, _ILM_CRC_OFFSET, ilm_crc)
    print(f"ILM0 CRC :{ilm_crc:4x}")

    dlm_address = read_u32_le(buffer, _DLM_START_OFFSET)
    dlm_size_code = read_u32_le(buffer, _DLM_SIZE_CODE_OFFSET)
    dlm_crc = cal_crc(method, dlm_address, dlm_size_code, buffer)
    write_u32_le(buffer, _DLM_CRC_OFFSET, dlm_crc)
    print(f"DLM0 CRC :{dlm_crc:4x}")

    ic_number = buffer[_IC_NUMBER_OFFSET]
    diff_start_address = read_u32_le(buffer, _DLM_DIFF_START_OFFSET)
    diff_size = read_u16_le(buffer, _DLM_DIFF_SIZE_CODE_OFFSET) + 1
    for index in range(ic_number - 1):
        crc = cal_crc(method, diff_start_address + diff_size * index, diff_size - 1, buffer)
        write_u32_le(buffer, _DLM_DIFF_CRC_TABLE_OFFSET + _U32_BYTES * index, crc)
        print(f"DLM{index + 1:2d} CRC: 0x{crc:08X}")

    header_crc = cal_crc(method, _HEADER_CRC_START_OFFSET, _HEADER_CRC_SIZE_CODE, buffer)
    write_u32_le(buffer, _HEADER_CRC_OFFSET, header_crc)
    print("--------------------------------------")
    print(f"HEADER CRC: 0x{header_crc:08X}")
    print()
