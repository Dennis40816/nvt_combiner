# Legacy `CalCrc` dispatch contract

The C implementation selects `CRC8Alg` only when `CrcMethod == Crc8`.
Otherwise it calls `CRC32Alg(addr, size_code + 1, buffer)`. This includes the
global `None` state produced by an unrecognized CRC argument in some modes.

The function tests lock this exact behavior using the previously characterized
CRC8 and CRC32 vectors; it is shared rather than copied by IC modules.
