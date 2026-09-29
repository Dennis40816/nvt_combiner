from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from nvt_combiner.postbuild import staged_overlay_map
from nvt_combiner.primitives.files import atomic_write_bytes as real_atomic_write_bytes


class StagedOverlayMapSafetyTests(unittest.TestCase):
    @staticmethod
    def _arguments(firmware: Path) -> list[str]:
        return ["CRC_Enable", str(firmware), "block.bin", "0", "0", "0"]

    def test_stage_failure_reports_paths_without_creating_a_partial_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            firmware = root / "fw.bin"
            source = root / "supplied-map.txt"
            firmware.write_bytes(b"firmware")
            source.write_bytes(b"overlay map")

            with patch("nvt_combiner.postbuild.atomic_write_bytes", side_effect=OSError("disk full")):
                with self.assertRaisesRegex(
                    ValueError,
                    r'failed to stage overlay map: source=".*supplied-map.txt"; '
                    r'target=".*map.txt"; backup="not-created"; error=disk full',
                ):
                    with staged_overlay_map(self._arguments(firmware), str(source)):
                        self.fail("staging failure must not enter the Combiner body")

            self.assertFalse((root / "map.txt").exists())

    def test_stale_backup_is_rejected_with_recovery_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            firmware = root / "fw.bin"
            source = root / "supplied-map.txt"
            backup = root / ".map.txt.nvt-combiner.backup"
            firmware.write_bytes(b"firmware")
            source.write_bytes(b"overlay map")
            backup.write_bytes(b"original map")

            with self.assertRaisesRegex(
                ValueError,
                r"stale overlay-map backup exists: .*restore or remove the backup before retrying",
            ):
                with staged_overlay_map(self._arguments(firmware), str(source)):
                    self.fail("a stale recovery backup must stop staging")

            self.assertEqual(b"original map", backup.read_bytes())

    def test_combiner_os_error_is_not_mislabeled_as_a_staging_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            firmware = root / "fw.bin"
            source = root / "supplied-map.txt"
            target = root / "map.txt"
            firmware.write_bytes(b"firmware")
            source.write_bytes(b"new overlay map")
            target.write_bytes(b"original map")

            with self.assertRaisesRegex(OSError, r"combiner read failure"):
                with staged_overlay_map(self._arguments(firmware), str(source)):
                    raise OSError("combiner read failure")

            self.assertEqual(b"original map", target.read_bytes())
            self.assertFalse((root / ".map.txt.nvt-combiner.backup").exists())

    def test_restore_failure_preserves_the_original_map_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            firmware = root / "fw.bin"
            source = root / "supplied-map.txt"
            target = root / "map.txt"
            backup = root / ".map.txt.nvt-combiner.backup"
            firmware.write_bytes(b"firmware")
            source.write_bytes(b"new overlay map")
            target.write_bytes(b"original map")
            call_count = 0

            def fail_only_restore(path: Path, data: bytes) -> None:
                nonlocal call_count
                call_count += 1
                if call_count == 3:
                    raise OSError("restore denied")
                real_atomic_write_bytes(path, data)

            with patch("nvt_combiner.postbuild.atomic_write_bytes", side_effect=fail_only_restore):
                with self.assertRaisesRegex(
                    ValueError,
                    r'failed to restore overlay map: target=".*map.txt"; '
                    r'backup=".*\.map.txt\.nvt-combiner\.backup"; error=restore denied',
                ):
                    with staged_overlay_map(self._arguments(firmware), str(source)):
                        self.assertEqual(b"new overlay map", target.read_bytes())

            self.assertEqual(b"new overlay map", target.read_bytes())
            self.assertEqual(b"original map", backup.read_bytes())


if __name__ == "__main__":
    unittest.main()
