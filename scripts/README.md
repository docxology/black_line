# Scripts

Thin CLIs over `src/black_line/`. See [`AGENTS.md`](AGENTS.md).

| Script | Purpose | Delegates to | Command |
|--------|---------|--------------|---------|
| `build_figures.py` | Build deterministic figures and registry | `black_line.figures.build_figures()` | `uv run python scripts/build_figures.py` |
| `check_figures.py` | Validate the generated-figure mirror | `black_line.figures.validate_generated_figures()` | `uv run python scripts/check_figures.py` |
| `check_registry.py` | Run registry invariants | `black_line.all_invariants()` | `uv run python scripts/check_registry.py` |
| `gen_formalism_ledger.py` | Regenerate the formalism claim ledger | `black_line.formalism_ledger.build_ledger()` | `uv run python scripts/gen_formalism_ledger.py` |
