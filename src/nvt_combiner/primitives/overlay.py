"""Function-level no-host-DLM overlay helpers from legacy Combiner C."""

from __future__ import annotations

from dataclasses import dataclass

from nvt_combiner.primitives.c_semantics import read_u32_le, strtol, write_u32_le
from nvt_combiner.primitives.checksum import cal_crc
from nvt_combiner.primitives.map_text import legacy_fgets_records
from nvt_combiner.primitives.safety import validate_range


@dataclass(frozen=True)
class OverlayInfo:
    """The observable result of ``GetIlmLimitSize`` and ``CheckFwOverley``."""

    count: int
    has_overlay: bool


def _third_hex_value(line: str) -> tuple[int | None, int]:
    """Return the third legacy ``0x`` value and the count found in one line."""
    positions: list[int] = []
    start = 0
    while True:
        position = line.find("0x", start)
        if position < 0:
            break
        positions.append(position)
        start = position + 1
    if len(positions) < 3:
        return None, len(positions)
    text = line[positions[2] + 2 :]
    end = text.find(" ")
    if end >= 0:
        text = text[:end]
    try:
        return int(text[:6], 16), 3
    except ValueError:
        return 0, 3


def inspect_map(map_text: str) -> OverlayInfo | None:
    """Port map's ILM limit and overlay table check with C-compatible text."""
    lines = legacy_fgets_records(map_text)
    ilm_limit = 0
    for line in lines:
        if "?TEXT_SIZE:" not in line:
            continue
        first = line.find("0x")
        second = line.find("0x", first + 1) if first >= 0 else -1
        if first < 0:
            print(f"Can't find the first hex value when decode IlmLimitSize, please check the format of map.txt: \n{line}")
            return None
        if second < 0:
            print(f"Can't find the second hex value when decode IlmLimitSize, please check the format of map.txt: \n{line}")
            return None
        value_text = line[second + 2 :].split(")", 1)[0]
        ilm_limit = strtol(value_text[:6], 16)
        print(f"ILM_LimitSize = 0x{ilm_limit:x}")
        break

    for index, line in enumerate(lines):
        if "_ovly_table =" not in line:
            continue
        # The C parser consumes a fixed, presentation-oriented record shape;
        # do not turn this into a permissive general map-file parser.
        cursor = index + 1
        count = 0
        over_limit = False
        while cursor < len(lines):
            address_line = lines[cursor]
            cursor += 1
            if "_novlys = " in address_line:
                break
            ram_base_address, found_hex_values = _third_hex_value(address_line)
            if ram_base_address is None:
                ordinal = ("first", "second", "third")[found_hex_values]
                print(f"Can't find the {ordinal} hex value when decode overlay info, please check the format of map.txt: \n{address_line}")
                return None
            print(f"RAM_BaseAddr  = {ram_base_address:x}")
            if cursor >= len(lines):
                return None
            section_line = lines[cursor]
            cursor += 1
            section_size, found_hex_values = _third_hex_value(section_line)
            if section_size is None:
                ordinal = ("first", "second", "third")[found_hex_values]
                print(f"Can't find the {ordinal} hex value when decode overlay info, please check the format of map.txt: \n{section_line}")
                return None
            print(f"section size  = {section_size:x}")
            if ram_base_address >= ilm_limit:
                print(
                    f"RAM_BaseAddr(0x{ram_base_address:x}) >= ILM_LimitSize(0x{ilm_limit:x}) "
                    "==> skip checking this overlay section."
                )
            else:
                print(f"RAM_BaseAddr + Section_size = {ram_base_address + section_size:x}")
                if ram_base_address + section_size >= ilm_limit:
                    over_limit = True
            cursor += 2  # legacy parser consumes two formatting lines.
            count += 1
        if over_limit:
            print("FW size overflow")
            return None
        print("FW pass overlay check.")
        return OverlayInfo(count, True)

    print("This FW has no overlay.")
    return OverlayInfo(0, False)


def write_overlay_count(buffer: bytearray, info_index: int, overlay_count: int) -> None:
    """Port the non-HostDL portion of ``DecodeOverlayInfoAndWriteToFwBin``."""
    validate_range(len(buffer), info_index, 1, context="overlay info", range_name="count field")
    buffer[info_index] = ((buffer[info_index] & 0xF0) | overlay_count) & 0xFF


def write_host_dlm_addresses(buffer: bytearray, info_index: int, map_text: str) -> None:
    """Port HostDL/Process ``OverlayDLMaddr`` mutation literally.

    The legacy C code deliberately writes at ``DLM_DataStartAddr + i * 16``;
    this is not the descriptor's CRC-calculation start-address field.
    """
    validate_range(len(buffer), info_index, 1, context="HostDL overlay", range_name="info field")
    if ((buffer[info_index] >> 4) & 1) == 0:
        return
    validate_range(len(buffer), 12, 4, context="HostDL overlay", range_name="DLM start field")
    data_start_address = read_u32_le(buffer, 12)
    lines = legacy_fgets_records(map_text)
    overlay_index = 1
    cursor = 0
    while cursor < len(lines):
        line = lines[cursor]
        cursor += 1
        if "OverlayDLMaddr" not in line or cursor >= len(lines):
            continue
        overlay_address = strtol(lines[cursor][18:26], 16)
        cursor += 1
        destination = data_start_address + overlay_index * 16
        validate_range(
            len(buffer),
            destination,
            4,
            context=f"HostDL overlay[{overlay_index}]",
            range_name="DLM address field",
        )
        write_u32_le(buffer, destination, overlay_address)
        print(f"OverlayDLMaddr{overlay_index} : {overlay_address:x}")
        overlay_index += 1
        cursor += min(2, len(lines) - cursor)


def calculate_overlay_crc(method: str, buffer: bytearray, dlm_start_index: int, overlay_count: int) -> None:
    """Port ``CalculateOverlayCRC`` for ordinary overlay descriptor tables."""
    validate_range(len(buffer), dlm_start_index, 4, context="overlay CRC", range_name="DLM start field")
    data_start_address = read_u32_le(buffer, dlm_start_index)
    print("--------------------------------------")
    print("OverlayAddr  Size   CRC")
    # A populated first descriptor CRC is the legacy "already handled" path.
    # In that case the C implementation leaves every descriptor unchanged.
    validate_range(
        len(buffer),
        data_start_address,
        16,
        context="overlay CRC",
        range_name="first descriptor",
    )
    if read_u32_le(buffer, data_start_address + 12) != 0:
        return
    for index in range(overlay_count):
        descriptor = data_start_address + index * 16
        validate_range(
            len(buffer),
            descriptor,
            16,
            context=f"overlay CRC[{index}]",
            range_name="descriptor",
        )
        size = read_u32_le(buffer, descriptor + 4) - 1
        start_address = read_u32_le(buffer, descriptor + 8)
        crc = cal_crc(method, start_address, size, buffer)
        write_u32_le(buffer, descriptor + 12, crc)
        write_u32_le(buffer, descriptor + 4, size)
        print(f"{start_address:4x}        {size:4x}    {crc:4x}")
