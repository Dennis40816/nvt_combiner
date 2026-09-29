from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.module.test_normal_overlay import REFERENCE_EXE, run, write_case


ROOT = Path(__file__).resolve().parents[2]


class TestPostbuildOverlayMap(unittest.TestCase):
    def test_explicit_map_flag_matches_reference_and_restores_map_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            wrapper_dir = root / "wrapper"
            reference_dir.mkdir()
            wrapper_dir.mkdir()
            write_case(reference_dir)
            write_case(wrapper_dir)
            supplied_map = wrapper_dir / "supplied-overlay-map.txt"
            supplied_map.write_bytes((wrapper_dir / "map.txt").read_bytes())
            (wrapper_dir / "map.txt").unlink()
            arguments = ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run(
                [
                    sys.executable,
                    "-m",
                    "nvt_combiner.postbuild",
                    "--overlay-map-txt",
                    "supplied-overlay-map.txt",
                    "--",
                    *arguments,
                ],
                wrapper_dir,
                environment,
            )

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual(
                (reference_dir / "fw.bin").read_bytes(),
                (wrapper_dir / "fw.bin").read_bytes(),
            )
            self.assertFalse((wrapper_dir / "map.txt").exists())
            self.assertTrue(supplied_map.is_file())

    def test_explicit_map_flag_restores_an_existing_map(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference_dir = root / "reference"
            wrapper_dir = root / "wrapper"
            reference_dir.mkdir()
            wrapper_dir.mkdir()
            write_case(reference_dir)
            write_case(wrapper_dir)
            supplied_map = wrapper_dir / "supplied-overlay-map.txt"
            supplied_map.write_bytes((wrapper_dir / "map.txt").read_bytes())
            original_map = b"previous map state\n"
            (wrapper_dir / "map.txt").write_bytes(original_map)
            arguments = ["CRC_Enable", "fw.bin", "block.bin", "0x110", "0", "0"]

            reference = run([str(REFERENCE_EXE), *arguments], reference_dir)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            candidate = run(
                [
                    sys.executable,
                    "-m",
                    "nvt_combiner.postbuild",
                    "--overlay-map-txt",
                    "supplied-overlay-map.txt",
                    "--",
                    *arguments,
                ],
                wrapper_dir,
                environment,
            )

            self.assertEqual(reference.returncode, candidate.returncode)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual(
                (reference_dir / "fw.bin").read_bytes(),
                (wrapper_dir / "fw.bin").read_bytes(),
            )
            self.assertEqual(original_map, (wrapper_dir / "map.txt").read_bytes())
