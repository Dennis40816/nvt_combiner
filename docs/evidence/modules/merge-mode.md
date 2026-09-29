# Generic merge-mode module gate

`MERGE_MODE` preserves its legacy positional interface:

```text
MERGE_MODE <output-bin> <input-bin> <source-hex> <destination-hex> <length-dec> [...]
```

The module test runs two contiguous blocks through the pinned 1.13 EXE and the
Python implementation, requiring equal process result, console output, and
output bytes. It covers the C mode's source/destination/length parsing and
copy diagnostics.

Gaps before or between destination blocks remain excluded because C writes
uninitialized `malloc` content for those bytes, which is not a stable external
contract to reproduce.
