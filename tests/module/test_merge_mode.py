from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
from tests.support.differential import REFERENCE_EXE
MODE = "MERGE_MODE"

def fixture(directory: Path) -> list[str]:
    (directory / "a.bin").write_bytes(b"xxABCD")
    (directory / "b.bin").write_bytes(b"1234EFGH")
    return [MODE, "output.bin", "a.bin", "0x2", "0x0", "4", "b.bin", "0x4", "0x4", "4"]

def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=env)

class MergeModeModuleTests(unittest.TestCase):
    def test_python_matches_reference_for_contiguous_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); reference_dir = root / "ref"; python_dir = root / "py"
            reference_dir.mkdir(); python_dir.mkdir()
            args = fixture(reference_dir); fixture(python_dir)
            reference = run([str(REFERENCE_EXE), *args], reference_dir)
            env = os.environ.copy(); env["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
            candidate = run([sys.executable, "-m", "nvt_combiner", *args], python_dir, env)
            self.assertEqual(reference.returncode, candidate.returncode, candidate.stdout + candidate.stderr)
            self.assertEqual(reference.stdout, candidate.stdout)
            self.assertEqual(reference.stderr, candidate.stderr)
            self.assertEqual((reference_dir / "output.bin").read_bytes(), (python_dir / "output.bin").read_bytes())
