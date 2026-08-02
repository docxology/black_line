# `black_line.figures` — deterministic figure builders

Every figure is built from the live package, not from hard-coded numbers. Two
builds produce byte-identical artifacts.

## Modules

- `__init__.py` — re-exports `build_figures`, `validate_generated_figures`, and `FigureSpec`
- `svg.py` — SVG primitives: canvas, text, rect, line, circle, escape
- `output.py` — `build_figures()` orchestrator, rasterization, and figure registry
- `validate.py` — `validate_generated_figures()` — fail-closed validation
- `cover.py` — cover art SVG
- `specs.py` — `FigureSpec` dataclass and common dimensions
- `legibility.py` — printed text size and page-fit constraint checks
- `scenarios.py` — scenario definitions for example/test-driven figure data
- `protocol_schematics.py` — operating loop, practice wires, review path schematics
- `registry_schematics.py` — registry overview, intake flow, status path
- `batch_figures.py` — batch summary figure
- `analytics_figures.py` — coverage heatmap, staleness timeline
- `horizon_figures.py` — refresh horizon, claim layers
- `intake_figures.py` — intake flow and normalization figures
- `invariant_figures.py` — invariant battery and surface diagrams
- `surface_figures.py` — witness surface and envelope diagrams

## Invariants

- Every figure draws from the live package — never from hand-typed constants
- `svg.text()` raises below `MIN_TEXT_SIZE` and `svg_document()` refuses a wider-than-allowed canvas
- Two builds of the same code produce bit-identical SVGs, PNGs, and registry
