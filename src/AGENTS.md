# Source tree contract

`src/` is a src-layout container. The only import package here is
`black_line/`; `src/__init__.py` is a package marker when present.

- Keep the `pythonpath = [".", "src"]` wiring in `pyproject.toml` aligned with this layout.
- Put implementation in `src/black_line/`. Do not move evaluator, analytics, or figure logic into `scripts/` or `tests/`.
- Figure builders live under `src/black_line/figures/`; `scripts/build_figures.py` is a thin CLI only.
- If the package path changes, update imports and `pyproject.toml` together, then run `uv run pytest tests/ --cov=src --cov-branch --cov-report=term-missing`.
