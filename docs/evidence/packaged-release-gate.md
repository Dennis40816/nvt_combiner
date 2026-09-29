# Packaged EXE release gate

The release gate first runs the unit and module suites, then builds a one-file
EXE with the Windows version resource:

```powershell
.\scripts\build-release.ps1
```

The script reads the generated EXE's `FileVersion` and `ProductVersion`
through Windows and requires both to equal the four-component Python release
version (currently `2.0.0.1`).  The packaged suite independently repeats that
resource check.  It also runs the produced EXE and the pinned
Combiner 1.13 reference with identical positional arguments, comparing return
code, stdout, stderr and all output binary bytes for these success cases:
generic CRC-disabled, CRC-enabled and basic-overlay normal, `MERGE_MODE`,
`NT36672A`, `NT51927`, each map-based normal family with its ordinary
basic-overlay case, NT51932 normal/A-B, and NT51950 normal/A-B.

On this workstation, PyInstaller 6.21.0 / Python 3.13.5 produced an
8,472,110-byte executable with SHA-256
`52c0189099dc09c0d62b153f7c60f555b61d4b17a486fd492c00ae0b585e8761`.
All 81 unit tests, 42 module tests, the package-version resource test, and 20
packaged differential cases passed.  The binary is intentionally left under
ignored `artifacts/`; its hash is evidence, not a reproducible release
identifier across Python/PyInstaller environments.
