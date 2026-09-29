"""Named legacy process result codes.

The C executable exposes both ``-1`` and ``1`` failure results.  They must
remain numerically distinct even when a Python call site can describe the
failure more precisely.
"""

from __future__ import annotations


RUNTIME_SUCCESS = 0
RUNTIME_FAIL = -1
IO_FAIL = 1
INPUT_FAIL = 1
