# Black Line

Black Line is a positive operating discipline for concise, inspectable, revisable
research, engineering, and writing. It asks how to make allowed work easier for
another person to inspect and continue after Red Line has answered what must be
refused.

The package contains a versioned practice registry and `evaluate_work`, which
returns `ALIGNED`, `NEEDS_EVIDENCE`, `NEEDS_REWORK`, or `OUTSIDE_SCOPE` from
self-declared tags and evidence. It is a method instrument, not a safety score,
accreditation, or permission mechanism.

Black Line is standalone, and this repository is the whole instrument — see
[`STANDALONE.md`](STANDALONE.md). Its relationship to the other works of the
line set is stated in
[`docs/manuscript/01b_line_set_relationship.md`](docs/manuscript/01b_line_set_relationship.md)
and documented once for the whole set in the companion `line_set` work,
<https://github.com/docxology/line_set>. The other three are
<https://github.com/docxology/red_line>,
<https://github.com/docxology/golden_line>, and
<https://github.com/docxology/white_line>. Those are orientation links: no
companion registry or manuscript is copied here, and nothing in this package
imports, installs, or consults a sibling line project.

## Quick start

```bash
uv run python scripts/build_figures.py   # output/ is ignored; five gates read the mirror
uv run pytest tests/ --cov=src --cov-branch --cov-report=term-missing
uv run python scripts/check_registry.py
uv run python scripts/check_figures.py
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

Every tool named there is declared in the `dev` extra of `pyproject.toml` and
pinned in `uv.lock`; the figure build additionally needs `rsvg-convert` from
librsvg, which is a system package rather than a Python one.

`output/` is disposable and git-ignored, so a fresh checkout has no figure
bundle. Five gates measure the shipped mirror rather than a temporary one — the
rendered-legibility floor, the rasterized-pixel check, the cover embed, and the
two `check_figures.py` CLI checks. Building first is a convenience, not a
precondition: `tests/conftest.py` rebuilds the mirror with this project's own
deterministic builder when it is absent, so the suite is green from a clean
checkout in either order. Without `rsvg-convert` those five gates skip with a
named reason, after asserting the mirror really is absent, rather than failing
for want of an artifact the checkout cannot build.

## Minimal API use

```python
from black_line import WorkAttempt, evaluate_work

assessment = evaluate_work(
    WorkAttempt(
        "Compare two methods for the stated research question",
        tags=frozenset({"research", "analysis"}),
        evidence=frozenset({"question", "scope", "source", "claim"}),
    ),
    as_of="2026-07-18",
    max_evidence_age_days=30,
)
print(assessment.status, assessment.registry_digest)
```

The status is a declaration-coverage prompt, not a truth, safety, or permission
claim. The assessment digest pins the practice registry used for the decision;
serialize the full record with `canonical_assessment(assessment)` when archiving
a review.

## Witness surfaces and the report envelope

`evaluate_with_surfaces` returns the identical assessment plus one typed
`EvidenceSurfaces` per finding — the practice's present, missing, and stale
required labels as co-present data. The status word is a projection of those
surfaces; the surfaces keep what it compresses, so a fully covered practice, a
half-covered one, and an untouched one stay distinguishable under the same
overall status. `assessment_envelope` wraps an assessment in the
cross-instrument report envelope (`line.report-envelope/1.0`): a digest
pointer to the complete canonical assessment plus the instrument's stated
non-claims, for archiving one line's complete report beside reports from the
sibling instruments without ranking, merging, or reinterpreting any of them.
Worked recipes for both live in `docs/usage.md`.

## Analytics

`black_line.analytics` provides pure, deterministic derived views over the
same frozen types: `coverage_matrix` (tag reach and declaration burden — on
the live registry `research` reaches 8 practices / 16 required labels while
`data` reaches 1 / 2, across 27 applicable tag-practice cells of 55),
`staleness_profile` (freshness-window sweeps through the real evaluator),
`summarize_assessments` (batch status and open-finding family counts),
`refresh_horizon` (dated evidence labels nearest to going stale under a pinned
review date), and `declaration_status_path` / `no_status_regression` /
`status_rank` for status-transition sweeps. Every sweep calls the real
`evaluate_work`, never a reimplementation, and all views describe declaration
coverage — never quality, safety, or permission. Worked recipes live in
`docs/usage.md`.

## Figures

Builders live in `src/black_line/figures/`; `scripts/build_figures.py` is a
thin CLI that writes 15 deterministic manuscript figures plus cover art,
including the analytics-derived tag-practice coverage heatmap, the executed
evidence-decay strips that pin the strict `age > window` staleness rule, the
refresh queue derived from `refresh_horizon`, the seeded permutation lattice
that turns conditional monotonicity from one trace into a sweep, the batch panel
that counts which wires a pinned battery of attempts leaves open, the intake
plate that runs Stage 1 over nine malformed declarations, the detection
matrix that runs the whole invariants battery over eight registries — the
shipped one and one planted defect per check — and the surfaces panel that
draws one `evaluate_with_surfaces` call's typed present/missing/stale surfaces
beside the statuses projected from them. Each figure is
embedded in the manuscript and carries an `alt`, an `interpretive_claim`, and
an `epistemic_boundary` in `figure_registry.json`; `validate_generated_figures`
compares all of those fields against the builders' declared specs, and the
embed gate requires the image and its caption to reach the manuscript.

In-figure text carries a rendered-size floor. `black_line.figures.legibility`
derives the point size each label prints at from the canvas, the declared embed
width, and the page geometry in `docs/manuscript/config.yaml`, and
`tests/test_legibility.py` fails any figure whose smallest label falls below
6pt.

## Agent skill

`.agents/skills/black-line/SKILL.md` is the project-scoped skill descriptor:
the instrument boundary (what a status is and is never), copy-pasteable
commands, an executed `WorkAttempt -> evaluate_work` worked example, the
analytics surface, gates, and gotchas.

The manuscript's scholarship map distinguishes computational reproducibility
from independent replication, treats openness as a socio-technical practice, and
keeps craft and tacit knowledge outside the evaluator's authority. Its formalism
section carries no hand-written numbers: definitions and propositions are
labelled fenced blocks, the renderer numbers them in document order, and every
cross-reference resolves from the label. The deterministic
figure builder also creates the title-page cover art from the same protocol
semantics, so the visual argument is versioned with the method.

## Rendering

The typeset PDF and HTML are the one thing this repository cannot produce by
itself. Rendering belongs to a separate publication engine,
<https://github.com/docxology/template>, cloned wherever you like — a declared
external dependency, not a copied engine and not a hidden one. Link this
repository into that checkout under a qualified project name and render it by
that name; the path-independent commands are in
[`docs/development.md`](docs/development.md). Everything above — the package,
the tests and their coverage floor, the registry battery, and the deterministic
figures — runs without it.

See [AGENTS.md](AGENTS.md) for the working contract.
