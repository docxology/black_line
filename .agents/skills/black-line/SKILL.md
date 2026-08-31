---
name: black-line
description: Operate the Black Line instrument — a versioned 11-practice registry plus evaluate_work, mapping self-declared tags and evidence to ALIGNED / NEEDS_EVIDENCE / NEEDS_REWORK / OUTSIDE_SCOPE, with read-only analytics over coverage, staleness, and status transitions. A method instrument, never a safety score or permission mechanism. USE WHEN black line check, evaluate a work attempt, declaration coverage, evidence freshness, practice registry, tag burden, staleness sweep, assessment digest, line-set method instrument.
---

# black-line

Project-scoped skill for the Black Line instrument. It ships inside the Black
Line repository (<https://github.com/docxology/black_line>) at
`.agents/skills/black-line/`, so every path below is relative to that
repository's root wherever it is checked out. Load this when working inside the
project. Version authority is `docs/manuscript/config.yaml`; it is deliberately not
restated here.

## What this instrument IS

A positive operating discipline made mechanically inspectable: a versioned
registry of 11 practices (6 craft families, 5-tag reviewed vocabulary:
analysis, data, engineering, research, writing) and a staged evaluator,
`evaluate_work`, that scores a self-declared `WorkAttempt` for declaration
coverage. A status describes which required evidence labels were declared as
fresh under a pinned review date — nothing more. Every assessment carries the
SHA-256 registry digest so the method version behind a review is recoverable.

## What it is NOT (hard boundary — never soften)

- NOT a safety score, accreditation, moral authority, or permission mechanism.
- `ALIGNED` never means a source is real, a test passed, or a claim is true —
  only that required labels were declared fresh.
- `OUTSIDE_SCOPE` is a coverage statement, never an approval.
- A Black Line status never licenses anything Red Line would refuse.
- Do not add prose, API surface, or figure text implying any of the above.

## Quick start (copy-pasteable from the project root)

```bash
uv run python scripts/build_figures.py        # 15 figures + cover + figure_registry.json (needs rsvg-convert)
.venv/bin/python -m pytest -q                 # full suite must be green; five gates read the built mirror
uv run python scripts/check_registry.py       # structural invariants + digest; non-zero exit on failure
uv run python scripts/check_figures.py        # fail if the generated registry drifts from the live contract
```

`output/` is git-ignored, so a fresh checkout has no mirror for the two
legibility gates, the cover-embed gate, or the two `check_figures.py` CLI
gates. `tests/conftest.py` rebuilds it from this project's own builder, so
either order is green; without `rsvg-convert` those five skip with a named
reason instead of failing. None of these scripts takes an option or an operand;
each exits non-zero on any argument rather than ignoring it.

## Worked example (executed; deterministic)

Undated labels in `evidence` never age. Route labels that should age through
`dated_evidence` only — an undated duplicate silently masks staleness.

```bash
.venv/bin/python -c "
from black_line import EvidenceItem, WorkAttempt, evaluate_work
attempt = WorkAttempt(
    'Trace the dataset behind the headline comparison figure',
    tags=frozenset({'data'}),
    dated_evidence=(
        EvidenceItem('data_origin', '2026-06-01'),
        EvidenceItem('transform_log', '2026-07-20'),
    ),
)
for window in (60, 30):
    a = evaluate_work(attempt, as_of='2026-07-22', max_evidence_age_days=window)
    print('window', window, '->', a.status.value)
    for f in a.findings:
        print('  ', f.practice_id, f.status.value, '|', '; '.join(f.reasons))
"
```

Output (verbatim):

```text
window 60 -> ALIGNED
   data-provenance ALIGNED | required evidence is present: data_origin, transform_log
window 30 -> NEEDS_EVIDENCE
   data-provenance NEEDS_EVIDENCE | required evidence is missing: data_origin; evidence already present: transform_log; stale evidence needs refresh: data_origin
```

`data_origin` is 51 days old at the 2026-07-22 review: at most the window is
fresh, `age > window` is stale (strict inequality — age 51 flips only under a
window of 50 or less). A stale label is a refresh request (`NEEDS_EVIDENCE`),
not missing work (`NEEDS_REWORK`). `assessment.registry_digest` pins the
registry content; `canonical_assessment(assessment)` gives byte-stable JSON
for archiving. Statuses: `ALIGNED` (all required labels fresh),
`NEEDS_EVIDENCE` (no usable declaration, or only stale gaps), `NEEDS_REWORK`
(some required labels missing; also blocking intake defects — fail-closed),
`OUTSIDE_SCOPE` (no practice's tags intersect; overall status only).

## Analytics (`black_line.analytics` — pure, read-only, deterministic)

Derived views over the frozen types; sweeps call the real evaluator, never a
reimplementation. They describe declaration coverage — never quality, safety,
or permission.

- `coverage_matrix()` → per-tag `TagCoverage` (practice reach, required-label
  burden). Live registry: `research` reaches 8 practices / 16 labels,
  `data` reaches 1 / 2; 27 of 55 tag-practice cells are applicable, so tag
  choice moves the declaration burden 8-fold.
- `staleness_profile(attempt, windows, as_of=...)` → `StalenessPoint` per
  window through real `evaluate_work` calls (the worked attempt above yields
  `NEEDS_EVIDENCE` at window 30 and `ALIGNED` at windows 51 and 60).
- `declaration_status_path(description, tags, labels)` → status after each
  incremental label. For the attempt above the path is
  `NEEDS_EVIDENCE → NEEDS_REWORK → ALIGNED`: the empty→non-empty step is the
  one intentional regression (the conditional-monotonicity boundary of
  `prop:fresh-monotonicity`), so `no_status_regression(path)` is `False` for the full path and
  `True` from the first non-empty declaration onward.
- `summarize_assessments(batch)` → `AssessmentSummary` with status counts and
  open-finding craft-family counts.
- `refresh_horizon(attempt, practices=..., as_of=..., max_evidence_age_days=...)`
  → dated evidence labels still fresh, sorted by ascending days until stale,
  each naming the practices requiring it. Three classes are omitted and named
  by `refresh_horizon_omissions`: undated, already stale, and not required by
  the supplied registry.
- `status_rank`: `NEEDS_REWORK` 0 < `NEEDS_EVIDENCE` 1 < `ALIGNED` 2.
  `OUTSIDE_SCOPE` deliberately raises `ValueError` — coverage statements are
  not rungs on the declaration ladder.

## Witness surfaces and the report envelope

```python
from black_line import evaluate_with_surfaces
from black_line.envelope import (
    assessment_envelope,
    canonical_envelope,
    envelope_matches_assessment,
)

assessment, surfaces = evaluate_with_surfaces(attempt, as_of="2026-07-01")
envelope = assessment_envelope(assessment, subject_id="your reference for the attempt")
```

`evaluate_with_surfaces` returns typed `EvidenceSurfaces` (present / missing /
stale, in declared evidence order) beside a byte-identical assessment — the
status is a projection of the surfaces, and the surfaces keep what it
compresses. `assessment_envelope` exports the `line.report-envelope/1.0`
record pointing at `canonical_assessment` by SHA-256; `native_status` is one
status word, never cross-line comparable.

## Gates

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest tests/ --cov=src --cov-branch --cov-report=term-missing   # fail_under 90, branch coverage
# After build_figures.py:
#   uv run python scripts/check_figures.py
# Rendering is an external toolchain (https://github.com/docxology/template),
# cloned anywhere; link this repo into its projects/ and render by the
# qualified name that link produced. See docs/development.md.
```

## Gotchas

- **No mocks, ever.** Tests use real records, `tmp_path`, and
  `dataclasses.replace` planted-bad registries (every invariant is shown to
  fire on a bad registry).
- **Version authority** is `docs/manuscript/config.yaml`; `pyproject.toml`,
  `src/black_line/version.py`, and the cover art are bound to it by
  `tests/test_version_sync.py` — never restate a version literal.
- **Standalone invariant:** never copy prose, registry entries, or code from
  red/golden/white_line. The four projects are the line "set" (never "suite"),
  each its own repository under `docxology/`, and the set is documented once in
  the companion `line_set` work (<https://github.com/docxology/line_set>).
  Those are orientation links; nothing here imports or depends on them.
- **Figures are inert unless embedded:** any new figure must be generated by
  `black_line.figures.build_figures` (via `scripts/build_figures.py`) AND
  referenced by filename in `docs/manuscript/*.md`, with `interpretive_claim` and
  `epistemic_boundary` in `figure_registry.json` (an embed gate in
  `tests/test_figures.py` enforces this, and `figures/validate.py` compares
  every one of those fields against the shipped registry). The cover is the
  one artifact outside `FIGURE_SPECS`; it is bound instead through
  `docs/manuscript/config.yaml`'s `paper.cover.image`, which `figures/validate.py`
  checks against the registry's `cover` entry, and it is embedded with its
  caption so its description reaches a reader.
- **In-figure text has a rendered floor:** `black_line.figures.legibility`
  derives the smallest legible canvas font from the page geometry in
  `docs/manuscript/config.yaml`; `tests/test_legibility.py` fails any figure whose
  smallest label would print below 6pt. Do not lower a size to fit a layout —
  reflow the layout.
- **Manuscript numbers are bound:** `tests/test_manuscript_bindings.py`
  re-derives numeric prose claims through the public API — change semantics
  and the suite fails; never hand-edit a quoted number.
- **Formalism blocks carry labels, never numbers.** Definitions and
  propositions are fenced Divs (`::: {.definition #def:name title="..."}`);
  the renderer numbers them in document order and `[@def:name]` resolves from
  the label. Never write `Definition 3` in prose —
  `tests/test_formalism_syntax.py` rejects it, along with an unlabelled block,
  a duplicate label, a reference to no block, and any label prefix outside
  `RENDERER_ACCEPTED_PREFIXES` (a `rem:` label fails the external engine's
  pre-render citation check and refuses the combined PDF). Every definition is
  bound to the code by `tests/test_formalism_definitions.py`.
- **Bibliography is closed both ways.** `tests/test_references.py` fails on a
  prose citation with no entry, an entry no prose cites, and an entry without
  an author, title, year, and locator. Verify a source against its publisher or
  DOI before adding it.
- **Claim ledger discipline** (`docs/claims.md`): classify every added
  sentence as computational/structural (bind to a test), methodological (cite
  lineage, no outcome claim), or world/authority (name the external reviewer —
  never let `ALIGNED` imply it).
- `models.py` is a public alias for `model/`; both paths export the same
  symbols. Prefer the package-root imports in new call sites.
