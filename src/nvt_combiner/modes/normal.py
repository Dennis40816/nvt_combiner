"""Legacy generic normal mode."""

from __future__ import annotations

from nvt_combiner.primitives.header import decode_one_header_size
from nvt_combiner.primitives.normal_crc import calculate_dlm_crc, calculate_ilm0_dlm0_crc
from nvt_combiner.primitives.overlay import calculate_overlay_crc, write_host_dlm_addresses, write_overlay_count
from nvt_combiner.primitives.files import write_file
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import validate_range
from nvt_combiner.modes.legacy_io import merge_firmware_and_blocks, prepare_map_based_normal_input


MODES = {"CRC_Enable", "CRC32_Enable", "CRC_Disable"}


def run(arguments: list[str]) -> int:
    """Run generic normal-mode merge and optional header/overlay CRC updates."""
    mode, firmware_path = arguments[:2]
    print(f"FwFilePath: {firmware_path}")
    preparation = prepare_map_based_normal_input(firmware_path, arguments[2:], len(arguments) + 1, 7)
    if preparation.status != RUNTIME_SUCCESS:
        return preparation.status
    prepared = preparation.input
    assert prepared is not None
    map_text = prepared.overlay_map.text
    overlay_info = prepared.overlay_map.info
    output = merge_firmware_and_blocks(prepared.firmware, prepared.blocks)
    if mode == "CRC_Disable":
        print("CRC Disable...")
    else:
        method = "CRC8" if mode == "CRC_Enable" else "CRC32"
        validate_range(len(output), 0, 0x29, context="generic normal", range_name="common header")
        write_overlay_count(output, 0x28, overlay_info.count)
        write_host_dlm_addresses(output, 0x28, map_text)
        calculate_overlay_crc(method, output, 12, overlay_info.count)
        print("--------------------------------------")
        header_size = decode_one_header_size(output)
        if header_size is None:
            return RUNTIME_FAIL
        print(f"One HeaderSize: {header_size}-byte.")

        is_cascade_ic = (output[0x20] >> 1) & 1
        calculate_ilm0_dlm0_crc(method, output, 0)
        calculate_dlm_crc(method, output, 0, header_size)
        if is_cascade_ic:
            calculate_ilm0_dlm0_crc(method, output, header_size)
            calculate_dlm_crc(method, output, header_size, header_size)

    if write_file(firmware_path, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    print("FW Merge is OK")
    return RUNTIME_SUCCESS
