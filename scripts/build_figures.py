#!/usr/bin/env python3
"""Thin CLI wrapper for the source-owned deterministic figure builder."""

from __future__ import annotations

from _cli import require_no_arguments

from black_line.figures import build_figures


def main() -> int:
    require_no_arguments("build_figures.py")
    generated = build_figures()
    print(f"generated {len(generated)} figures under output/figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
