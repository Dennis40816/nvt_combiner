"""Compatibility dispatcher. Avoid argparse: legacy argv is positional."""

from __future__ import annotations

import sys

from nvt_combiner.primitives.result_codes import RUNTIME_FAIL
from nvt_combiner.primitives.safety import InputValidationError
from nvt_combiner.modes.nt51932 import AB_MODE as NT51932_AB_MODE
from nvt_combiner.modes.nt51932 import MODE as NT51932_NORMAL_MODE, run as run_nt51932, run_merge_ab as run_nt51932_ab
from nvt_combiner.modes.nt51950 import AB_MODE as NT51950_AB_MODE, NORMAL_MODE as NT51950_NORMAL_MODE, run_merge_ab as run_nt51950_ab, run_normal as run_nt51950_normal
from nvt_combiner.modes.nt51927 import MODE as NT51927_MODE, run as run_nt51927
from nvt_combiner.modes.merge import MODE as MERGE_MODE, run as run_merge
from nvt_combiner.modes.normal import MODES as NORMAL_MODES, run as run_normal
from nvt_combiner.modes.nt36672 import MODE as NT36672_MODE, run as run_nt36672
from nvt_combiner.modes.nt51931 import MODE as NT51931_MODE, run as run_nt51931
from nvt_combiner.modes.nt51930 import MODE as NT51930_MODE, run as run_nt51930
from nvt_combiner.modes.nt51928b import MODE as NT51928B_MODE, run as run_nt51928b


def _dispatch(arguments: list[str]) -> int:
    """Route one validated mode selector without changing positional argv."""
    if arguments[0] == NT51932_NORMAL_MODE:
        return run_nt51932(arguments)
    if arguments[0] == NT51932_AB_MODE:
        return run_nt51932_ab(arguments)
    if arguments[0] == NT51950_AB_MODE:
        return run_nt51950_ab(arguments)
    if arguments[0] == NT51950_NORMAL_MODE:
        return run_nt51950_normal(arguments)
    if arguments[0] == NT51927_MODE:
        return run_nt51927(arguments)
    if arguments[0] == NT36672_MODE:
        return run_nt36672(arguments)
    if arguments[0] == NT51931_MODE:
        return run_nt51931(arguments)
    if arguments[0] == NT51930_MODE:
        return run_nt51930(arguments)
    if arguments[0] == NT51928B_MODE:
        return run_nt51928b(arguments)
    if arguments[0] == MERGE_MODE:
        return run_merge(arguments)
    if arguments[0] in NORMAL_MODES:
        return run_normal(arguments)

    print(f"invalid argument: {arguments[0]}")
    return RUNTIME_FAIL


def main(argv: list[str] | None = None) -> int:
    """Dispatch one legacy positional invocation and return its process code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    print("--------------------------------------")
    print("Combiner version:1.13.0.0")

    # The C binary crashes if argv[1] is absent; malformed calls are not a
    # compatibility contract, so migration reports a deterministic failure.
    if not arguments:
        print("missing mode argument")
        return RUNTIME_FAIL

    try:
        return _dispatch(arguments)
    except InputValidationError as error:
        print(f"Validation error: {error}")
        return RUNTIME_FAIL
    except (MemoryError, OverflowError) as error:
        print(
            f'Runtime error: buffer allocation failed; mode="{arguments[0]}"; '
            f"error_type={type(error).__name__}; error={error}"
        )
        return RUNTIME_FAIL
    except OSError as error:
        print(
            f'Runtime I/O error: mode="{arguments[0]}"; '
            f'path="{error.filename or "unknown"}"; error={error}'
        )
        return RUNTIME_FAIL
    except (IndexError, ValueError) as error:
        print(
            f'Runtime error: malformed arguments or input metadata; mode="{arguments[0]}"; '
            f"error_type={type(error).__name__}; error={error}"
        )
        return RUNTIME_FAIL
