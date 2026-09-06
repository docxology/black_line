# Script contract

Every file in `scripts/` is a thin CLI over `src/`. Business logic belongs in
`src/black_line/`, not here.

## Files

- `_cli.py` — shared CLI infrastructure (argument parsing, output formatting)
- `build_figures.py` — calls `black_line.figures.build_figures()` and prints the output count
- `check_figures.py` — calls `black_line.figures.validate_generated_figures()` and exits non-zero on drift
- `check_registry.py` — runs `all_invariants()` over `BLACK_PRACTICES` and exits non-zero on failure
- `gen_formalism_ledger.py` — regenerates `data/formalism_claim_ledger.json` via `black_line.formalism_ledger.build_ledger()`

## Canonical commands

- `uv run pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing`
- `uv run ruff check src tests scripts && uv run ruff format --check src tests scripts`
- `uv run python scripts/check_registry.py`
- `uv run python scripts/build_figures.py`
- `uv run python scripts/check_figures.py`
- `uv run python scripts/gen_formalism_ledger.py`
