# Release versioning

`nvt_combiner` uses a four-component release version.  The current version is
**2.0.0.1**.

- `nvt_combiner.version.__version__` is the only version source; setuptools
  derives wheel metadata from it.
- `scripts/build-release.ps1` generates the Windows version resource and
  writes EXE `FileVersion`/`ProductVersion` exactly as that four-component
  source version.
- The legacy `Combiner version:1.13.0.0` console banner is intentionally
  unchanged: it is part of the reference EXE's observable output and is
  covered by differential tests.

Run `./scripts/build-release.ps1` for the release build.  It generates the
resource at an absolute path, verifies its `FileVersion` and `ProductVersion`
through Windows, runs the packaged differential gate, builds the wheel, and
prints the EXE hash.
