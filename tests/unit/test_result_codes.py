from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.primitives.result_codes import INPUT_FAIL, IO_FAIL, RUNTIME_FAIL, RUNTIME_SUCCESS


class TestLegacyResultCodes(unittest.TestCase):
    def test_runtime_status_values_preserve_legacy_process_results(self) -> None:
        self.assertEqual(0, RUNTIME_SUCCESS)
        self.assertEqual(-1, RUNTIME_FAIL)
        self.assertEqual(1, IO_FAIL)
        self.assertEqual(1, INPUT_FAIL)
