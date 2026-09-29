"""Port of legacy ``CalCrc`` method dispatch."""

from __future__ import annotations

from nvt_combiner.primitives.crc import crc8_alg, crc32_alg
from nvt_combiner.primitives.safety import InputValidationError


def cal_crc(method: str, address: int, size_code: int, buffer: bytes | bytearray) -> int:
    """Return legacy ``CalCrc`` output for an inclusive C size code.

    The supported C enum cases are ``Crc8`` and ``Crc32``.  The latter has a
    special zero-size bypass; the retained fallback covers the observed
    migration vectors for unrecognised states.
    """
    if size_code < 0:
        raise InputValidationError(
            f"{method} CRC: size_code must be >= 0; size_code={size_code}"
        )
    if method == "CRC8":
        return crc8_alg(address, size_code, buffer)
    if method == "CRC32" and size_code == 0:
        return 0
    return crc32_alg(address, size_code + 1, buffer)
