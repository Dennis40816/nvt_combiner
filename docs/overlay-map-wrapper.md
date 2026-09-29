# Optional overlay-map postbuild wrapper

`Combiner.exe` keeps its legacy positional CLI exactly unchanged.  If the
calling pipeline needs to supply an overlay map explicitly, use the separate
Python wrapper:

```powershell
nvt-combiner-postbuild --overlay-map-txt C:\path\to\map.txt -- `
  CRC_Enable fw.bin block.bin 0x0 0x20000 16
```

Without `--overlay-map-txt`, the wrapper calls Combiner with no added behavior.
With the flag, it temporarily stages the supplied map as the sibling
`map.txt` of the legacy firmware path, calls the unchanged positional Combiner
arguments, then restores the previous `map.txt` (or removes the temporary one).
The option is only valid for map-based normal selectors; it intentionally is
not a flag accepted by the compatibility `Combiner.exe`.

Staging and restoration use atomic replacement.  If an existing `map.txt`
must be displaced, its bytes are first saved as
`.map.txt.nvt-combiner.backup`.  A successful restoration removes that backup.
If restoration fails, the backup is deliberately retained and the error names
both target and recovery paths.  A later run refuses to overwrite a stale
backup and tells the operator to restore or remove it first.

`tests/module/test_postbuild_overlay_map.py` differentially verifies both
restoration cases: no original `map.txt`, and an existing map whose exact
bytes must be restored after the run.  Unit failure-injection cases additionally
cover staging failure, stale backup detection, and preservation after a
simulated restoration failure.
