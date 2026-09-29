# Architecture optimization branch

Branch: `refactor/architecture-optimization`

## Completed safe refactors

- A single Python version source drives setuptools metadata and the generated
  Windows EXE version resource. `scripts/build-release.ps1` performs build,
  resource verification, packaged differential gate, wheel build and hashing.
- `tests/support/differential.py` centralizes reference-process execution and
  the source-tree Python environment for future module differential cases.
- `PreparationResult` replaces the anonymous `(status, input)` tuple returned
  by the common map-based normal preamble. The legacy numerical status and
  stdout timing remain unchanged.

## Layout decision

No generic IC layout table is introduced in this branch. The current offsets
are not interchangeable configuration: they participate in each family’s
specific buffer-size, FwConfig-copy and CRC-write order. A generic callback or
offset dictionary would make those contracts less visible without reducing
verified behavior.

Any future layout extraction must be one IC family at a time and first add
reference cases that cover all reads/writes moved by that layout.

## NT51927 memory decision

`NT51927BASED_GEN_CRC_MODE` deliberately builds three `0xFFFFFF` RAM images.
Replacing them with sparse or streaming storage is deferred: before doing so,
the differential suite needs explicit cases for overlapping sections,
zero-filled untouched ranges, and multi-header linked-flash traversal. This
avoids silently changing CRC inputs while chasing memory savings.
