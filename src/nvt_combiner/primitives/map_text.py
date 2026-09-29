"""Text-mode map reader matching MSVC ``fopen(..., \"r\")`` newline handling."""

from __future__ import annotations

from pathlib import Path


_FGETS_CAPACITY = 500


def read_legacy_map_text(map_file: Path) -> str:
    """Read a map using text mode so CRLF is normalised before C-style parsing."""
    return map_file.read_text(encoding="latin1")


def legacy_fgets_records(map_text: str) -> list[str]:
    """Split normalised map text as ``fgets(buffer, 500, ...)`` would."""
    maximum_characters = _FGETS_CAPACITY - 1
    records: list[str] = []
    position = 0
    while position < len(map_text):
        newline = map_text.find("\n", position)
        limit = position + maximum_characters
        if newline >= position and newline < limit:
            end = newline + 1
        else:
            end = min(limit, len(map_text))
        records.append(map_text[position:end])
        position = end
    return records
