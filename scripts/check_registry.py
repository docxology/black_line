#!/usr/bin/env python3
"""Run the structural review battery and print the registry digest.

Exits non-zero if any structural check fails, so the script can gate CI.
"""

from _cli import require_no_arguments

from black_line import BLACK_PRACTICES, all_invariants, registry_digest


def main() -> int:
    require_no_arguments("check_registry.py")
    results = all_invariants()
    for check in results:
        print(f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.detail}")
    print(f"practices={len(BLACK_PRACTICES)} digest={registry_digest(BLACK_PRACTICES)}")
    return 0 if all(check.passed for check in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
