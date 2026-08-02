# Deferred work

_Last reviewed: 2026-08-01 (verification window)._

## Completed — 2026-08-01 verification window

- [x] `ruff format --check` regression closed. Two figure modules
      (`src/black_line/figures/protocol_schematics.py`,
      `src/black_line/figures/surface_figures.py`) had shipped unformatted, so
      `ruff format --check src tests scripts` failed the documented validation
      contract while every test passed (`ruff check` does not see layout). Both
      reformatted with the pinned ruff; the figure build stays deterministic
      (two consecutive `build_figures.py` runs byte-identical) and the registry
      digest `a02bff47…` is unchanged.
- [x] The gap that let that slip was that no test ran either ruff gate.
      `tests/test_standalone_contract.py` now fails `ruff check` and
      `ruff format --check` over `src tests scripts` when the shipped code
      drifts, with a positive control proving the format gate can fail. The new
      gate immediately caught its own unformatted test file, then passed after
      formatting. Measured: 340 passed (337 before), 99.95% branch coverage of
      `src/`, both ruff gates clean.

## Completed — 2026-07-29 third window (figure-module coverage)

- [x] Two of the three long-standing uncovered figure-module branches closed
      with real cases (2026-07-29): `legibility.py` now covers the bare
      geometry token (`landscape` beside `key=value` pairs must be skipped,
      not mis-parsed) and `validate.py` covers both cover-block exits (a
      sibling key closing an imageless `cover:` block; deeper-indented
      non-image content staying inside one). Measured: 331 passed, total
      branch coverage 99.61% → 99.95%, `legibility.py` and `validate.py`
      both 100.00%.

## Open — one deliberate remainder

- The one uncovered arc left in `src/` is
  `analytics_figures.py` 273→285: the label-skip branch for a status run
  narrower than 200 canvas px in `evidence_decay_svg`. The builder takes no
  arguments and its pinned executed sweep produces no run that narrow, so
  covering the arc honestly means either a second executed decay scenario
  with a near-boundary window (a shipped-figure change, its own window) or
  an override parameter added purely for coverage. Neither is worth bending
  a shipped plate for; the arc is cosmetic (a skipped label on a
  too-narrow run) and this entry is its record.

## Completed — 2026-07-29 witness surfaces and report envelope

- [x] Scoring refactored into one staged core behind `evaluate_work` and the
      new `evaluate_with_surfaces`; typed `EvidenceSurfaces` (present /
      missing / stale) per finding, with the reasons trail derived from the
      surfaces and proven re-derivable in `tests/test_witness_surfaces.py`.
- [x] Cross-instrument report envelope (`envelope.py`,
      `line.report-envelope/1.0`) with `assessment_digest`,
      `canonical_envelope`, `envelope_matches_assessment`, and transportable
      non-claims. Executed usage recipe bound by `tests/test_docs_recipes.py`.
- [x] `docs/correspondence.md` records the 2026-07-29 "Space Between the
      Lines" review and the adopted/deferred/declined mapping.

## Completed — 2026-07-29 manuscript window (formalism + surfaces panel)

- [x] The manuscript's formal section now defines `EvidenceSurfaces`
      (four fields in declared order, `stale ⊆ missing`), states the
      surfaces-to-finding projection as a proposition (one staged core;
      `evaluate_with_surfaces` byte-identical to `evaluate_work`), and
      defines the report envelope (ten fields, digest pointer, travelling
      non-claims, `native_status` never compared or merged across lines).
      Bound by three new tests in `tests/test_formalism_definitions.py`
      with drifted-body positive controls; both claim tables extended;
      `02_method.md` narrates surfaces-as-state / status-as-projection.
- [x] One new derived plate, `black_surfaces_panel`: a single executed
      `evaluate_with_surfaces` call drawn as typed present/missing/stale
      chips beside the projected statuses and the one overall word, with
      derivation proven through the builder's override argument. Figure
      count sites updated to 15.

## Open — from the 2026-07-29 window, deferred with a stated reason

- The shared witness register the review proposes (co-registration of all
  four instruments' envelopes, cross-line relations, return contracts held
  jointly) is a separate work by design and is deliberately not implemented
  in this repository. Black Line's contribution is the envelope export above.

## Completed — 2026-07-22 expansion window

- [x] Analytics module (`src/black_line/analytics.py`): coverage, staleness,
      batch-summary, and status-transition views, all routed through the real
      evaluator; Proposition 4's conditional monotonicity exercised by seeded
      permutation sweeps with the empty-declaration boundary kept as a
      positive control.
- [x] Two derived figures (tag-practice coverage heatmap, evidence-decay
      strips) embedded in the manuscript; executed worked examples and
      adversarial-declaration attacks in the manuscript with per-claim test
      bindings (`tests/test_manuscript_bindings.py`).
- [x] Version copies bound to `manuscript/config.yaml` through
      `tests/test_version_sync.py` instead of restated literals.
- [x] Project-scoped agent skill descriptor at
      `.agents/skills/black-line/SKILL.md` (instrument boundary, executed
      worked example, analytics surface, gates, gotchas) plus README
      Analytics / Figures / Agent skill sections.

## Completed — 2026-07-26 quality remediation + follow-up

- [x] Figure builders extracted to `src/black_line/figures/`; scripts are thin
      CLIs. Schematic figures split into `registry_schematics.py` and
      `protocol_schematics.py`. Figure-gate logic lives in
      `figures/validate.py`.
- [x] Recipes in `docs/usage.md` for `staleness_profile`,
      `summarize_assessments`, and `refresh_horizon`.
- [x] Read-only `refresh_horizon` analytics view with tests (undated items
      omitted; nearest-to-stale dated evidence sorted ascending).

## Completed — 2026-07-27 legibility, derived figures, ledger derivation

- [x] Rendered-legibility floor for in-figure text
      (`src/black_line/figures/legibility.py`), derived from the page geometry
      rather than restated; measured minimum across the generated plates moved
      from 3.18pt to 6.12pt. `tests/test_legibility.py` rejects a planted
      shrunken font and a canvas widened without its text, and binds the
      assumption under the arithmetic — every shipped PNG rasterizes to
      exactly the SVG canvas the point size is measured against — with a
      rescaled-raster positive control.
- [x] Skill-descriptor and README numeric literals bound
      (`tests/test_version_sync.py`) — this closes the follow-up the
      2026-07-22 entry opened and a later edit dropped without recording.
- [x] `refresh_horizon` consumes its `practices` argument, and
      `refresh_horizon_omissions` names every excluded declaration.
- [x] Three derived figures (`fig:black-refresh-queue`,
      `fig:black-monotonicity-lattice`, `fig:black-batch-summary`) and the
      cover embedded with its caption; `paper.cover.image` bound to the
      registry cover entry. The batch panel is the first figure in the set to
      show more than one work attempt.
- [x] `data/claim_ledger.yaml` re-keyed on the claim and re-derived by
      `tests/test_claim_ledger.py`.
- [x] Executed recipes in `docs/usage.md`, bound by
      `tests/test_docs_recipes.py`.

## Completed — 2026-07-27 adversarial verification pass

- [x] Refresh-queue caption, `<desc>`, manuscript embed, and docstring no
      longer call the omitted set "dated" — one of the three omitted classes
      is undated by construction. Bound by
      `tests/test_manuscript_bindings.py::test_refresh_queue_omission_wording_matches_the_executed_omissions`,
      which checks every reader-facing surface, not just the two that were
      already compared against each other.
- [x] `05_limits.md` tag-minimization contrast restated as sevenfold (7/14 →
      1/2) with the eightfold `research`-vs-`data` spread named separately;
      the fold is re-derived in the binding test.
- [x] `scripts/_cli.py` argument guard: all three CLIs exit non-zero on any
      argument. `tests/test_scripts_cli.py` discovers the roster from disk and
      runs each script as a subprocess on good and garbage input.
- [x] `manuscript/03_practices.md` quotes all eleven registry wires verbatim
      (two had drifted a word each); bound by
      `test_the_practice_list_restates_every_registry_wire_verbatim`.
- [x] Documented verification order corrected in README, AGENTS,
      `docs/development.md`, and the skill descriptor: `build_figures.py`
      before `pytest`, because `output/` is git-ignored and three tests
      measure the shipped mirror.

## Completed — 2026-07-28 standalone-repository pass

- [x] The repository ships its own `.gitignore`. Before this, "`output/` is
      git-ignored" was true only for a checkout sitting inside a larger tree.
      Bound by a real `git check-ignore` run in a throwaway repository, with
      the same probe minus the file as its positive control.
- [x] Zero relative markdown links escape the repository root (was five, three
      of them shipping inside the rendered manuscript). The acknowledgements
      are unchanged; each now names the sibling work and its repository.
- [x] `ruff` declared in the `dev` extra, pinned in `uv.lock`, and configured;
      it had been in the documented contract and in neither file. Bound by a
      test that extracts every tool the contract blocks invoke.
- [x] Rendering documented path-independently against
      <https://github.com/docxology/template> as a declared external
      dependency, with what the project can do without it stated plainly.
- [x] A missing `rsvg-convert` no longer errors the whole suite. The five
      mirror-reading gates skip with a named reason after asserting the mirror
      is absent and that nothing could have built it.
- [x] `STANDALONE.md` added; skill descriptor and folder contracts no longer
      locate themselves at a monorepo path.

## Completed — 2026-07-28 formalism numbering, craft scholarship, derived plates

- [x] All 28 formalism blocks converted to labelled fenced Divs; the renderer
      numbers them and every cross-reference resolves from a label. No number is
      written in the manuscript source. `tests/test_formalism_syntax.py` refuses
      an unlabelled block, a duplicate or mislabelled label, an unclosed Div, a
      reference to no block, a hand-written `Definition N`, and a label prefix
      the external engine's citation check would reject.
- [x] Every definition bound to the code by
      `tests/test_formalism_definitions.py`; two definitions added from code the
      formalism had not described (the review-configuration pre-stage and the
      fail-closed registry check), plus the matching proposition.
- [x] Two derived figures — the executed intake battery and the invariants
      detection matrix — both computed at build time, both with a narrowed-input
      override proving they follow their data.
- [x] Craft and technē scholarship built on the existing Polanyi thread
      (Ryle, Aristotle, Dreyfus and Dreyfus, Schön, Sennett, Collins), and the
      replication-versus-reproducibility distinction with its terminology
      history and empirical backdrop. `tests/test_references.py` closes prose
      citations against the bibliography in both directions.

## Open — deferred with a stated reason

- The monotonicity lattice samples twelve seeded declaration orders; the
  property is not proven for all 16! orders and the figure says so. A proof
  would need a different argument, not a larger sample.
- The legibility floor is measured against the PDF's declared embed width.
  The HTML edition scales figures to the viewport, so its rendered size is not
  bound by anything here; nothing currently measures it.
- The rendered PDF is untagged, so no figure's registered `alt` string reaches
  a PDF accessibility tree — the caption is the only description that reaches
  a reader. Tagging is a renderer concern in the external template engine,
  not a change this project can make alone.

- The two new plates are pinned batteries, not sweeps. The intake plate covers
  every Stage 1 branch the evaluator is written to survive, but a
  user-defined iterable with a hostile ``__iter__`` is outside what the
  evaluator claims to handle and is not exercised. The detection matrix plants
  one defect per check; it does not enumerate the defect space.

## Open — intentionally outside the current instrument boundary

These items are not represented as hidden evaluator features:

- Add optional adapters for independently verifiable source and test records;
  keep the current lexical evaluator as the baseline rather than treating an
  adapter as proof of truth.
- Define a signed or externally anchored assessment envelope if a future public
  release needs tamper evidence. The current registry digest only detects
  disagreement with a known digest.
- Add a maintained citation/release workflow now that the project is published
  as its own repository. Nothing in this repository currently mints a DOI or a
  release record, and no test asserts one; the local gates say nothing about
  publication.

Each open item requires a new evidence contract, tests that can fail, and
manuscript language that does not overclaim what the adapter establishes.
