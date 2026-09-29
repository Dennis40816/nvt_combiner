"""NT51927 CRC-only mode."""

from __future__ import annotations

from pathlib import Path

from nvt_combiner.primitives.c_semantics import read_u32_le, write_u32_le
from nvt_combiner.primitives.checksum import cal_crc
from nvt_combiner.primitives.files import write_file
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import InputValidationError, copy_exact, validate_range


MODE = "NT51927BASED_GEN_CRC_MODE"
_NULL = 0xFFFFFFFF
_RAM_SIZE = 0xFFFFFF


def run(arguments: list[str]) -> int:
    """Generate NT51927 common, section and linked-header CRC fields."""
    if len(arguments) != 4:
        print(f"argument number error. Expected: 4. Actual: {len(arguments)}")
        return RUNTIME_FAIL
    method, input_path, output_path = arguments[1:4]
    if method not in ("CRC8", "CRC32"):
        print(f"CRC_method invalid. Expected: CRC8 or CRC32. Actual: {method}")
        return RUNTIME_FAIL
    try:
        buffer = bytearray(Path(input_path).read_bytes())
    except OSError:
        print(f"Open {input_path} failed. errno_t: 2")
        return RUNTIME_FAIL

    print(f"bin size: {len(buffer)}-byte")
    if len(buffer) < 0x220:
        print("The length of bin file is too short to get common header.")
        return RUNTIME_FAIL
    common_crc = cal_crc(method, 0x200, 27, buffer)
    print(f"Common Header CRC(@ 0x00200): 0x{common_crc:08X}")
    write_u32_le(buffer, 0x21C, common_crc)

    # The legacy algorithm reconstructs three independent target-RAM images
    # before calculating per-IC section CRCs; these buffers are not output.
    ram_m, ram_l, ram_r = bytearray(_RAM_SIZE), bytearray(_RAM_SIZE), bytearray(_RAM_SIZE)
    header_index = 0
    header = 0x220
    visited_headers: set[int] = set()
    while True:
        if header in visited_headers:
            raise InputValidationError(
                f"NT51927 flash-header chain contains a cycle; "
                f"header_index={header_index}, header=0x{header:X}"
            )
        visited_headers.add(header)
        validate_range(
            len(buffer),
            header,
            48,
            context=f"NT51927 flash header[{header_index}]",
            range_name="header",
        )
        ic_loc = buffer[header + 32]
        # Header bits select which of M/L/R receives this flash section.
        targets = ((ic_loc >> 1 & 1, ram_m, "M"), (ic_loc >> 2 & 1, ram_l, "L"), (ic_loc >> 3 & 1, ram_r, "R"))
        for start_offset, dest_offset, size_offset, crc_offset, label in ((0, 4, 8, 12, "ILM"), (16, 20, 24, 28, "DLM")):
            start = read_u32_le(buffer, header + start_offset)
            destination = read_u32_le(buffer, header + dest_offset)
            size = read_u32_le(buffer, header + size_offset) + 1
            if start != _NULL:
                validate_range(
                    len(buffer),
                    start,
                    size,
                    context=f"NT51927 flash header[{header_index}] {label}",
                    range_name="flash source",
                )
                if destination == _NULL:
                    raise InputValidationError(
                        f"NT51927 flash header[{header_index}] {label}: "
                        f"destination is NULL while source=0x{start:X} and size={size}"
                    )
                validate_range(
                    _RAM_SIZE,
                    destination,
                    size,
                    context=f"NT51927 flash header[{header_index}] {label}",
                    range_name="RAM destination",
                )
                for enabled, ram, _ in targets:
                    if enabled:
                        copy_exact(
                            ram,
                            destination,
                            buffer,
                            start,
                            size,
                            context=f"NT51927 flash header[{header_index}] {label}",
                        )
            if destination != _NULL:
                validate_range(
                    _RAM_SIZE,
                    destination,
                    size,
                    context=f"NT51927 flash header[{header_index}] {label}",
                    range_name="RAM CRC",
                )
                crc = 0
                for enabled, ram, suffix in targets:
                    if enabled:
                        crc = cal_crc(method, destination, size - 1, ram)
                        print(f"IC_{suffix} {label} CRC of Flash Header#{header_index}: 0x{crc:08X}")
                write_u32_le(buffer, header + crc_offset, crc)

        crc = cal_crc(method, header, 43, buffer)
        print(f"Flash Header#{header_index} CRC(@ 0x{header:05X}): 0x{crc:08X}")
        write_u32_le(buffer, header + 44, crc)
        header_index += 1
        # Flash headers form a linked list; 0xFFFFFFFF terminates the chain.
        header = read_u32_le(buffer, header + 40)
        if header == _NULL:
            break
    if write_file(output_path, buffer) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    return RUNTIME_SUCCESS
