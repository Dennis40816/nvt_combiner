"""Function-level ports for legacy generic normal-mode CRC fields."""

from __future__ import annotations

from nvt_combiner.primitives.c_semantics import read_u32_le, write_u32_le
from nvt_combiner.primitives.checksum import cal_crc
from nvt_combiner.primitives.safety import validate_range


def calculate_ilm0_dlm0_crc(method: str, buffer: bytearray, offset: int) -> None:
    """Port ``Cal_ILM0_DLM0_CRC`` including its observable writes/output."""
    validate_range(
        len(buffer),
        offset,
        32,
        context="generic ILM/DLM CRC",
        range_name="header fields",
    )
    print("--------------------------------------")

    ilm_address = read_u32_le(buffer, offset)
    ilm_size = read_u32_le(buffer, offset + 8)
    ilm_crc = cal_crc(method, ilm_address, ilm_size, buffer)
    write_u32_le(buffer, offset + 24, ilm_crc)
    print(f"ILM0 CRC :{ilm_crc:4x}")

    dlm_address = read_u32_le(buffer, offset + 12)
    dlm_size = read_u32_le(buffer, offset + 20)
    dlm_crc = cal_crc(method, dlm_address, dlm_size, buffer)
    write_u32_le(buffer, offset + 28, dlm_crc)
    print(f"DLM0 CRC :{dlm_crc:4x}")


def _two_u32_are_zero(buffer: bytes | bytearray, offset: int) -> bool:
    """Equivalent to the legacy unaligned ``long long`` zero comparison."""
    return read_u32_le(buffer, offset) == 0 and read_u32_le(buffer, offset + 4) == 0


def calculate_dlm_crc(method: str, buffer: bytearray, offset: int, header_size: int) -> None:
    """Port ``CalculateDLMCRC`` including table and header CRC writes."""
    validate_range(
        len(buffer),
        offset,
        header_size,
        context="generic DLM CRC",
        range_name="header",
    )
    # Each DLM descriptor is split across parallel low/high tables in this
    # header format; advancing both cursors preserves the original pairing.
    offset_low = offset + 0x30
    offset_high = offset + 0x38
    header_end_entry = offset + header_size - 16

    print("--------------------------------------")
    print("DLM_BinAddr  Size   CRC")
    while True:
        if (
            # A zero pair is the table terminator.  The final header slot is
            # also reserved for header metadata and must never be a DLM row.
            (_two_u32_are_zero(buffer, offset_low) and _two_u32_are_zero(buffer, offset_high))
            or offset_low == header_end_entry
        ):
            break
        size = read_u32_le(buffer, offset_low + 4)
        start_address = read_u32_le(buffer, offset_high)
        crc = cal_crc(method, start_address, size, buffer)
        write_u32_le(buffer, offset_low + 12, crc)
        print(f"{start_address:4x}        {size:4x}    {crc:4x}")
        offset_low += 16
        offset_high += 16

    print("--------------------------------------")
    print("HeaderBinAddr  Size   CRC")
    start_address = read_u32_le(buffer, offset + header_size - 8)
    size = read_u32_le(buffer, offset + header_size - 12)
    if size == 0:
        # A zero size code is a legacy sentinel: leave the stored header CRC
        # untouched instead of calculating CRC over an empty range.
        print("size of header is ZERO  , bypass the Header CRC ")
        return

    size -= 4
    crc = cal_crc(method, start_address, size, buffer)
    write_u32_le(buffer, offset + header_size - 4, crc)
    print(f"{start_address:5x}           {size:4x}   {crc:8x}")
