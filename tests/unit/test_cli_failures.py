from __future__ import annotations

from contextlib import redirect_stdout
import errno
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from nvt_combiner.cli import main
from nvt_combiner.primitives.result_codes import RUNTIME_FAIL


class CliFailureLoggingTests(unittest.TestCase):
    def test_allocation_overflow_reports_mode_and_error_type(self) -> None:
        output = StringIO()
        with patch("nvt_combiner.cli._dispatch", side_effect=OverflowError("range too large")):
            with redirect_stdout(output):
                status = main(["MERGE_MODE"])

        self.assertEqual(RUNTIME_FAIL, status)
        self.assertIn(
            'Runtime error: buffer allocation failed; mode="MERGE_MODE"; '
            "error_type=OverflowError; error=range too large",
            output.getvalue(),
        )

    def test_uncaught_os_error_reports_mode_and_filename(self) -> None:
        output = StringIO()
        error = OSError(errno.EIO, "simulated I/O failure", "input.bin")
        with patch("nvt_combiner.cli._dispatch", side_effect=error):
            with redirect_stdout(output):
                status = main(["CRC_Enable"])

        self.assertEqual(RUNTIME_FAIL, status)
        self.assertIn(
            'Runtime I/O error: mode="CRC_Enable"; path="input.bin"; '
            "error=[Errno 5] simulated I/O failure: 'input.bin'",
            output.getvalue(),
        )

    def test_malformed_metadata_error_is_returned_without_a_traceback(self) -> None:
        output = StringIO()
        with patch("nvt_combiner.cli._dispatch", side_effect=IndexError("missing field")):
            with redirect_stdout(output):
                status = main(["NT51932BASED_NORMAL_MODE"])

        self.assertEqual(RUNTIME_FAIL, status)
        self.assertIn(
            'Runtime error: malformed arguments or input metadata; '
            'mode="NT51932BASED_NORMAL_MODE"; error_type=IndexError; error=missing field',
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
