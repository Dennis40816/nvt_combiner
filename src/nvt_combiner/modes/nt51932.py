"""NT51932 normal-mode orchestration built only from frozen primitives."""

from __future__ import annotations

from pathlib import Path

from nvt_combiner.primitives.c_semantics import read_u16_le, read_u32_le, strtol, write_u32_le
from nvt_combiner.primitives.checksum import cal_crc
from nvt_combiner.primitives.files import write_file
from nvt_combiner.primitives.overlay import calculate_overlay_crc, write_host_dlm_addresses, write_overlay_count
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import copy_exact, validate_non_negative, validate_range
from nvt_combiner.modes.legacy_io import prepare_map_based_normal_input


MODE = "NT51932BASED_NORMAL_MODE"
AB_MODE = "NT51932BASED_MERGE_AB_MODE"
_CRC8 = "CRC8"
_CRC32 = "CRC32"
_U32_BYTES = 4

# NT51932 common-header layout.
_HEADER_CRC_OFFSET = 0x7100
_HEADER_CRC_START_OFFSET = 0x7104
_HEADER_CRC_SIZE_CODE = 0x23
_ILM_SIZE_CODE_OFFSET = 0x7108
_ILM_CRC_OFFSET = 0x710C
_DLM_SIZE_CODE_OFFSET = 0x7114
_DLM_CRC_OFFSET = 0x7118
_DLM_DIFF_SIZE_CODE_OFFSET = 0x7120
_DLM_DIFF_CRC_TABLE_OFFSET = 0x7128
_OVERLAY_INFO_OFFSET = 0x7028
_IC_NUMBER_OFFSET = 0x702B
_FW_CONFIG_SOURCE_OFFSET = 0x7038
_ILM_START_OFFSET = 0x7164
_DLM_START_OFFSET = 0x7168
_DLM_DIFF_START_OFFSET = 0x716C

_SMALL_OUTPUT_SIZE = 256 * 1024
_LARGE_OUTPUT_SIZE = 512 * 1024
_SMALL_OUTPUT_MAX_IC_NUMBER = 13
_FW_CONFIG_ALIGNMENT = 0x1000
_FW_CONFIG_SIZE = 0x1000
_FW_CONFIG_END_FLAG = b"\x00NVT"


def _calculate_crc_fields(method: str, buffer: bytearray, ic_number: int) -> None:
    """Write NT51932 ILM, DLM, per-IC diff and common-header CRC fields."""
    ilm_address = read_u32_le(buffer, _ILM_START_OFFSET)
    ilm_crc = cal_crc(method, ilm_address, read_u32_le(buffer, _ILM_SIZE_CODE_OFFSET), buffer)
    write_u32_le(buffer, _ILM_CRC_OFFSET, ilm_crc)

    dlm_address = read_u32_le(buffer, _DLM_START_OFFSET)
    dlm_crc = cal_crc(method, dlm_address, read_u32_le(buffer, _DLM_SIZE_CODE_OFFSET), buffer)
    write_u32_le(buffer, _DLM_CRC_OFFSET, dlm_crc)

    print("--------------------------------------")
    print(f"ILM0 CRC :{ilm_crc:4x}")
    print(f"DLM0 CRC :{dlm_crc:4x}")

    dlm_diff_start = read_u32_le(buffer, _DLM_DIFF_START_OFFSET)
    dlm_diff_size = read_u16_le(buffer, _DLM_DIFF_SIZE_CODE_OFFSET) + 1
    for index in range(ic_number - 1):
        crc = cal_crc(method, dlm_diff_start + dlm_diff_size * index, dlm_diff_size - 1, buffer)
        write_u32_le(buffer, _DLM_DIFF_CRC_TABLE_OFFSET + _U32_BYTES * index, crc)
        print(f"DLM{index + 1:2d} CRC: 0x{crc:08X}")

    header_crc = cal_crc(method, _HEADER_CRC_START_OFFSET, _HEADER_CRC_SIZE_CODE, buffer)
    write_u32_le(buffer, _HEADER_CRC_OFFSET, header_crc)
    print("--------------------------------------")
    print(f"HEADER CRC: 0x{header_crc:08X}")
    print()


def run(arguments: list[str]) -> int:
    """Run the legacy NT51932 normal mode for validated map slices.

    ``arguments`` excludes the executable name but includes the mode selector.
    Valid invocation behavior, including legacy trailing incomplete block tuple
    handling, matches the C source.
    """
    crc_method, output_file, firmware_file = arguments[1:4]
    print(f"FwFilePath: {firmware_file}")
    preparation = prepare_map_based_normal_input(firmware_file, arguments[4:], len(arguments) + 1, 9)
    if preparation.status != RUNTIME_SUCCESS:
        return preparation.status
    prepared = preparation.input
    assert prepared is not None
    map_text = prepared.overlay_map.text
    overlay_info = prepared.overlay_map.info

    validate_range(
        len(prepared.firmware),
        _IC_NUMBER_OFFSET,
        1,
        context="NT51932",
        range_name="IC number field",
    )
    ic_number = prepared.firmware[_IC_NUMBER_OFFSET]
    total_size = _SMALL_OUTPUT_SIZE if ic_number <= _SMALL_OUTPUT_MAX_IC_NUMBER else _LARGE_OUTPUT_SIZE
    max_block_address = max((block.destination_address + block.length for block in prepared.blocks), default=0)
    if max_block_address > total_size:
        print(
            f"The bin size must <= {total_size // 1024}KB in IC_NUM = {ic_number} case. "
            f"But you want to generate {max_block_address // 1024}KB bin."
        )
        return RUNTIME_FAIL
    if len(prepared.firmware) > total_size:
        print("Firmware image is larger than the legacy output buffer.")
        return RUNTIME_FAIL

    print(f"Create a buffer with size = {total_size}-byte (0x{total_size:X})")
    output = bytearray(total_size)
    copy_exact(output, 0, prepared.firmware, 0, len(prepared.firmware), context="NT51932 firmware")
    for index, block in enumerate(prepared.blocks):
        copy_exact(
            output,
            block.destination_address,
            block.data,
            0,
            block.length,
            context=f'NT51932 block[{index}] file="{block.file_name}" source={block.source_address}',
        )

    fw_config_source = read_u32_le(output, _FW_CONFIG_SOURCE_OFFSET)
    dlm_diff_start = read_u32_le(output, _DLM_DIFF_START_OFFSET)
    dlm_diff_size_code = read_u16_le(output, _DLM_DIFF_SIZE_CODE_OFFSET)
    # The copied config follows every per-IC DLM-diff section and starts at
    # the next 4 KiB boundary, exactly as the legacy postbuild format expects.
    fw_config_destination = (
        (dlm_diff_start + (dlm_diff_size_code + 1) * (ic_number - 1))
        // _FW_CONFIG_ALIGNMENT
        + 1
    ) * _FW_CONFIG_ALIGNMENT
    copy_exact(
        output,
        fw_config_destination,
        output,
        fw_config_source,
        _FW_CONFIG_SIZE,
        context="NT51932 FW config",
    )
    print(f"FwConfig Address = 0x{fw_config_destination:X}")
    # The four-byte marker belongs at the end of the copied config page, not
    # at the end of the whole output image.
    end_flag_address = fw_config_destination + _FW_CONFIG_SIZE - len(_FW_CONFIG_END_FLAG)
    copy_exact(
        output,
        end_flag_address,
        _FW_CONFIG_END_FLAG,
        0,
        len(_FW_CONFIG_END_FLAG),
        context="NT51932 FW config end flag",
    )
    print(f"EndFlag Address = 0x{end_flag_address:X}")

    if crc_method in (_CRC8, _CRC32):
        write_overlay_count(output, _OVERLAY_INFO_OFFSET, overlay_info.count)
        write_host_dlm_addresses(output, _OVERLAY_INFO_OFFSET, map_text)
        calculate_overlay_crc(crc_method, output, _DLM_START_OFFSET, overlay_info.count)
        _calculate_crc_fields(crc_method, output, ic_number)
    else:
        print("CRC Disable...")

    if write_file(output_file, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    print("FW Merge is OK")
    return RUNTIME_SUCCESS


def run_merge_ab(arguments: list[str]) -> int:
    """Run the legacy NT51932 A/B merge mode with its original argv shape."""
    legacy_argc = len(arguments) + 1
    if legacy_argc != 6:
        print(f"Parameter count error. Expected: 6. But was: {legacy_argc}")
        return RUNTIME_FAIL

    a_code_path, b_code_path, output_path, offset_text = arguments[1:5]
    b_code_offset = validate_non_negative(
        strtol(offset_text, 0),
        context="NT51932 A/B merge",
        field_name="b_code_offset",
    )
    print(f"a_code_bin: {a_code_path}")
    print(f"b_code_bin: {b_code_path}")
    print(f"output_bin: {output_path}")
    print(f"b_code_offset: 0x{b_code_offset:X}")
    print("Start to Merge...")

    try:
        a_code = Path(a_code_path).read_bytes()
        b_code = Path(b_code_path).read_bytes()
    except OSError as error:
        print(f"Open file fail: {error.filename}")
        return RUNTIME_FAIL

    if len(a_code) > b_code_offset:
        print(
            f"Detect overlap: A Code File Size: 0x{len(a_code):X}. "
            f"B Code Offset: 0x{b_code_offset:X}.",
            end="",
        )
        return RUNTIME_FAIL

    validate_range(
        len(b_code),
        _ILM_START_OFFSET,
        _DLM_DIFF_START_OFFSET + _U32_BYTES - _ILM_START_OFFSET,
        context=f'NT51932 B code file="{b_code_path}"',
        range_name="relocation header",
    )

    output = bytearray(b_code_offset + len(b_code))
    copy_exact(output, 0, a_code, 0, len(a_code), context="NT51932 A code")
    copy_exact(output, b_code_offset, b_code, 0, len(b_code), context="NT51932 B code")

    ilm_offset = b_code_offset + _ILM_START_OFFSET
    dlm_offset = b_code_offset + _DLM_START_OFFSET
    dlm_diff_offset = b_code_offset + _DLM_DIFF_START_OFFSET
    original_ilm = read_u32_le(output, ilm_offset)
    original_dlm = read_u32_le(output, dlm_offset)
    original_dlm_diff = read_u32_le(output, dlm_diff_offset)
    modified_ilm = b_code_offset + original_ilm
    modified_dlm = b_code_offset + original_dlm
    modified_dlm_diff = b_code_offset + original_dlm_diff
    write_u32_le(output, ilm_offset, modified_ilm)
    write_u32_le(output, dlm_offset, modified_dlm)
    write_u32_le(output, dlm_diff_offset, modified_dlm_diff)

    print(f"Modify ILM start addr in bin: 0x{original_ilm:X} -> 0x{modified_ilm:X}")
    print(f"Modify DLM start addr in bin: 0x{original_dlm:X} -> 0x{modified_dlm:X}")
    print(f"Modify DLM_DIFF start addr in bin: 0x{original_dlm_diff:X} -> 0x{modified_dlm_diff:X}")
    if write_file(output_path, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    print("A/B code have been merged.")
    return RUNTIME_SUCCESS
