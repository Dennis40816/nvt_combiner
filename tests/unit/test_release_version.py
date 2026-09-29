from __future__ import annotations

from pathlib import Path
import sys
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner import __version__
from nvt_combiner.version import __version__ as source_version


class TestReleaseVersion(unittest.TestCase):
    def test_python_and_package_metadata_use_one_version_source(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as project_file:
            project = tomllib.load(project_file)

        self.assertEqual("2.0.0.1", __version__)
        self.assertEqual(__version__, source_version)
        self.assertNotIn("version", project["project"])
        self.assertEqual(["version"], project["project"]["dynamic"])
        self.assertEqual(
            "nvt_combiner.version.__version__",
            project["tool"]["setuptools"]["dynamic"]["version"]["attr"],
        )
