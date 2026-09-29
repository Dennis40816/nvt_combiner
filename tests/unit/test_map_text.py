from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nvt_combiner.primitives.map_text import legacy_fgets_records, read_legacy_map_text


class TestLegacyMapTextReader(unittest.TestCase):
    def test_normalizes_windows_crlf_like_c_text_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            map_file = Path(temporary) / "map.txt"
            map_file.write_bytes(b"first\r\nsecond\r\n")

            self.assertEqual("first\nsecond\n", read_legacy_map_text(map_file))

    def test_splits_a_physical_line_at_the_499_character_fgets_limit(self) -> None:
        self.assertEqual(["A" * 499, "A\n"], legacy_fgets_records("A" * 500 + "\n"))
