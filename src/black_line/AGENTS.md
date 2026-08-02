# `black_line` package

Executable method: registry, evaluator, analytics, invariants, serialization,
envelope export, and deterministic figures.

- Public API: `__init__.py` re-exports stable surfaces including analytics
  (`refresh_horizon`, `staleness_profile`, `summarize_assessments`, …).
- `envelope.py` — report envelope export for cross-instrument transport
- `version.py` — single source of truth for the package version
- `models.py` is a public alias for `model/` (same symbols; both paths are first-class).
- `model/` — data classes and type definitions
- Figures: `figures/` owns builders and `validate_generated_figures`.

Validation: `uv run pytest tests/ --cov=src --cov-branch --cov-fail-under=90`.
