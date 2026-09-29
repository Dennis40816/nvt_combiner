"""NT51950 A/B merge orchestration."""

from __future__ import annotations

from nvt_combiner.primitives.c_semantics import read_u32_le, strtol, write_u32_le
from nvt_combiner.primitives.checksum import cal_crc
from nvt_combiner.primitives.files import read_file, write_file
from nvt_combiner.primitives.overlay import calculate_overlay_crc, write_host_dlm_addresses, write_overlay_count
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import copy_exact, validate_non_negative, validate_range
from nvt_combiner.modes.legacy_io import merge_firmware_and_blocks, prepare_map_based_normal_input


AB_MODE = "NT51950BASED_MERGE_AB_MODE"
NORMAL_MODE = "NT51950BASED_NORMAL_MODE"
_CRC_METHODS = ("CRC8", "CRC32")

# NT51950 common-header layout.
_OVERLAY_INFO_OFFSET = 0xA028
_FW_CONFIG_SOURCE_OFFSET = 0xA038
_HEADER_START_OFFSET = 0xA100
_ILM_SIZE_CODE_OFFSET = 0xA108
_ILM_CRC_OFFSET = 0xA10C
_DLM_START_OFFSET = 0xA110
_DLM_SIZE_CODE_OFFSET = 0xA118
_DLM_CRC_OFFSET = 0xA11C
_HEADER_CRC_OFFSET = 0xA130
_HEADER_CRC_SIZE_CODE = 0x2F
_FW_CONFIG_DESTINATION = 0x36000
_FW_CONFIG_SIZE = 1920


def run_merge_ab(arguments: list[str]) -> int:
    """Run the legacy NT51950 A/B merge mode with its original argv shape."""
    legacy_argc = len(arguments) + 1
    if legacy_argc != 7:
        print(f"Parameter count error. Expected: 7. But was: {legacy_argc}")
        return RUNTIME_FAIL

    crc_method, a_code_path, b_code_path, output_path, offset_text = arguments[1:6]
    b_code_offset = validate_non_negative(
        strtol(offset_text, 0),
        context="NT51950 A/B merge",
        field_name="b_code_offset",
    )
    print("Start to Merge...")

    a_status, a_code = read_file(a_code_path)
    if a_status != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    b_status, b_code = read_file(b_code_path)
    if b_status != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    assert a_code is not None and b_code is not None

    if len(a_code) > b_code_offset:
        print(
            f"Detect overlap: A Code File Size: 0x{len(a_code):X}. "
            f"B Code Offset: 0x{b_code_offset:X}.",
            end="",
        )
        return RUNTIME_FAIL

    validate_range(
        len(b_code),
        _HEADER_START_OFFSET,
        _HEADER_CRC_OFFSET + 4 - _HEADER_START_OFFSET,
        context=f'NT51950 B code file="{b_code_path}"',
        range_name="CRC header",
    )

    output = bytearray(b_code_offset + len(b_code))
    copy_exact(output, 0, a_code, 0, len(a_code), context="NT51950 A code")
    copy_exact(output, b_code_offset, b_code, 0, len(b_code), context="NT51950 B code")

    ilm_offset = b_code_offset + _HEADER_START_OFFSET
    dlm_offset = b_code_offset + _DLM_START_OFFSET
    write_u32_le(output, ilm_offset, b_code_offset + read_u32_le(output, ilm_offset))
    write_u32_le(output, dlm_offset, b_code_offset + read_u32_le(output, dlm_offset))

    print("Calculate Header CRC...")
    header_start = b_code_offset + _HEADER_START_OFFSET
    header_crc = cal_crc(crc_method, header_start, _HEADER_CRC_SIZE_CODE, output)
    write_u32_le(output, b_code_offset + _HEADER_CRC_OFFSET, header_crc)
    print("--------------------------------------")
    print(f"HEADER CRC: 0x{header_crc:08X}")
    print()

    if write_file(output_path, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    return RUNTIME_SUCCESS


def run_normal(arguments: list[str]) -> int:
    """Run NT51950 normal merge, config relocation and optional CRC updates."""
    method, output_path, firmware_path = arguments[1:4]
    print(f"FwFilePath: {firmware_path}")
    preparation = prepare_map_based_normal_input(firmware_path, arguments[4:], len(arguments) + 1, 9)
    if preparation.status != RUNTIME_SUCCESS:
        return preparation.status
    prepared = preparation.input
    assert prepared is not None
    map_text = prepared.overlay_map.text
    overlay_info = prepared.overlay_map.info
    output = merge_firmware_and_blocks(prepared.firmware, prepared.blocks)
    print(f"Create a buffer with size = {len(output)}-byte (0x{len(output):X})")
    validate_range(
        len(output),
        _FW_CONFIG_SOURCE_OFFSET,
        4,
        context="NT51950",
        range_name="FW config source field",
    )
    config_source = read_u32_le(output, _FW_CONFIG_SOURCE_OFFSET)
    copy_exact(
        output,
        _FW_CONFIG_DESTINATION,
        output,
        config_source,
        _FW_CONFIG_SIZE,
        context="NT51950 FW config",
    )
    print(
        f"Copy FwConfig from 0x{config_source:X} to 0x{_FW_CONFIG_DESTINATION:X}. "
        f"Size: {_FW_CONFIG_SIZE}-byte."
    )
    if method in _CRC_METHODS:
        write_overlay_count(output, _OVERLAY_INFO_OFFSET, overlay_info.count)
        write_host_dlm_addresses(output, _OVERLAY_INFO_OFFSET, map_text)
        calculate_overlay_crc(method, output, _DLM_START_OFFSET, overlay_info.count)
        ilm = read_u32_le(output, _HEADER_START_OFFSET)
        ilm_crc = cal_crc(method, ilm, read_u32_le(output, _ILM_SIZE_CODE_OFFSET), output)
        write_u32_le(output, _ILM_CRC_OFFSET, ilm_crc)
        dlm = read_u32_le(output, _DLM_START_OFFSET)
        dlm_crc = cal_crc(method, dlm, read_u32_le(output, _DLM_SIZE_CODE_OFFSET), output)
        write_u32_le(output, _DLM_CRC_OFFSET, dlm_crc)
        print("--------------------------------------")
        print(f"ILM0 CRC :{ilm_crc:4x}")
        print(f"DLM0 CRC :{dlm_crc:4x}")
        header_crc = cal_crc(method, _HEADER_START_OFFSET, _HEADER_CRC_SIZE_CODE, output)
        write_u32_le(output, _HEADER_CRC_OFFSET, header_crc)
        print("--------------------------------------")
        print(f"HEADER CRC: 0x{header_crc:08X}")
        print()
    else:
        print("CRC Disable...")
    if write_file(output_path, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    print("FW Merge is OK")
    return RUNTIME_SUCCESS
