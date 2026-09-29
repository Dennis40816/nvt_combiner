# NT51929 no-overlay map equivalence

## Decision

For the current NT51929 CtrlRAM postbuild, complete two-stage `NT51932BASED_NORMAL_MODE CRC8` flow, an empty `output/map.txt` and the 51929 golden `T01_map.txt` are equivalent **when neither map declares an overlay table**.

The owner-run evidence reports that both maps open successfully and print `This FW has no overlay.`. Both results are 262,144 bytes; their SHA-256 is identical:

```text
e47fa6e1b15c2a51d01f845d1be225684727908b4ddf9d949fc8891f4441ea45
```

A byte-by-byte comparison reports zero differences.

## Scope and implementation policy

- This conclusion is restricted to the verified no-overlay NT51929 flow. It must not be extrapolated to a map containing `_ovly_table =`.
- The existing `nvt_fw_combiner` runner writes an empty staging `output/map.txt` at `LegacyCombinerPostbuildProcessor.cs:106`; this remains valid for the stated scope.
- The legacy-compatible `Combiner.exe <mode> ...` argv contract remains unchanged. It still discovers `map.txt` beside the firmware path, then `output/map.txt`, exactly as the C program does.
- A future **postbuild wrapper** may expose `--overlay-map-txt <path>`. If omitted, it writes an empty staging `map.txt`; if supplied, it stages the supplied map at that legacy path before invoking the unchanged legacy command. The option is deliberately not added to the legacy Combiner command line.
- Any overlay implementation must be accompanied by a real overlay map, reference EXE run, and byte-level differential case before it is promoted.

## Provenance

The result above was supplied by the owner on 2026-07-10. The new repository's synthetic no-overlay test validates the same behavioral class, but it does not replace the private golden evidence.
