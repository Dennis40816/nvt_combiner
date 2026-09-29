"""NT36672A merge-and-generate-CRC mode."""

from __future__ import annotations

from pathlib import Path

from nvt_combiner.primitives.c_semantics import read_u32_le
from nvt_combiner.primitives.files import write_file
from nvt_combiner.primitives.normal_crc import calculate_dlm_crc, calculate_ilm0_dlm0_crc
from nvt_combiner.primitives.result_codes import IO_FAIL, RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import validate_range
from nvt_combiner.modes.legacy_io import merge_firmware_and_blocks, read_legacy_blocks


MODE = "NT36672ABASED_MERGE_BIN_AND_GEN_CRC_MODE"


def run(arguments: list[str]) -> int:
    """Run the legacy NT36672A normal-header CRC flow."""
    legacy_argc = len(arguments) + 1
    if legacy_argc < 9 or legacy_argc % 2 == 0:
        print("Parameter format is error. FW Merge is FAIL")
        return RUNTIME_FAIL

    method, output_path, firmware_path = arguments[1:4]
    print("Start to Merge...")
    try:
        firmware = Path(firmware_path).read_bytes()
    except OSError:
        print(f"Open FW file '{firmware_path}' failure")
        return IO_FAIL

    blocks = read_legacy_blocks(arguments[4:])
    if blocks is None:
        print("Read other bins to GlobalBuffer fail.", end="")
        return RUNTIME_FAIL
    output = merge_firmware_and_blocks(firmware, blocks)

    if method in ("CRC8", "CRC32"):
        validate_range(len(output), 0, 0x21, context="NT36672A", range_name="common header")
        header_size = read_u32_le(output, 0)
        is_cascade_ic = (output[0x20] >> 1) & 1
        if is_cascade_ic:
            header_size >>= 1
        calculate_ilm0_dlm0_crc(method, output, 0)
        calculate_dlm_crc(method, output, 0, header_size)
        if is_cascade_ic:
            calculate_ilm0_dlm0_crc(method, output, header_size)
            calculate_dlm_crc(method, output, header_size, header_size)
    else:
        print("CRC Disable...")

    if write_file(output_path, output) != RUNTIME_SUCCESS:
        return RUNTIME_FAIL
    print("FW Merge is OK")
    return RUNTIME_SUCCESS
