"""Run private legacy differentials only when their oracle is supplied."""

import os
from pathlib import Path

import pytest


def pytest_collection_modifyitems(items):
    oracle = os.environ.get("NVT_COMBINER_LEGACY_ORACLE")
    if oracle and Path(oracle).is_file():
        return

    marker = pytest.mark.skip(
        reason="set NVT_COMBINER_LEGACY_ORACLE to an existing private legacy Combiner 1.13 EXE"
    )
    for item in items:
        path = Path(str(item.path))
        is_module = path.parent.name == "module"
        is_packaged = path.name == "test_supported_modes.py" and path.parent.name == "packaged"
        if (is_module or is_packaged) and (
            "REFERENCE_EXE" in vars(item.module) or "EXE" in vars(item.module)
        ):
            item.add_marker(marker)
