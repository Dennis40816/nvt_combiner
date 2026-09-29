"""Function-level ports for NT51928B header CRC fields."""

from __future__ import annotations

from nvt_combiner.primitives.c_semantics import read_u32_le, write_u32_le
from nvt_combiner.primitives.checksum import cal_crc


# NT51928B common-header layout.
_HEADER_CRC_OFFSET = 0xD130
_HEADER_CRC_START_OFFSET = 0xD100
_HEADER_CRC_SIZE_CODE = 0x2F
_ILM_SIZE_CODE_OFFSET = 0xD108
_ILM_CRC_OFFSET = 0xD10C
_DLM_START_OFFSET = 0xD110
_DLM_SIZE_CODE_OFFSET = 0xD118
_DLM_CRC_OFFSET = 0xD11C


def calculate_ilm_dlm_crc(method: str, buffer: bytearray) -> None:
    """Port ``NT51928B_CalculateIlmDlmCrc``."""
    print("--------------------------------------")
    ilm_crc = cal_crc(
        method,
        read_u32_le(buffer, _HEADER_CRC_START_OFFSET),
        read_u32_le(buffer, _ILM_SIZE_CODE_OFFSET),
        buffer,
    )
    write_u32_le(buffer, _ILM_CRC_OFFSET, ilm_crc)
    print(f"ILM0 CRC :{ilm_crc:4x}")

    dlm_crc = cal_crc(
        method,
        read_u32_le(buffer, _DLM_START_OFFSET),
        read_u32_le(buffer, _DLM_SIZE_CODE_OFFSET),
        buffer,
    )
    write_u32_le(buffer, _DLM_CRC_OFFSET, dlm_crc)
    print(f"DLM0 CRC :{dlm_crc:4x}")


def calculate_header_crc(method: str, buffer: bytearray) -> None:
    """Port ``NT51928B_CalculateHeaderCrc``."""
    header_crc = cal_crc(method, _HEADER_CRC_START_OFFSET, _HEADER_CRC_SIZE_CODE, buffer)
    write_u32_le(buffer, _HEADER_CRC_OFFSET, header_crc)
    print("--------------------------------------")
    print(f"HEADER CRC: 0x{header_crc:08X}")
    print()
