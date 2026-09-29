"""CRC primitives that preserve the legacy Combiner bit-level results.

The historical name ``CRC8Alg`` is retained even though it returns a 32-bit
value.  The input size is a *size code*: both endpoint bytes are processed.
"""

from nvt_combiner.primitives.safety import InputValidationError, validate_range


_CRC32_INITIAL_REMAINDER = 0xFFFFFFFF
_CRC32_POLYNOMIAL = 0x04C11DB7
_CRC32_HIGH_BIT = 0x80000000
_CRC32_MASK = 0xFFFFFFFF


def legacy_crc8_alg(address: int, size_code: int, buffer: bytes | bytearray) -> int:
    """Freeze the literal state-machine port of legacy ``CRC8Alg``.

    This is retained as a readable audit oracle for differential unit tests.
    Production callers should use :func:`crc8_alg`, the mathematically
    equivalent MSB-first implementation below.
    """
    state = [1] * 32

    for offset in range(address, address + size_code + 1):
        value = buffer[offset]
        data = [(value >> bit) & 1 for bit in range(8)]
        q = state
        state = [
            q[24] ^ q[30] ^ data[0] ^ data[6],
            q[24] ^ q[25] ^ q[30] ^ q[31] ^ data[0] ^ data[1] ^ data[6] ^ data[7],
            q[24] ^ q[25] ^ q[26] ^ q[30] ^ q[31] ^ data[0] ^ data[1] ^ data[2] ^ data[6] ^ data[7],
            q[25] ^ q[26] ^ q[27] ^ q[31] ^ data[1] ^ data[2] ^ data[3] ^ data[7],
            q[24] ^ q[26] ^ q[27] ^ q[28] ^ q[30] ^ data[0] ^ data[2] ^ data[3] ^ data[4] ^ data[6],
            q[24] ^ q[25] ^ q[27] ^ q[28] ^ q[29] ^ q[30] ^ q[31] ^ data[0] ^ data[1] ^ data[3] ^ data[4] ^ data[5] ^ data[6] ^ data[7],
            q[25] ^ q[26] ^ q[28] ^ q[29] ^ q[30] ^ q[31] ^ data[1] ^ data[2] ^ data[4] ^ data[5] ^ data[6] ^ data[7],
            q[24] ^ q[26] ^ q[27] ^ q[29] ^ q[31] ^ data[0] ^ data[2] ^ data[3] ^ data[5] ^ data[7],
            q[0] ^ q[24] ^ q[25] ^ q[27] ^ q[28] ^ data[0] ^ data[1] ^ data[3] ^ data[4],
            q[1] ^ q[25] ^ q[26] ^ q[28] ^ q[29] ^ data[1] ^ data[2] ^ data[4] ^ data[5],
            q[2] ^ q[24] ^ q[26] ^ q[27] ^ q[29] ^ data[0] ^ data[2] ^ data[3] ^ data[5],
            q[3] ^ q[24] ^ q[25] ^ q[27] ^ q[28] ^ data[0] ^ data[1] ^ data[3] ^ data[4],
            q[4] ^ q[24] ^ q[25] ^ q[26] ^ q[28] ^ q[29] ^ q[30] ^ data[0] ^ data[1] ^ data[2] ^ data[4] ^ data[5] ^ data[6],
            q[5] ^ q[25] ^ q[26] ^ q[27] ^ q[29] ^ q[30] ^ q[31] ^ data[1] ^ data[2] ^ data[3] ^ data[5] ^ data[6] ^ data[7],
            q[6] ^ q[26] ^ q[27] ^ q[28] ^ q[30] ^ q[31] ^ data[2] ^ data[3] ^ data[4] ^ data[6] ^ data[7],
            q[7] ^ q[27] ^ q[28] ^ q[29] ^ q[31] ^ data[3] ^ data[4] ^ data[5] ^ data[7],
            q[8] ^ q[24] ^ q[28] ^ q[29] ^ data[0] ^ data[4] ^ data[5],
            q[9] ^ q[25] ^ q[29] ^ q[30] ^ data[1] ^ data[5] ^ data[6],
            q[10] ^ q[26] ^ q[30] ^ q[31] ^ data[2] ^ data[6] ^ data[7],
            q[11] ^ q[27] ^ q[31] ^ data[3] ^ data[7],
            q[12] ^ q[28] ^ data[4],
            q[13] ^ q[29] ^ data[5],
            q[14] ^ q[24] ^ data[0],
            q[15] ^ q[24] ^ q[25] ^ q[30] ^ data[0] ^ data[1] ^ data[6],
            q[16] ^ q[25] ^ q[26] ^ q[31] ^ data[1] ^ data[2] ^ data[7],
            q[17] ^ q[26] ^ q[27] ^ data[2] ^ data[3],
            q[18] ^ q[24] ^ q[27] ^ q[28] ^ q[30] ^ data[0] ^ data[3] ^ data[4] ^ data[6],
            q[19] ^ q[25] ^ q[28] ^ q[29] ^ q[31] ^ data[1] ^ data[4] ^ data[5] ^ data[7],
            q[20] ^ q[26] ^ q[29] ^ q[30] ^ data[2] ^ data[5] ^ data[6],
            q[21] ^ q[27] ^ q[30] ^ q[31] ^ data[3] ^ data[6] ^ data[7],
            q[22] ^ q[28] ^ q[31] ^ data[4] ^ data[7],
            q[23] ^ q[29] ^ data[5],
        ]

    return sum(bit << index for index, bit in enumerate(state))


def _update_crc32_msb_first(remainder: int, value: int) -> int:
    """Feed one byte into the legacy polynomial in MSB-first order."""
    remainder ^= value << 24
    for _ in range(8):
        if remainder & _CRC32_HIGH_BIT:
            remainder = ((remainder << 1) ^ _CRC32_POLYNOMIAL) & _CRC32_MASK
        else:
            remainder = (remainder << 1) & _CRC32_MASK
    return remainder


def crc8_alg(address: int, size_code: int, buffer: bytes | bytearray) -> int:
    """Return legacy ``CRC8Alg`` using its equivalent clean CRC formulation.

    The C function's name is misleading: it is a 32-bit LFSR with initial
    remainder ``0xFFFFFFFF``, polynomial ``0x04C11DB7``, MSB-first input bytes
    and no final XOR.  ``size_code`` is inclusive.
    """
    if size_code < 0:
        raise InputValidationError(f"CRC8: size_code must be >= 0; size_code={size_code}")
    input_range = validate_range(
        len(buffer),
        address,
        size_code + 1,
        context="CRC8",
        range_name="input",
    )

    remainder = _CRC32_INITIAL_REMAINDER
    for value in buffer[input_range]:
        remainder = _update_crc32_msb_first(remainder, value)
    return remainder


def crc32_alg(address: int, byte_count: int, buffer: bytes | bytearray) -> int:
    """Return the bit-for-bit result of legacy ``CRC32Alg``.

    The C routine consumes a little-endian 32-bit word at a time through a
    parallel LFSR.  Its equivalent serial form is an MSB-first CRC-32 with an
    initial value of ``0xFFFFFFFF``, no final XOR, reversed byte order inside
    each four-byte word, and zero padding in an incomplete final word.

    Unlike :func:`crc8_alg`, this function takes a byte count.  Legacy
    ``CalCrc`` passes it ``size_code + 1``.
    """
    if byte_count < 0:
        raise InputValidationError(f"CRC32: byte_count must be >= 0; byte_count={byte_count}")
    validate_range(
        len(buffer),
        address,
        byte_count,
        context="CRC32",
        range_name="input",
    )

    crc = _CRC32_INITIAL_REMAINDER
    for start in range(address, address + byte_count, 4):
        word = bytes(buffer[start : min(start + 4, address + byte_count)])
        for value in reversed(word + b"\x00" * (4 - len(word))):
            crc = _update_crc32_msb_first(crc, value)
    return crc
