"""Shared process helpers for legacy-versus-Python differential tests."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_EXE = Path(os.environ.get("NVT_COMBINER_LEGACY_ORACLE") or ".")


def run_process(
    command: list[str],
    cwd: Path,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one side of a differential case with captured text streams."""
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=environment)


def python_environment() -> dict[str, str]:
    """Return an environment that imports the source tree under test first."""
    environment = os.environ.copy()
    source_path = str(ROOT / "src")
    existing_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = f"{source_path};{existing_python_path}" if existing_python_path else source_path
    return environment


def run_python(arguments: list[str], cwd: Path, module: str = "nvt_combiner") -> subprocess.CompletedProcess[str]:
    """Run Python implementation with the exact argument sequence for a case."""
    return run_process([sys.executable, "-m", module, *arguments], cwd, python_environment())
