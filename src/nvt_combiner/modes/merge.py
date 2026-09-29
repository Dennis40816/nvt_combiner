"""Legacy generic MERGE_MODE."""

from __future__ import annotations

from pathlib import Path

from nvt_combiner.primitives.c_semantics import strtol
from nvt_combiner.primitives.files import write_file
from nvt_combiner.primitives.result_codes import INPUT_FAIL, IO_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import copy_exact, validate_non_negative, validate_range


MODE = "MERGE_MODE"


def run(arguments: list[str]) -> int:
    """Merge legacy block tuples into their destination offsets in one bin."""
    output_path = arguments[1]
    blocks: list[tuple[int, int, int, bytes, str]] = []
    total_size = 0
    for index in range((len(arguments) - 2) // 4):
        file_name, source_text, destination_text, length_text = arguments[2 + 4 * index : 6 + 4 * index]
        context = f'MERGE_MODE block[{index}] file="{file_name}"'
        try:
            source = validate_non_negative(strtol(source_text, 16), context=context, field_name="source")
            destination = validate_non_negative(
                strtol(destination_text, 16),
                context=context,
                field_name="destination",
            )
            length = validate_non_negative(strtol(length_text, 10), context=context, field_name="length")
            contents = Path(file_name).read_bytes()
        except OSError:
            print("file open failure")
            return IO_FAIL
        print(f"Copy from Source File[{index}]:0x{source:x} ")
        print(f"To Target File:0x{destination:x} ")
        print(f"Size:{length} ")
        if len(contents) < length:
            print(f" input bin[{index}]'s size is smaller than the size to merge, please check input parameter")
            return INPUT_FAIL
        validate_range(len(contents), source, length, context=context, range_name="source")
        blocks.append((destination, source, length, contents, context))
        total_size = max(total_size, destination + length)

    print(f"Target File's size:{total_size} ")
    output = bytearray(total_size)
    for destination, source, length, contents, context in blocks:
        copy_exact(output, destination, contents, source, length, context=context)
    if write_file(output_path, output) != RUNTIME_SUCCESS:
        return IO_FAIL
    print("FW Merge is OK")
    return RUNTIME_SUCCESS
