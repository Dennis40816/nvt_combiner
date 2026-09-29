"""Function-level primitives for observable MSVC C data semantics."""

from __future__ import annotations

import struct

from nvt_combiner.primitives.safety import validate_range


def read_u16_le(buffer: bytes | bytearray, offset: int) -> int:
    """Read the value produced by ``*(unsigned short *)(buffer + offset)``."""
    validate_range(len(buffer), offset, 2, context="read_u16_le", range_name="word")
    return struct.unpack_from("<H", buffer, offset)[0]


def read_u32_le(buffer: bytes | bytearray, offset: int) -> int:
    """Read the value produced by ``*(unsigned int *)(buffer + offset)``."""
    validate_range(len(buffer), offset, 4, context="read_u32_le", range_name="word")
    return struct.unpack_from("<I", buffer, offset)[0]


def write_u32_le(buffer: bytearray, offset: int, value: int) -> None:
    """Store the low 32 bits like legacy assignment through ``unsigned int *``."""
    validate_range(len(buffer), offset, 4, context="write_u32_le", range_name="word")
    struct.pack_into("<I", buffer, offset, value & 0xFFFFFFFF)


def strtol(text: str, base: int) -> int:
    """Implement the subset of MSVC ``strtol`` used by legacy CLI arguments.

    It intentionally accepts leading whitespace/signs and stops at the first
    invalid digit.  Overflow and invalid-address behavior are outside the
    supported legacy invocation contract and remain the caller's concern.
    """
    if base not in (0, 10, 16):
        raise ValueError("supported bases are 0, 10, and 16")

    source = text.lstrip()
    sign = 1
    if source.startswith(("+", "-")):
        if source[0] == "-":
            sign = -1
        source = source[1:]

    effective_base = base
    if base == 0:
        if source[:2].lower() == "0x":
            effective_base = 16
            source = source[2:]
        elif source.startswith("0"):
            effective_base = 8
        else:
            effective_base = 10
    elif base == 16 and source[:2].lower() == "0x":
        source = source[2:]

    value = 0
    found_digit = False
    for character in source:
        if "0" <= character <= "9":
            digit = ord(character) - ord("0")
        elif "a" <= character.lower() <= "z":
            digit = ord(character.lower()) - ord("a") + 10
        else:
            break
        if digit >= effective_base:
            break
        value = value * effective_base + digit
        found_digit = True

    return sign * value if found_digit else 0
