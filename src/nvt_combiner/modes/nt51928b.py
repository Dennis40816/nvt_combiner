"""NT51928B no-overlay normal mode."""

from __future__ import annotations

from nvt_combiner.primitives.c_semantics import read_u32_le
from nvt_combiner.primitives.files import write_file
from nvt_combiner.primitives.nt51928b_crc import calculate_header_crc, calculate_ilm_dlm_crc
from nvt_combiner.primitives.overlay import calculate_overlay_crc, write_host_dlm_addresses, write_overlay_count
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import copy_exact, validate_range
from nvt_combiner.modes.legacy_io import merge_firmware_and_blocks, prepare_map_based_normal_input


MODE = "NT51928BBASED_NORMAL_MODE"
_CRC_METHODS = ("CRC8", "CRC32")

# NT51928B common-header layout.
_OVERLAY_INFO_OFFSET = 0xD028
_FW_CONFIG_SOURCE_OFFSET = 0xD038
_DLM_START_OFFSET = 0xD110
_FW_CONFIG_DESTINATION = 0x3E000
_FW_CONFIG_SIZE = 1920


def run(arguments: list[str]) -> int:
    """Run NT51928B normal merge, config copy and optional CRC writes."""
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
        context="NT51928B",
        range_name="FW config source field",
    )
    config_source = read_u32_le(output, _FW_CONFIG_SOURCE_OFFSET)
    copy_exact(
        output,
        _FW_CONFIG_DESTINATION,
        output,
        config_source,
        _FW_CONFIG_SIZE,
        context="NT51928B FW config",
    )
    print(
        f"Copy FwConfig from 0x{config_source:X} to 0x{_FW_CONFIG_DESTINATION:x}. "
        f"Size: {_FW_CONFIG_SIZE}-byte."
    )

    if method in _CRC_METHODS:
        write_overlay_count(output, _OVERLAY_INFO_OFFSET, overlay_info.count)
        write_host_dlm_addresses(output, _OVERLAY_INFO_OFFSET, map_text)
        calculate_overlay_crc(method, output, _DLM_START_OFFSET, overlay_info.count)
        calculate_ilm_dlm_crc(method, output)
        calculate_header_crc(method, output)
    else:
        print("CRC Disable...")

    if write_file(output_path, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    print("FW Merge is OK")
    return RUNTIME_SUCCESS
