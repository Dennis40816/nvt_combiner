"""Argument-shape helpers for wrappers that must not alter Combiner argv."""

from __future__ import annotations


_IN_PLACE_MODES = {"CRC_Enable", "CRC32_Enable", "CRC_Disable"}
_MAP_BASED_NORMAL_MODES = {
    "NT51928BBASED_NORMAL_MODE",
    "NT51930BASED_NORMAL_MODE",
    "NT51931BASED_NORMAL_MODE",
    "NT51932BASED_NORMAL_MODE",
    "NT51950BASED_NORMAL_MODE",
}


def firmware_path_for_legacy_arguments(arguments: list[str]) -> str | None:
    """Return the firmware path used by legacy map lookup, if the mode has one."""
    if not arguments:
        return None
    if arguments[0] in _IN_PLACE_MODES and len(arguments) >= 2:
        return arguments[1]
    if arguments[0] in _MAP_BASED_NORMAL_MODES and len(arguments) >= 4:
        return arguments[3]
    return None
