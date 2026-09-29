# NT51932 normal-mode no-overlay module gate

## Supported slice

The Python implementation accepts the unchanged legacy argument shape:

```text
NT51932BASED_NORMAL_MODE <CRC8|CRC32> <output-bin> <firmware-bin> \
  <block-bin> <source-hex> <destination-hex> <length-dec> [...]
```

It retains legacy lookup of `map.txt` beside the firmware, then
`output/map.txt`. A map without `_ovly_table =` follows the no-overlay path.
No `--overlay-map-txt` argument is accepted by this compatibility CLI; that is
reserved for the separate future postbuild wrapper described in the NT51929
map evidence.

## Differential test

`tests/module/test_nt51932_no_overlay.py` creates a 256 KiB single-IC fixture,
one 16-byte block, and both empty and textual no-overlay maps. It executes:

1. the private legacy Combiner 1.13 oracle; and
2. `python -m nvt_combiner` with the exact same positional arguments.

For both CRC methods it asserts equal return code, stdout, stderr, complete
output bytes, and output SHA-256. The current characterized output hashes are:

| CRC method | SHA-256 |
| --- | --- |
| CRC8 | `031b3439ae9a758353b1666fecad1b7a86ad9d3546f72cd988bb89359f961b08` |
| CRC32 | `cc4c29643bcf1bcbce3e1ceac8701f0ef5377819f219cecab391421249be5f159` |

## Packaged EXE check

The same CRC8 fixture was built with PyInstaller 6.21.0 and run through the
generated one-file `Combiner.exe`. It matched the reference EXE's exit code
and console output; both output files were 262,144 bytes, had the CRC8 hash
above, and had no differing byte. The generated EXE was intentionally left in
ignored `artifacts/`; its environment-specific SHA-256 was
`b8468bc8104dc5b2809ea1827d7b24397a341dc59e2555053173a33b66d70813`.

## Basic overlay check

`tests/module/test_nt51932_overlay.py` verifies one ordinary
`_ovly_table =` descriptor-table map against the pinned EXE for both CRC
methods.  It compares process result, console output and all 256 KiB bytes.

| CRC method | SHA-256 |
| --- | --- |
| CRC8 | `15260dd268c0eba40a6859e145719edca937c19c8cfe974ff3b5a49d3299357c` |
| CRC32 | `6988ef30d398234c67bcefdd87b8d4eef0223d341f358cf958ac16b93be5dfc5` |

## Explicit exclusions

- HostDL/Process `OverlayDLMaddr` mutation and uncharacterized/malformed
  multiple overlay tables.
- Firmware exceeding the legacy 256/512 KiB buffer allocation.
- Undefined C behavior such as a block source range extending past its source
  file, missing `argv[1]`, or invalid pointer offsets.
- Any assertion of full NT51929 golden parity: the owner evidence proves its
  empty-map equivalence, while this test is only a public synthetic oracle.

`tests/module/test_nt51932_arity.py` also covers the characterized incomplete
block-tuple failure: legacy opens/checks `map.txt` first, then emits the
parameter-format error.  Python preserves that observable order.
