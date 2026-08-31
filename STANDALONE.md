# Black Line standalone guide

Black Line is its own repository. This file states what a separated copy is,
what it can do alone, and what it cannot.

## What a separated copy is

A copy of this repository is the whole instrument: the `black_line` Python
package, its practice registry and evaluator, its tests, its documentation, its
manuscript sources, its references, and its deterministic figure builders. The
package declares no third-party Python dependencies and imports no sibling line
project — [red_line](https://github.com/docxology/red_line),
[golden_line](https://github.com/docxology/golden_line),
[white_line](https://github.com/docxology/white_line), and
[line_set](https://github.com/docxology/line_set) are separate works with
separate repositories, and none of them is installed, imported, or consulted at
runtime. Links to them are orientation, not dependency.

This repository also carries its own `.gitignore`. That matters for a separated
copy: the statement made in `README.md`, `AGENTS.md`, and `docs/` that `output/`
is git-ignored and disposable is true because of a file in this repository, not
because of some larger tree a checkout happens to sit inside.
`tests/test_standalone_contract.py` binds that claim to a real `git check-ignore`
run rather than leaving it as prose.

## What it can do alone

The whole local verification loop in
[`docs/development.md`](docs/development.md) runs from the copy alone, offline:

- the test suite with its branch-coverage floor,
- the `ruff` lint and format gates, from tools this repository declares,
- the registry structural battery (`scripts/check_registry.py`),
- the deterministic figure build (`scripts/build_figures.py`),
- the generated-figure contract gate (`scripts/check_figures.py`).

The only thing outside Python that the figure build needs is `rsvg-convert` from
librsvg (`brew install librsvg`, `apt-get install librsvg2-bin`). It is a hard
requirement of the PNG raster step and fails loudly when absent. The five gates
that read the built mirror skip with a named reason on a machine that has no
rasterizer, after asserting the mirror really is absent, so a missing system
package reports as unrun rather than as a failed legibility floor.

## What it cannot do alone

It cannot produce the typeset PDF or HTML manuscript. Rendering and
rendered-output validation belong to a separate publication engine at
[`docxology/template`](https://github.com/docxology/template), which you clone
wherever you like — see [`docs/development.md`](docs/development.md) for the
path-independent invocation.

That is a declared external dependency. It is not evidence that the evaluator or
the manuscript is unsound, and the absence of a rendered PDF is not a failing
gate — it is an unrun one.

## Purpose

Black Line is a positive operating discipline made mechanically inspectable: a
versioned practice registry and `evaluate_work`, returning `ALIGNED`,
`NEEDS_EVIDENCE`, `NEEDS_REWORK`, or `OUTSIDE_SCOPE` from self-declared tags and
evidence. A status describes declaration coverage and nothing else. It is not a
truth claim, a safety score, an accreditation, a moral authority, or a permission
mechanism, and it never licenses anything Red Line would refuse. Read
`README.md`, `docs/manuscript/05_limits.md`, and `docs/claims.md` before changing the
evaluator.

## Making a copy

Copy or clone the repository whole; there is no extraction step and no helper
from another checkout to run. Do not copy a rendering engine into this tree, and
do not copy prose, registry entries, or code in from a sibling line project.
After copying, check that every cross-work reference still names a repository
rather than a relative path out of this one —
`tests/test_standalone_contract.py` fails on any relative markdown link that
resolves outside this repository's root.

## Validation

Use the canonical local commands in [`docs/development.md`](docs/development.md).
Generated figures must exist before the figure-contract gate; `output/` is
ignored and disposable, and the suite rebuilds it when it can.

The local gates are necessary but not sufficient for publication. Rendered
PDF/HTML outputs must also pass the template engine's validation, which runs in
that engine's checkout and not here.
