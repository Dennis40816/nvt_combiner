"""Shared map, block and buffer operations with legacy console behavior."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nvt_combiner.primitives.c_semantics import strtol
from nvt_combiner.primitives.map_text import read_legacy_map_text
from nvt_combiner.primitives.overlay import OverlayInfo, inspect_map
from nvt_combiner.primitives.result_codes import IO_FAIL, RUNTIME_FAIL, RUNTIME_SUCCESS
from nvt_combiner.primitives.safety import copy_exact, validate_non_negative, validate_range


@dataclass(frozen=True)
class Block:
    file_name: str
    source_address: int
    destination_address: int
    length: int
    data: bytes


@dataclass(frozen=True)
class ValidatedOverlayMap:
    text: str
    info: OverlayInfo


@dataclass(frozen=True)
class PreparedNormalInput:
    overlay_map: ValidatedOverlayMap
    firmware: bytes
    blocks: list[Block]


@dataclass(frozen=True)
class PreparationResult:
    """The legacy status and optional inputs from a normal-mode preamble."""

    status: int
    input: PreparedNormalInput | None


def open_legacy_map(firmware_file: str) -> Path | None:
    """Locate ``map.txt`` in the legacy primary/fallback order."""
    firmware = Path(firmware_file)
    primary = firmware.parent / "map.txt"
    if primary.is_file():
        print(f'Success to open map.txt at "{primary}".')
        print("--------------------------------------")
        return primary

    print(f'Open map.txt at "{primary}" failed.')
    fallback = firmware.parent / "output" / "map.txt"
    if fallback.is_file():
        print(f'Success to open map.txt at "{fallback}".')
        print("--------------------------------------")
        return fallback

    print(f'Open map.txt at "{fallback}" failed.')
    return None


def read_validated_overlay_map(firmware_file: str) -> ValidatedOverlayMap | None:
    """Open, text-normalise and validate a legacy map in observable C order."""
    map_file = open_legacy_map(firmware_file)
    if map_file is None:
        return None
    try:
        text = read_legacy_map_text(map_file)
    except OSError as error:
        print(f'Read map.txt fail: path="{map_file}"; error={error}')
        return None
    info = inspect_map(text)
    if info is None:
        return None
    return ValidatedOverlayMap(text, info)


def read_legacy_blocks(raw_arguments: list[str]) -> list[Block] | None:
    """Read block tuples and emit their table as C does during loading."""
    blocks: list[Block] = []
    print("--------------------------------------")
    print("Start to read other bins.")
    print("Source\t\tDest\t\tLength\t\tFileName")
    for index in range(len(raw_arguments) // 4):
        file_name, source_text, destination_text, length_text = raw_arguments[index * 4 : index * 4 + 4]
        context = f'block[{index}] file="{file_name}"'
        try:
            source_address = validate_non_negative(
                strtol(source_text, 16),
                context=context,
                field_name="source",
            )
            destination_address = validate_non_negative(
                strtol(destination_text, 16),
                context=context,
                field_name="destination",
            )
            requested_length = validate_non_negative(
                strtol(length_text, 10),
                context=context,
                field_name="requested_length",
            )
            source_bytes = Path(file_name).read_bytes()
        except OSError:
            print("file open failure")
            return None

        length = min(len(source_bytes), requested_length)
        source_range = validate_range(
            len(source_bytes),
            source_address,
            length,
            context=context,
            range_name="source",
        )
        blocks.append(
            Block(
                file_name,
                source_address,
                destination_address,
                length,
                source_bytes[source_range],
            )
        )
        print(f"0x{source_address:X}\t\t0x{destination_address:X}\t\t{length}\t\t{file_name}")
    return blocks


def prepare_map_based_normal_input(
    firmware_file: str,
    raw_block_arguments: list[str],
    legacy_argc: int,
    minimum_legacy_argc: int,
) -> PreparationResult:
    """Run the shared map-normal preamble in legacy observable order."""
    # The C tool opens/parses map.txt before it rejects malformed argv.  Keep
    # this order because callers can observe both its diagnostics and failure.
    overlay_map = read_validated_overlay_map(firmware_file)
    if overlay_map is None:
        return PreparationResult(RUNTIME_FAIL, None)
    if legacy_argc < minimum_legacy_argc or legacy_argc % 2 == 0:
        print("Parameter format is error. FW Merge is FAIL")
        return PreparationResult(RUNTIME_FAIL, None)

    print("Start to Merge...")
    try:
        firmware = Path(firmware_file).read_bytes()
    except OSError:
        print(f"Open FW file '{firmware_file}' failure")
        return PreparationResult(IO_FAIL, None)

    blocks = read_legacy_blocks(raw_block_arguments)
    if blocks is None:
        print("Read other bins to GlobalBuffer fail.", end="")
        return PreparationResult(RUNTIME_FAIL, None)
    return PreparationResult(RUNTIME_SUCCESS, PreparedNormalInput(overlay_map, firmware, blocks))


def merge_firmware_and_blocks(firmware: bytes, blocks: list[Block]) -> bytearray:
    """Build the dynamic-size buffer and copy blocks in command-line order."""
    for index, block in enumerate(blocks):
        context = f'block[{index}] file="{block.file_name}"'
        validate_non_negative(block.destination_address, context=context, field_name="destination")
        validate_non_negative(block.length, context=context, field_name="length")
    total_size = max(len(firmware), *(block.destination_address + block.length for block in blocks))
    output = bytearray(total_size)
    copy_exact(output, 0, firmware, 0, len(firmware), context="firmware")
    for index, block in enumerate(blocks):
        copy_exact(
            output,
            block.destination_address,
            block.data,
            0,
            block.length,
            context=f'block[{index}] file="{block.file_name}" source={block.source_address}',
        )
    return output
