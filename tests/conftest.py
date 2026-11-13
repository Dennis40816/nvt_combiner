"""Run private legacy differentials only when their oracle is supplied."""

from pathlib import Path
import sys

import pytest


LEGACY_REASON = "set NVT_COMBINER_LEGACY_ORACLE to an existing private legacy Combiner 1.13 EXE"
NT51928B_REASON = (
    "set NVT_COMBINER_NT51928B_ORACLE to the private NT51928B reference EXE "
    "built from the 2026-11-13 C source"
)


def pytest_collection_modifyitems(items):
    differential = sys.modules.get("tests.support.differential")
    nt51928b_oracle = getattr(differential, "NT51928B_REFERENCE_EXE", None)
    for item in items:
        path = Path(str(item.path))
        is_module = path.parent.name == "module"
        is_packaged = path.name == "test_supported_modes.py" and path.parent.name == "packaged"
        if not (is_module or is_packaged):
            continue
        module_vars = vars(item.module)
        oracle = module_vars.get("REFERENCE_EXE", module_vars.get("EXE"))
        if oracle is None or Path(oracle).is_file():
            continue
        reason = NT51928B_REASON if oracle is nt51928b_oracle else LEGACY_REASON
        item.add_marker(pytest.mark.skip(reason=reason))
