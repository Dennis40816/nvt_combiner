"""NT51931 no-overlay normal mode."""

from __future__ import annotations

from nvt_combiner.primitives.files import write_file
from nvt_combiner.primitives.normal_crc import calculate_ilm0_dlm0_crc
from nvt_combiner.primitives.nt51931_crc import calculate_diff_dlm_and_fw_header_crc
from nvt_combiner.primitives.overlay import calculate_overlay_crc, write_host_dlm_addresses, write_overlay_count
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import validate_range
from nvt_combiner.modes.legacy_io import merge_firmware_and_blocks, prepare_map_based_normal_input


MODE = "NT51931BASED_NORMAL_MODE"
_CRC_METHODS = ("CRC8", "CRC32")

# NT51931 common-header layout.
_OVERLAY_INFO_OFFSET = 0x28
_DLM_START_OFFSET = 0x0C
_MINIMUM_CRC_HEADER_SIZE = 0x100


def run(arguments: list[str]) -> int:
    """Run NT51931 normal merge and its common-header CRC sequence."""
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

    if method in _CRC_METHODS:
        validate_range(
            len(output),
            0,
            _MINIMUM_CRC_HEADER_SIZE,
            context="NT51931",
            range_name="CRC header",
        )
        write_overlay_count(output, _OVERLAY_INFO_OFFSET, overlay_info.count)
        write_host_dlm_addresses(output, _OVERLAY_INFO_OFFSET, map_text)
        calculate_overlay_crc(method, output, _DLM_START_OFFSET, overlay_info.count)
        calculate_ilm0_dlm0_crc(method, output, 0)
        calculate_diff_dlm_and_fw_header_crc(method, output)
    else:
        print("CRC Disable...")

    if write_file(output_path, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    print("FW Merge is OK")
    return RUNTIME_SUCCESS
