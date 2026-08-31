# Development

Use `uv` for the project environment. Run the tests, the gates, and the figure
builder from this repository's own root; nothing in that loop reaches outside
this checkout.

The package has no runtime dependencies beyond the Python standard library. Its
declared development tools — `pytest`, `pytest-cov`, and `ruff` — are in the
`dev` extra of `pyproject.toml` and pinned in `uv.lock`, so the contract below
runs from this repository's declarations rather than from whatever happens to be
on the ambient PATH.

The PNG rasterization step needs one thing that is not a Python package:
`rsvg-convert` from librsvg (`brew install librsvg`, or
`apt-get install librsvg2-bin`). It is a hard requirement of the raster step and
fails loudly when absent. The manuscript declares its denser 0.5-inch page
geometry in `docs/manuscript/config.yaml`; keep that source setting and the generated
artifacts in sync when changing layout.

## Local verification loop

Run the checks in this order after a source or manuscript change:

```bash
uv run python scripts/build_figures.py  # figures plus deterministic cover art
uv run pytest tests/ --cov=src --cov-branch --cov-report=term-missing
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run python scripts/check_registry.py
uv run python scripts/check_figures.py   # fail if the generated registry drifts from the live contract
```

The figure build is listed first because `output/` is git-ignored and five
gates measure the shipped mirror: the cover-embed contract, the two legibility
floors, and the two `check_figures.py` CLI checks. It is a convenience rather
than a precondition — `tests/conftest.py` rebuilds the mirror with this
project's own deterministic builder when it is missing, so a clean checkout is
green in either order. Where `rsvg-convert` is not installed those five gates
skip with a named reason, after asserting the mirror really is absent, instead
of failing for want of an artifact the checkout cannot produce.

Every script here takes no options and no operands and exits non-zero on any
argument, so a typo in one of these lines cannot exit 0.

## Rendering the manuscript (external toolchain)

The typeset PDF and HTML are the one thing this repository cannot produce by
itself. Rendering is done by a separate publication engine,
<https://github.com/docxology/template>, which you clone wherever you like. This
is a declared external dependency: without it the whole local loop above still
runs and the package, tests, registry, and figures are all still real — you
simply have no rendered PDF or HTML. An absent rendered artifact is an unrun
gate, not a failing one.

Nothing below assumes a particular directory layout. Set the two roots to
wherever the two repositories actually live:

```bash
BLACK_LINE_ROOT=$(pwd)                  # this repository, from its root
TEMPLATE_ROOT=${TEMPLATE_ROOT:-$HOME/src/template}

git clone https://github.com/docxology/template.git "${TEMPLATE_ROOT}"   # once

# Make this repository visible to the engine under a qualified project name.
# A direct child of projects/ with src/ and tests/ is discovered by its bare
# directory name, so the qualified name here is simply `black_line`.
ln -sfn "${BLACK_LINE_ROOT}" "${TEMPLATE_ROOT}/projects/black_line"

cd "${TEMPLATE_ROOT}"
uv run python scripts/pipeline/stage_03_render.py --project black_line
uv run python scripts/pipeline/stage_04_validate.py --project black_line
```

If instead you link this repository through the engine's private-projects root,
the qualified name becomes the path under `projects/` that the link produced
(for example `working/black_line`); pass that name to the same commands.

Inspect the generated PDF and web pages as well as their machine-readable
reports. Generated files are outputs of the source-to-artifact chain; fix the
producer or manuscript source rather than hand-editing a rendered file. The
engine's strict publication gates are public-release checks that run in the
engine checkout, not here.
