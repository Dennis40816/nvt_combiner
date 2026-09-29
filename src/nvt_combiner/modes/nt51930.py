"""NT51930 no-overlay normal mode."""

from __future__ import annotations

from nvt_combiner.primitives.c_semantics import read_u16_le, read_u32_le
from nvt_combiner.primitives.files import write_file
from nvt_combiner.primitives.nt51930_crc import calculate_crc_fields
from nvt_combiner.primitives.overlay import calculate_overlay_crc, write_host_dlm_addresses, write_overlay_count
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import copy_exact, validate_range
from nvt_combiner.modes.legacy_io import prepare_map_based_normal_input


MODE = "NT51930BASED_NORMAL_MODE"
_CRC_METHODS = ("CRC8", "CRC32")

# NT51930 common-header layout.
_FW_CONFIG_SOURCE_OFFSET = 0x7038
_OVERLAY_INFO_OFFSET = 0x7028
_DLM_DIFF_SIZE_CODE_OFFSET = 0x7120
_IC_NUMBER_OFFSET = 0x7123
_DLM_START_OFFSET = 0x719C
_DLM_DIFF_START_OFFSET = 0x71A0
_SMALL_OUTPUT_SIZE = 256 * 1024
_LARGE_OUTPUT_SIZE = 512 * 1024
_SMALL_OUTPUT_MAX_IC_NUMBER = 13
_FW_CONFIG_ALIGNMENT = 0x1000
_FW_CONFIG_SIZE = 0x1000
_FW_CONFIG_END_FLAG = b"\x00NVT"


def run(arguments: list[str]) -> int:
    """Run NT51930 normal merge, fixed-buffer placement and CRC updates."""
    method, output_path, firmware_path = arguments[1:4]
    print(f"FwFilePath: {firmware_path}")
    preparation = prepare_map_based_normal_input(firmware_path, arguments[4:], len(arguments) + 1, 9)
    if preparation.status != RUNTIME_SUCCESS:
        return preparation.status
    prepared = preparation.input
    assert prepared is not None
    map_text = prepared.overlay_map.text
    overlay_info = prepared.overlay_map.info
    maximum_block_address = max(
        len(prepared.firmware),
        *(block.destination_address + block.length for block in prepared.blocks),
    )
    validate_range(
        len(prepared.firmware),
        _IC_NUMBER_OFFSET,
        1,
        context="NT51930",
        range_name="IC number field",
    )
    ic_number = prepared.firmware[_IC_NUMBER_OFFSET]
    total_size = _SMALL_OUTPUT_SIZE if ic_number <= _SMALL_OUTPUT_MAX_IC_NUMBER else _LARGE_OUTPUT_SIZE
    if maximum_block_address > total_size:
        print(
            f"The bin size must <= {total_size // 1024}KB in IC_NUM = {ic_number} case. "
            f"But you want to generate {maximum_block_address // 1024}KB bin.",
            end="",
        )
        return RUNTIME_FAIL

    print(f"Create a buffer with size = {total_size}-byte (0x{total_size:X})")
    output = bytearray(total_size)
    copy_exact(output, 0, prepared.firmware, 0, len(prepared.firmware), context="NT51930 firmware")
    for index, block in enumerate(prepared.blocks):
        copy_exact(
            output,
            block.destination_address,
            block.data,
            0,
            block.length,
            context=f'NT51930 block[{index}] file="{block.file_name}" source={block.source_address}',
        )

    config_source = read_u32_le(output, _FW_CONFIG_SOURCE_OFFSET)
    diff_start = read_u32_le(output, _DLM_DIFF_START_OFFSET)
    diff_size_code = read_u16_le(output, _DLM_DIFF_SIZE_CODE_OFFSET)
    config_destination = (
        (diff_start + (diff_size_code + 1) * (ic_number - 1))
        // _FW_CONFIG_ALIGNMENT
        + 1
    ) * _FW_CONFIG_ALIGNMENT
    copy_exact(
        output,
        config_destination,
        output,
        config_source,
        _FW_CONFIG_SIZE,
        context="NT51930 FW config",
    )
    print(f"FwConfig Address = 0x{config_destination:X}")
    end_flag_address = config_destination + _FW_CONFIG_SIZE - len(_FW_CONFIG_END_FLAG)
    copy_exact(
        output,
        end_flag_address,
        _FW_CONFIG_END_FLAG,
        0,
        len(_FW_CONFIG_END_FLAG),
        context="NT51930 FW config end flag",
    )
    print(f"EndFlag Address = 0x{end_flag_address:X}")

    if method in _CRC_METHODS:
        write_overlay_count(output, _OVERLAY_INFO_OFFSET, overlay_info.count)
        write_host_dlm_addresses(output, _OVERLAY_INFO_OFFSET, map_text)
        calculate_overlay_crc(method, output, _DLM_START_OFFSET, overlay_info.count)
        calculate_crc_fields(method, output)
    else:
        print("CRC Disable...")

    if write_file(output_path, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    print("FW Merge is OK")
    return RUNTIME_SUCCESS
