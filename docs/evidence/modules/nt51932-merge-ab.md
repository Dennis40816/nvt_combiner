# NT51932 A/B merge module gate

## Supported interface

```text
NT51932BASED_MERGE_AB_MODE <a-code-bin> <b-code-bin> <output-bin> <b-code-offset>
```

The implementation preserves the C `strtol(..., 0)` offset interpretation,
requires `argc == 6`, concatenates A and B at the requested offset, and
relocates the B-code ILM, DLM, and DLM_DIFF addresses at offsets `0x7164`,
`0x7168`, and `0x716C` respectively.

## Differential coverage

`tests/module/test_nt51932_merge_ab.py` runs the pinned 1.13 executable and
the Python module with identical relative arguments. It compares exit code,
stdout, stderr, and every output byte for a successful merge. It also compares
the legacy overlap failure, including its no-trailing-newline console message
and absence of an output file.

The fixture uses an A code exactly as large as the B-code offset. This avoids
the legacy C implementation's uninitialized gap when `a_code_size < offset`.

## Explicit exclusions

- Any output with an uninitialized A/B gap from the C `malloc` behavior.
- Invalid B files too short to contain the three relocated fields.
- Other IC-family A/B layouts, including NT51950's different header-CRC path.
