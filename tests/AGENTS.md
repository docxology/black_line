# Test folder contract

`tests/` exercises the public API, evaluator, registry, invariants, analytics,
serialization, deterministic figures, manuscript bindings, and cross-cutting
contracts.

## Test modules

- `test_public_api.py` — imports, version markers, and the `models` public alias
- `test_black_line.py` — core package smoke and default call forms
- `test_evaluator.py` — status semantics and intake notes
- `test_registry.py` — practice registry tuple and lookups
- `test_invariants.py` — structural battery and planted-bad cases
- `test_analytics.py` — coverage matrix, staleness profile, batch summary, refresh horizon, monotonicity sweeps
- `test_serialization.py` — canonical JSON and registry digest
- `test_figures.py` — figure determinism, captions, and registry metadata
- `test_figure_contract.py` — figure registry contract enforcement
- `test_legibility.py` — printed text size and page-fit constraints
- `test_manuscript_bindings.py` — prose and claim bindings against executed values
- `test_formalism_definitions.py` — formalism block parsing and numbering
- `test_formalism_syntax.py` — formalism syntax validation and error paths
- `test_claim_ledger.py` — claim ledger registration and digest binding
- `test_references.py` — bibliography key citation both directions
- `test_publication_metadata.py` — publication metadata across config and package
- `test_scripts_cli.py` — every read-only script passes on good input
- `test_standalone_contract.py` — the package works without sibling repos
- `test_version_sync.py` — version markers across package, manuscript, and figures
- `test_witness_surfaces.py` — witness-layer contracts and envelope format
- `test_no_mocks.py` — lexical ban on mocks, stand-in names, path hardcodes, and import-path insertion
- `test_docs_recipes.py` — documentation recipes produce expected output

## Invariants

- No mocks. Use real records, temporary output roots, and planted-bad registries.
- Keep project coverage at or above the `90` floor in `pyproject.toml`.
- Import figure builders from `black_line.figures`, not from `scripts/`.
- Environment isolation may use `monkeypatch.setenv` / `delenv` only.

## Validation

- `uv run pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing`
