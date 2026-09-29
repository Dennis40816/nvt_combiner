"""Optional postbuild wrapper; it does not change legacy Combiner argv."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from pathlib import Path
import sys
from typing import Iterator

from nvt_combiner.cli import main as combiner_main
from nvt_combiner.primitives.files import atomic_write_bytes
from nvt_combiner.primitives.legacy_args import firmware_path_for_legacy_arguments


@contextmanager
def staged_overlay_map(legacy_arguments: list[str], overlay_map_path: str) -> Iterator[None]:
    """Temporarily expose an explicit map as the legacy sibling ``map.txt``."""
    firmware_path = firmware_path_for_legacy_arguments(legacy_arguments)
    if firmware_path is None:
        raise ValueError("--overlay-map-txt requires a map-based normal-mode legacy invocation")

    source = Path(overlay_map_path)
    if not source.is_file():
        raise ValueError(f"overlay map file not found: {source}")
    target = Path(firmware_path).parent / "map.txt"
    if source.resolve() == target.resolve():
        yield
        return

    backup = target.with_name(f".{target.name}.nvt-combiner.backup")
    if backup.exists():
        raise ValueError(
            f'stale overlay-map backup exists: backup="{backup}"; '
            f'target="{target}"; restore or remove the backup before retrying'
        )

    try:
        staged_contents = source.read_bytes()
        original = target.read_bytes() if target.exists() else None
    except OSError as error:
        raise ValueError(
            f'failed to read overlay map: source="{source}"; target="{target}"; error={error}'
        ) from error

    backup_created = False
    keep_backup = False
    try:
        if original is not None:
            try:
                atomic_write_bytes(backup, original)
            except OSError as error:
                raise ValueError(
                    f'failed to create overlay-map backup: backup="{backup}"; '
                    f'target="{target}"; error={error}'
                ) from error
            backup_created = True
        # Stage at the only path the legacy executable understands. Atomic
        # replacement prevents a short write from leaving a partial map.txt.
        try:
            atomic_write_bytes(target, staged_contents)
        except OSError as error:
            raise ValueError(
                f'failed to stage overlay map: source="{source}"; target="{target}"; '
                f'backup="{backup if backup_created else "not-created"}"; error={error}'
            ) from error
        try:
            yield
        finally:
            try:
                if original is None:
                    target.unlink(missing_ok=True)
                else:
                    atomic_write_bytes(target, original)
            except OSError as error:
                keep_backup = backup_created
                raise ValueError(
                    f'failed to restore overlay map: target="{target}"; '
                    f'backup="{backup if backup_created else "not-created"}"; error={error}'
                ) from error
    finally:
        if backup_created and not keep_backup:
            try:
                backup.unlink(missing_ok=True)
            except OSError as error:
                raise ValueError(
                    f'failed to remove overlay-map backup: backup="{backup}"; '
                    f'target="{target}"; error={error}'
                ) from error


def main(argv: list[str] | None = None) -> int:
    """Run Combiner with optional map staging and unchanged positional argv."""
    parser = argparse.ArgumentParser(prog="nvt-combiner-postbuild")
    parser.add_argument("--overlay-map-txt", metavar="PATH")
    parser.add_argument("legacy_arguments", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(argv)
    legacy_arguments = list(parsed.legacy_arguments)
    if legacy_arguments[:1] == ["--"]:
        legacy_arguments = legacy_arguments[1:]

    if parsed.overlay_map_txt is None:
        return combiner_main(legacy_arguments)
    try:
        with staged_overlay_map(legacy_arguments, parsed.overlay_map_txt):
            return combiner_main(legacy_arguments)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
