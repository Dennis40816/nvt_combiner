# NT51950 A/B merge module gate

## Supported interface

```text
NT51950BASED_MERGE_AB_MODE <CRC8|CRC32> <a-code-bin> <b-code-bin> <output-bin> <b-code-offset>
```

The module preserves base-zero offset parsing, relocates B-code ILM and DLM
start addresses at `0xA100` and `0xA110`, then calculates the header CRC over
the relocated 48-byte (`0x2F` size-code) header and stores it at `0xA130`.

## Differential coverage

`tests/module/test_nt51950_merge_ab.py` compares the pinned 1.13 executable
and Python module with identical arguments for both `CRC8` and `CRC32`. It
requires equality of exit code, stdout, stderr, and every output byte. A
separate test locks the overlap failure console output and no-output-file
behavior.

## Explicit exclusions

- Legacy uninitialized output gaps where A is shorter than B offset.
- B code shorter than the `0xA130` header CRC field.
- `NT51950BASED_NORMAL_MODE`, which has its own map and FWConfig behavior.
