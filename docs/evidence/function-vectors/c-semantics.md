# C data-semantics primitives

The C implementation frequently uses unaligned pointer casts such as
`*(unsigned int *)(pBuf + offset)` and parses CLI values with `strtol`.
These are now isolated function-level ports rather than hidden inside an IC
module.

| Primitive | Locked behavior |
| --- | --- |
| `read_u16_le` / `read_u32_le` | Unaligned little-endian reads |
| `write_u32_le` | Writes exactly four bytes; stores `value & 0xFFFFFFFF` |
| `strtol(text, 16)` | Optional `0x`, whitespace/signs, then stops at an invalid digit |
| `strtol(text, 10)` | Decimal CLI length parsing, including C-style trailing text stop |
| `strtol(text, 0)` | A/B offset parsing: hexadecimal prefix, decimal, and C octal prefix |

The test boundary is valid readable/writable ranges and non-overflowing
numbers. Out-of-range pointer reads and `long` overflow are undefined or
platform-specific in the legacy C and are deliberately not promoted to a new
Python contract.
