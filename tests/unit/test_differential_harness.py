from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


from tests.support.differential import python_environment, run_process


class TestDifferentialHarness(unittest.TestCase):
    def test_python_environment_places_the_source_tree_first(self) -> None:
        environment = python_environment()

        self.assertEqual(str(Path(__file__).resolve().parents[2] / "src"), environment["PYTHONPATH"].split(";")[0])

    def test_run_process_captures_console_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_process([sys.executable, "-c", "print('differential harness')"], Path(temporary))

        self.assertEqual(0, result.returncode)
        self.assertEqual("differential harness\n", result.stdout)
        self.assertEqual("", result.stderr)
