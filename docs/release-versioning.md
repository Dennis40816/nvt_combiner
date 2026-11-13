# Release versioning

`nvt_combiner` uses a four-component release version.  The current version is
**2.0.0.2**.

The 2.0.0.x versions are preliminary builds that identify the Python port.
The owner set this on 2026-11-13.  The first formal release will be
**2.1.0.0**.  The existing tags `2.0.0.0` and `2.0.0.1` and the `2.0.0.1`
GitHub release of the private repository stay as they are.

- `nvt_combiner.version.__version__` is the only version source; setuptools
  derives wheel metadata from it.
- `scripts/build-release.ps1` generates the Windows version resource and
  writes EXE `FileVersion`/`ProductVersion` exactly as that four-component
  source version.
- The legacy console banner is `Combiner version:1.14.0.0`. The owner set
  it on 2026-11-13. It is part of the reference EXE's observable output and
  is covered by differential tests. The banner is separate from the release
  version above.

Run `./scripts/build-release.ps1` for the release build.  It generates the
resource at an absolute path, verifies its `FileVersion` and `ProductVersion`
through Windows, runs the packaged differential gate, builds the wheel, and
prints the EXE hash.
