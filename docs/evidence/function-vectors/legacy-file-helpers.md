# Legacy `Utilities.c` function contract

`ReadFile` and `WriteFile` have been ported as independent functions before
they are used in any mode module.

| C function | Python function | Success | Open failure |
| --- | --- | --- | --- |
| `ReadFile(char*, unsigned char**, unsigned int*)` | `read_file(path) -> (status, bytes \| None)` | `(0, exact bytes)` | prints `Open file fail: <path>`; returns `(1, None)` |
| `WriteFile(char*, unsigned char*, unsigned int)` | `write_file(path, buffer) -> status` | writes raw bytes using `wb`; returns `0` | prints `Open file fail: <path>`; returns `1` |

The functions intentionally do not create parent directories, add retries, or
translate paths. Those changes would alter the legacy observable behavior.
Their unit tests cover binary-byte preservation, overwrite/truncate semantics,
and both error messages. Mode-level reference EXE coverage is deferred until
the later A/B mode module phase.
