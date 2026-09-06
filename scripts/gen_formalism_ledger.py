#!/usr/bin/env python3
"""Regenerate ``data/formalism_claim_ledger.json``.

Thin orchestrator: parsing and derivation live in
``black_line.formalism_ledger``; this file only guards the invocation.
"""

from __future__ import annotations

from _cli import require_no_arguments

from black_line.formalism_ledger import build_ledger


def main() -> int:
    require_no_arguments("gen_formalism_ledger.py")
    print(build_ledger())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
