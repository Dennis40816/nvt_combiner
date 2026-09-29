"""Legacy common-header decoding primitives."""

from __future__ import annotations

from nvt_combiner.primitives.c_semantics import read_u32_le
from nvt_combiner.primitives.safety import validate_range


def decode_one_header_size(buffer: bytes | bytearray) -> int | None:
    """Return legacy ``HeaderSize`` or ``None`` when no qualifying section exists."""
    validate_range(len(buffer), 0, 4, context="generic header", range_name="header-size field")
    maximum = read_u32_le(buffer, 0)
    for offset in range(0x30, maximum, 0x10):
        validate_range(
            len(buffer),
            offset,
            12,
            context="generic header",
            range_name=f"section descriptor at 0x{offset:X}",
        )
        length = read_u32_le(buffer, offset + 4)
        bin_address = read_u32_le(buffer, offset + 8)
        if bin_address == 0 and length != 0:
            return length + 1
    return None
