"""Bounds-checked buffer operations for deterministic failure behavior."""

from __future__ import annotations


class InputValidationError(ValueError):
    """A malformed input range that must not reach a copy or CRC operation."""


def validate_non_negative(value: int, *, context: str, field_name: str) -> int:
    """Return a CLI numeric value or reject Python's negative-index semantics."""
    if value < 0:
        raise InputValidationError(f"{context}: {field_name} must be >= 0; {field_name}={value}")
    return value


def validate_range(
    buffer_size: int,
    start: int,
    length: int,
    *,
    context: str,
    range_name: str,
) -> slice:
    """Return an exact slice or raise an error containing useful diagnostics."""
    if start < 0:
        raise InputValidationError(
            f"{context}: {range_name} start must be >= 0; "
            f"start={start}, length={length}, buffer_size={buffer_size}"
        )
    if length < 0:
        raise InputValidationError(
            f"{context}: {range_name} length must be >= 0; "
            f"start={start}, length={length}, buffer_size={buffer_size}"
        )
    if length == 0:
        # Legacy callers commonly pass a non-zero address for an empty block.
        # No byte is dereferenced, so retaining that no-op is both safe and
        # required for CLI/output compatibility.
        return slice(start, start)

    end = start + length
    if end > buffer_size:
        available = max(buffer_size - start, 0)
        raise InputValidationError(
            f"{context}: {range_name} range out of bounds; "
            f"start={start}, length={length}, end={end}, "
            f"buffer_size={buffer_size}, available={available}"
        )
    return slice(start, end)


def copy_exact(
    destination: bytearray,
    destination_start: int,
    source: bytes | bytearray,
    source_start: int,
    length: int,
    *,
    context: str,
) -> None:
    """Copy an exact range without permitting Python slice resizing."""
    source_slice = validate_range(
        len(source),
        source_start,
        length,
        context=context,
        range_name="source",
    )
    destination_slice = validate_range(
        len(destination),
        destination_start,
        length,
        context=context,
        range_name="destination",
    )

    # Snapshot first so overlapping source/destination ranges are deterministic.
    payload = bytes(source[source_slice])
    memoryview(destination)[destination_slice] = payload
