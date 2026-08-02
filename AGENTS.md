# Black Line project guidance

Black Line is its own repository and a standalone Python package with a
manuscript beside it. Keep the executable method under `src/black_line/`; keep
scripts as thin build or validation entry points; and preserve the instrument
boundary: statuses describe self-declared evidence coverage, never truth,
safety, accreditation, or permission. What a separated copy is, can do, and
cannot do is stated in [`STANDALONE.md`](STANDALONE.md).

## Validation contract

Run from this project root with `uv`. Every tool named here is declared in
`pyproject.toml` under the `dev` extra and pinned in `uv.lock`, so the contract
runs from this repository's own declarations rather than from an ambient PATH:

```bash
uv run python scripts/build_figures.py   # first: output/ is ignored and five gates read it
uv run pytest tests/ --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run python scripts/check_registry.py
uv run python scripts/check_figures.py
```

Building first is a convenience, not a precondition. `output/` is git-ignored,
and five gates measure the shipped mirror rather than a temporary bundle — the
cover-embed contract, the two legibility floors, and the two `check_figures.py`
CLI checks. `tests/conftest.py` rebuilds the mirror with this project's own
deterministic builder when it is missing, so the suite is green from a clean
checkout in either order. On a machine without `rsvg-convert` those five gates
skip with a named reason after asserting the mirror really is absent; they never
fail for want of an artifact the checkout cannot produce.

None of these scripts accepts an option or an operand; each exits non-zero on
any argument, so a mistyped flag fails instead of reading as a pass.

Figure builders live in `src/black_line/figures/`; `scripts/build_figures.py` is
a thin CLI. Analytics helpers (`staleness_profile`, `summarize_assessments`,
`refresh_horizon`) live in `src/black_line/analytics.py`.

`evaluate_work` and `evaluate_with_surfaces` share one staged core in
`src/black_line/evaluator.py`; never add a second scoring path. The typed
`EvidenceSurfaces` are what a finding's status projects from, and the report
envelope (`src/black_line/envelope.py`) points at `canonical_assessment` by
digest without reinterpreting it — the envelope's non-claims travel with it.
The shared witness register across the line set is a separate work by design;
do not build cross-line logic here (see `docs/correspondence.md`).

Rendering the typeset PDF/HTML is the one thing this repository cannot do by
itself. It belongs to a separate publication engine,
<https://github.com/docxology/template>, which you clone wherever you like — a
declared external dependency, not a hidden one. Nothing below assumes a
directory layout; see [`docs/development.md`](docs/development.md) for the
path-independent invocation, and note that the qualified project name passed to
the engine is whatever path under its `projects/` the link produced.

Generated `output/` is disposable and ignored. Regenerate it from the current
source before relying on a PDF, HTML page, figure registry, or report.

Tests use real records, temporary output roots, and planted-bad registries;
do not introduce mocks or weaken the evidence-boundary language.
