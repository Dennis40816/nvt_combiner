# Generic normal-mode gate

The unchanged interface is verified for no-overlay maps and one basic overlay
descriptor-table map:

```text
CRC_Enable|CRC32_Enable|CRC_Disable <fw-in-out> \
  <block-bin> <source-hex> <destination-hex> <length-dec> [...]
```

`tests/module/test_normal_crc_enabled.py` runs the pinned Combiner 1.13 EXE
and `python -m nvt_combiner` with exactly the same positional argv.  Each
case asserts process exit code, stdout, and the complete rewritten firmware.
The CRC-enabled fixture covers a single common header for both CRC methods,
plus a two-header cascade flow for CRC8.  Reference output SHA-256 values:

| Mode / case | SHA-256 |
| --- | --- |
| `CRC_Enable`, one header | `98ea9065b341ba081f9da51206fd7adf08d5e6ee05344c9a4ad899659cc86514` |
| `CRC32_Enable`, one header | `2a1cb60ab113702ef9d5cd5ac65e1961c8b4a047ebc5f890de6951a69913d6f8` |
| `CRC_Enable`, cascade headers | `0c0fb57aa27388e9e24dfc4cd04a7cca74a8bd3329afc3496ff9861747404eb4` |
| `CRC_Enable`, one overlay descriptor | `b8acb23000f27747ed751e08606e38c859f7f2a3ed006ef8832278cf12d6371d` |
| `CRC32_Enable`, one overlay descriptor | `d5632bda0b1062b56b3d4ce13899bb480cf609e1473211dd62571b5aaf285000` |
| `CRC_Enable`, two overlay descriptors | `6c6593c137dd4c08270c3bc81d67e9e5e52aed6479a701f35f05386ac176562b` |
| `CRC32_Enable`, two overlay descriptors | `fb0ee46eb3078912d5efe98b4c923e719c68b55ea5c34fbe3c0bbe690bd028f2` |
| `CRC_Enable`, HostDL `OverlayDLMaddr` | `95585bb62dd9d5d18011908ad9fab233b165451a04c80046c54b601e8dff8dc8` |
| `CRC32_Enable`, HostDL `OverlayDLMaddr` | `2c447048e750735bbda0af525d2ca78880a8dfbf7275a4f5994670470ac22813` |

`tests/module/test_normal_overlay.py` adds the map parser's `?TEXT_SIZE:` /
`_ovly_table =` path, one- and two-descriptor CRC tables, and overlay count
writeback for CRC8 and CRC32.

`tests/module/test_normal_overlay_count_wrap.py` validates the C assignment
semantics for an extreme, valid 256-descriptor overlay table: `OverlaySize`
is an `int`, but its destination field is a byte, so the reference and Python
both retain `0xA0` after the `0x100` count is ORed into that field.

`tests/module/test_normal_hostdl_overlay.py` characterizes the legacy
HostDL/Process bit-4 branch: it reads eight characters at offset 18 of the
line after `OverlayDLMaddr`, mutates `DLM_DataStartAddr + i * 16`, and prints
the exact legacy console line.

`tests/module/test_normal_family_hostdl_overlay.py` applies that same
primitive to generic, NT51931, NT51930, NT51932, NT51950 and NT51928B normal
modes with each family’s real overlay-info offset.  The CRC8 invocation,
stdout and complete output binary all match the reference.  Generic normal
also separately covers this branch for CRC32.

`tests/module/test_normal_overlay_failure.py` verifies the map validation
failure where `RAM_BaseAddr + section size >= ILM_LimitSize`; the Python mode
and pinned EXE return the same failure code, console text and unchanged
firmware.

`tests/module/test_normal_map_fallback.py` verifies the legacy absence of a
sibling `map.txt` falls back to `output\\map.txt`, including console text and
the rewritten firmware result.

`tests/module/test_normal_missing_block.py` verifies a block-file open
failure after the map has been accepted.  It fixes the C timing contract: the
block-reader separator and table heading are printed before the failed open,
and the caller's final failure message has no trailing newline.

`tests/module/test_normal_overlay_crc_disable.py` verifies `CRC_Disable`
still parses an overlay map yet leaves overlay/CRC fields untouched, matching
the reference process output and merged firmware.

`tests/module/test_normal_dlm_overlay.py` verifies the valid DLM-overlay
branch where `RAM_BaseAddr >= ILM_LimitSize` is explicitly skipped rather than
rejected; output remains byte-for-byte equal to reference.

`tests/module/test_normal_malformed_map.py` verifies a malformed
`?TEXT_SIZE:` record missing its second hex value.  The text-mode map reader
normalises CRLF like MSVC `fopen(..., "r")`, so Python and reference report
the same diagnostic whitespace and failure result.
It also checks overlay records missing their first, second or third `0x`
value, preserving C's distinct diagnostics, and an invalid second text-size
value that must follow MSVC `strtol` and become zero rather than fail.  A
500-byte physical map line is also split at the 499-character `fgets` limit,
so a diagnostic emits the same final C record rather than the whole physical
line.

`tests/module/test_normal_text_size_no_overlay.py` verifies a valid
`?TEXT_SIZE:` record with no overlay table prints the ILM limit then follows
the no-overlay merge path exactly.

Excluded: malformed overlay sections, malformed pointers / source ranges that invoke
undefined C behavior, and legacy allocation gaps beyond the supplied firmware
and blocks.
