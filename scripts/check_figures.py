#!/usr/bin/env python3
"""Thin CLI: fail closed when generated figures drift from the live contract."""

from __future__ import annotations

from _cli import require_no_arguments

from black_line.figures import FIGURE_SPECS
from black_line.figures.validate import validate_generated_figures


def main() -> int:
    require_no_arguments("check_figures.py")
    errors = validate_generated_figures()
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"PASS generated figure contract: {len(FIGURE_SPECS)} figures + cover")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
