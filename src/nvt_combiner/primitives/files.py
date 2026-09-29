"""Function-level ports of legacy ``Utilities.c`` binary helpers."""

from __future__ import annotations

import os
from os import PathLike
from pathlib import Path
import tempfile

from nvt_combiner.primitives.result_codes import IO_FAIL, RUNTIME_SUCCESS

PathArgument = str | PathLike[str]


def atomic_write_bytes(file_path: PathArgument, buffer: bytes | bytearray) -> None:
    """Write beside the target and atomically replace it after a full flush."""
    path = Path(file_path)
    descriptor = -1
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        stream = os.fdopen(descriptor, "wb")
        descriptor = -1
        with stream:
            written = stream.write(buffer)
            if written != len(buffer):
                raise OSError(f"short write: expected={len(buffer)}, actual={written}")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def read_file(file_path: PathArgument) -> tuple[int, bytes | None]:
    """Port ``ReadFile`` as ``(status, buffer)`` without adding path recovery.

    Status ``0`` mirrors C success; ``1`` mirrors its open-file failure.  The
    caller remains responsible for any mode-specific validation.
    """
    path = str(file_path)
    try:
        with open(path, "rb") as stream:
            return RUNTIME_SUCCESS, stream.read()
    except OSError:
        print(f"Open file fail: {path}")
        return IO_FAIL, None


def write_file(file_path: PathArgument, buffer: bytes | bytearray) -> int:
    """Atomically replace a complete output while retaining legacy status."""
    path = str(file_path)
    try:
        atomic_write_bytes(path, buffer)
    except OSError as error:
        print(f'Write file fail: path="{path}"; error={error}')
        return IO_FAIL
    return RUNTIME_SUCCESS
