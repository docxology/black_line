# Development

## Set up the project

Install [uv](https://docs.astral.sh/uv/) and run commands from the project root
unless the render recipe changes directories. Black Line uses Python 3.11
or newer and the standard library. The locked development environment adds
pytest, pytest-cov, and Ruff.

Install librsvg's `rsvg-convert` and put it on `PATH`. On Debian or Ubuntu,
install `librsvg2-bin`. On macOS, install `librsvg` through Homebrew.

```bash
uv sync --locked
```

See the [usage guide](usage.md) for a reading with a pinned review date,
dated evidence and a freshness window. The guide also covers archiving and
replaying an evaluation and matching report envelopes.

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

Every script here takes no options and no operands and exits with usage status 2
on any argument, so a typo in one of these lines cannot exit 0.

CLI tests run writing scripts against temporary copies of the real source and
manuscript inputs, including a separate formalism-ledger output directory.
Git ignore probes disable host-wide excludes per command, so a contributor's
global ignore rules cannot supply the missing-`.gitignore` negative control.

## Render and validate the manuscript

Black Line cannot produce the typeset publication without the external
template renderer. Install Pandoc, a matching
[pandoc-crossref](https://github.com/lierdakil/pandoc-crossref/releases) filter,
and XeLaTeX with the [pinned template prerequisites](https://github.com/docxology/template/blob/87704feae0a4490ef7dad9c931d268e8c30273c2/README.md#L565-L574).
Build from a clean Black Line checkout in a directory named `black_line`.

```bash
BLACK_LINE_ROOT="$(pwd)"
TEMPLATE_ROOT="$(mktemp -d)/template"
git clone https://github.com/docxology/template.git "$TEMPLATE_ROOT"
git -C "$TEMPLATE_ROOT" checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2

uv sync --locked
uv run python scripts/build_figures.py

mkdir -p "$TEMPLATE_ROOT/projects/working"
ln -s "$BLACK_LINE_ROOT" "$TEMPLATE_ROOT/projects/working/black_line"

(
  cd "$TEMPLATE_ROOT" &&
  uv sync --locked --no-dev --python 3.14 &&
  .venv/bin/python scripts/pipeline/stage_03_render.py --project working/black_line &&
  .venv/bin/python scripts/pipeline/stage_04_validate.py --project working/black_line
)
```

The template resolves `working/black_line` to the linked checkout and
discovers [`docs/manuscript/`](manuscript/README.md). Its
[configuration](manuscript/config.yaml) selects the cover, page geometry,
figure sizing, and output formats. Inspect these generated files in the Black
Line checkout.

- `output/pdf/black_line_combined.pdf`
- `output/web/index.html`
- `output/epub/black_line_combined.epub`
- `output/reports/validation_report.md`

Check the section order, bibliography, figures, and formalism links.
If one fails, update the producer or manuscript source and rebuild.
