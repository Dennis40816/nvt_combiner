# Buffer and output write-safety gate

Branch: `fix/write-safety-guards`

The protection boundary is deliberately below the IC orchestration layer.
Every buffer copy and CRC input is checked as an exact range before it is
read or mutated.  Every little-endian word access is also range checked, so a
short header produces a deterministic diagnostic instead of a Python
`struct.error` or a C out-of-bounds access.

An invalid range reports:

- mode/IC and operation context;
- source or destination range name;
- `start`, `length`, computed `end`;
- complete `buffer_size` and remaining `available` bytes.

Negative CLI source, destination, length, and A/B offsets are rejected by
field name.  Allocation overflow, memory exhaustion, unexpected OS I/O
errors, malformed metadata, NT51927 linked-header cycles, and map read errors
have separate top-level messages.  Valid zero-length legacy block copies stay
as no-ops even when their unused address is beyond an empty source.

Output writes use a same-directory temporary file and `os.replace`.  The
existing output is therefore unchanged if writing, flushing, syncing, or
replacing the temporary file fails.  Temporary files are cleaned on failure.
The optional overlay-map wrapper additionally keeps a persistent recovery
backup until the original `map.txt` has been restored.

Verification on 2026-07-17:

- 81 function/unit tests passed, including injected short-write/replace,
  postbuild stage/restore, stale-backup, word-access, CRC-range, and CLI-log
  failures.
- 42 module tests passed.  Five malformed-input cases verify no output
  replacement for block source overrun, MERGE overrun, negative destination,
  NT51932 config overrun, and an NT51927 header cycle.
- Every existing valid Python-vs-Combiner-1.13 module differential still
  matched return code, console streams, and all output bytes.
- The PyInstaller `2.0.0.1` EXE passed its Windows version-resource check and
  all packaged supported-mode differential cases.
