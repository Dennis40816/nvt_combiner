"""Checks for Windows metadata embedded in the packaged executable."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import unittest

from nvt_combiner.version import __version__


class TestReleaseMetadata(unittest.TestCase):
    """The EXE resource version must follow the package version source."""

    @unittest.skipUnless(
        os.environ.get("COMBINER_EXE"),
        "COMBINER_EXE is required to inspect a packaged executable",
    )
    def test_windows_version_resource_matches_package_version(self) -> None:
        executable = Path(os.environ["COMBINER_EXE"]).resolve()
        expected_version = __version__
        escaped_path = str(executable).replace("'", "''")
        command = (
            "$version = (Get-Item -LiteralPath '"
            f"{escaped_path}'"
            ").VersionInfo; "
            '"$($version.FileVersion)|$($version.ProductVersion)"'
        )

        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            f"{expected_version}|{expected_version}",
        )


if __name__ == "__main__":
    unittest.main()
