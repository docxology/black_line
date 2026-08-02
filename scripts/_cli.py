#!/usr/bin/env python3
"""Shared argument guard for the project's thin CLI entry points.

None of these scripts takes an option or an operand: each one runs the same
fixed check against the checkout it lives in. That made every one of them
accept `--nope`, `garbage`, or a misspelled flag silently and exit 0, so a
typo in a CI line read as a pass. A gate that cannot reject its own invocation
is not a gate, so unexpected argv is a usage error here rather than a shrug.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence


def require_no_arguments(name: str, argv: Sequence[str] | None = None) -> None:
    """Exit non-zero when the caller passed anything this script cannot honour.

    Args:
        name: Script name to print in the usage line.
        argv: Argument vector to inspect, defaulting to ``sys.argv``. The
            first element is the program name and is ignored.

    Raises:
        SystemExit: With status 2 when any argument was supplied.
    """

    arguments = list(sys.argv[1:] if argv is None else list(argv)[1:])
    if arguments:
        raise SystemExit(
            f"{name}: takes no arguments, got {' '.join(arguments)!r}\n"
            f"usage: python scripts/{name} (no options, no operands)"
        )
