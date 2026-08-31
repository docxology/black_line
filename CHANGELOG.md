# Changelog

## Unreleased

### 2026-08-01 (verification window)

- **The format gate regression is closed and now bound.** Two figure modules
  (`src/black_line/figures/protocol_schematics.py` and
  `src/black_line/figures/surface_figures.py`) had shipped unformatted, so
  `uv run ruff format --check src tests scripts` — a stated line of the
  validation contract in README, AGENTS, and the development doc — failed
  while `ruff check` and every test stayed green, because `ruff check` does
  not see layout. Both files are reformatted with the pinned ruff; the figure
  build remains deterministic (two consecutive `build_figures.py` runs
  byte-identical across all generated artifacts) and the registry digest
  `a02bff47a767b545…` is unchanged.
- No test had been running either ruff gate, which is how the regression went
  unmeasured. `tests/test_standalone_contract.py` now fails
  `ruff check src tests scripts` and `ruff format --check src tests scripts`
  when the shipped code drifts, and carries a positive control proving the
  format gate can fail; the new gate immediately caught its own unformatted
  test file, then passed after formatting. Measured: 340 collected and passing
  tests (337 before), 99.95% branch coverage of `src/`, `ruff check` clean and
  `ruff format --check` clean under the pinned config.

## 0.4.0 — 2026-07-29

The eleven dated windows below, accumulated as Unreleased since 0.3.0, are
released together as 0.4.0: witness surfaces and the report envelope; the
manuscript window (formalism plus the surfaces panel); the verification
follow-up that re-verified that window independently; formalism numbering,
craft scholarship, and two derived plates; the standalone-repository pass;
the adversarial verification pass; the legibility floor with three derived
figures and the ledger derivation; the operability window (agent skill
descriptor plus doc reconciliation); the manuscript expansion (executed
examples plus adversarial declarations); the analytics and coverage
expansion; and the audit improvement pass.

### 2026-07-29 (witness surfaces and the report envelope)

Prompted by "The Space Between the Lines" (an external review,
2026-07-29), a design review of the line set arguing that each instrument's
selected status is a safe projection that should not become the whole state,
and that each line should export one common report envelope a shared witness
layer could co-register without aggregation. The shared register itself is a
separate work and is deliberately **not** built here; this window ships the
per-instrument pieces that are Black Line's to ship.

- **Typed evidence surfaces.** The evaluator's scoring stage was refactored
  into one staged core (`_evaluate`) behind two public forms: the unchanged
  `evaluate_work`, and `evaluate_with_surfaces`, which additionally returns
  one frozen `EvidenceSurfaces` per finding — the practice's present,
  missing, and stale required labels as typed co-present data. Previously
  those three surfaces existed only inside the finding's reason strings, so
  strong support and strong resistance on one practice were machine-readable
  only as prose. The finding's status and reasons are now *derived from* the
  surfaces, and `tests/test_witness_surfaces.py` proves (a) byte-identical
  assessments from both public forms across a battery reaching every
  `AssessmentStatus`, and (b) that every reasons trail is re-derivable from
  its surfaces, so the prose and the data cannot drift. `PracticeFinding` and
  the manuscript's formal triple are unchanged.
- **The common report envelope.** New `envelope.py` exports
  `assessment_envelope` under the cross-instrument schema string
  `line.report-envelope/1.0`: review date, registry digest, the native
  status word, a SHA-256 `report_ref` to the complete `canonical_assessment`
  output (new `serialization.assessment_digest`), caller-supplied source
  snapshot references, and the instrument's transportable non-claims
  (`SCOPE_AND_NONCLAIMS` — coverage never truth, ALIGNED never permission).
  The envelope points at the native record and never reinterprets it;
  `envelope_matches_assessment` is the read-back check for an archived pair,
  and `canonical_envelope` is its stable serialization. Sibling lines export
  the same shape by publishing the same schema string, never by importing one
  another.
- **Docs.** `docs/usage.md` gains an executed recipe for both surfaces and
  envelope (bound by `tests/test_docs_recipes.py`); `docs/architecture.md`
  describes the staged core, the surfaces-to-finding projection, and the
  envelope; README gains the "Witness surfaces and the report envelope"
  section. `docs/correspondence.md` records the review and maps what was
  adopted, deferred, and declined.
- Measured gate: 325 collected and passing tests (311 before: 13 new witness
  tests plus one new executed recipe), 99.58% branch coverage of `src/`
  (three pre-existing figure-module misses; every new and refactored module
  at 100%), `ruff check src tests scripts` clean and `ruff format --check`
  clean under the pinned config, `check_registry.py` digest unchanged, and
  `check_figures.py` passing on the unchanged 14-figure-plus-cover contract.
  Package version unchanged at 0.3.0: additions accumulate in Unreleased
  until the next release window. A manuscript formalism definition for the
  surfaces and envelope is deferred to the next manuscript window (see TODO).

### 2026-07-29 follow-up — the manuscript window (formalism + surfaces panel)

The deferred manuscript work from the entry above, closed the same day.

- **Formalism.** `docs/manuscript/03b_formalism.md` gains a "Surfaces, projection,
  and the report envelope" section: a definition of `EvidenceSurfaces` (the
  four fields in order, `stale ⊆ missing`, all three tuples in the practice's
  declared evidence order), a proposition that the finding is a projection of
  its surfaces — status and ordered reasons derived from (surfaces,
  evidence-declared), with `evaluate_with_surfaces` byte-identical to
  `evaluate_work` under canonical serialization — and a definition of the
  report envelope (the ten `AssessmentEnvelope` fields, the SHA-256
  `report_ref` pointer to `canonical_assessment`, the travelling non-claims,
  and the explicit rule that `native_status` is this line's own word, never
  to be compared, ranked, averaged, or merged across lines). Both claim
  tables gained matching rows, and `docs/manuscript/02_method.md` narrates
  surfaces-as-state / status-as-projection beside the staged outline. Three
  new binding tests in `tests/test_formalism_definitions.py` re-derive the
  field lists, the containment and order invariants, and the equivalence from
  the running package, with drifted-body positive controls. Existing
  definitions are untouched.
- **One derived plate.** `black_surfaces_panel` (`fig:black-surfaces-panel`,
  builder `src/black_line/figures/surface_figures.py`, pinned scenario in
  `figures/scenarios.py`): one real `evaluate_with_surfaces` call at review
  date 2026-07-01 under a 30-day window matches 7 practices whose 14 required
  labels split into 5 present (filled), 9 missing (hollow), and 3 merely
  stale (amber dashed refresh chips), beside each projected status and the
  single overall word — NEEDS_EVIDENCE and NEEDS_REWORK each cover 2 distinct
  surface shapes, which is the review's compression point drawn rather than
  asserted. Embedded in the formalism section with its registry caption;
  `tests/test_figures.py::test_the_surfaces_panel_follows_the_executed_call`
  proves derivation through the builder's own override argument. Figure count
  sites updated to 15 (README, skill descriptor, `EXPECTED_FIGURE_COUNT`,
  `data/claim_ledger.yaml` `generated-figure-count`).
- Measured gate: 329 collected and passing tests (325 before: three new
  formalism-definition bindings plus the surfaces-panel figure test), 99.61%
  branch coverage of `src/` (the same three pre-existing figure-module
  misses; `surface_figures.py` and every other touched module at 100%),
  `ruff check src tests scripts` and `ruff format --check src tests scripts`
  both clean, `check_registry.py` digest unchanged
  (`a02bff47a767b545…`), `check_figures.py` passing on the 15-figure-plus-cover
  contract, and two consecutive `build_figures.py` runs byte-identical across
  all 33 generated files. Version unchanged at 0.3.0.

### 2026-07-29 verification follow-up — the window independently re-verified

The manuscript window above shipped without an independent adversarial pass;
this entry records one, run against this tree. Every measured number in the
two entries above reproduced exactly: 329 collected and passing tests, 99.61%
branch coverage (1671 statements, 382 branches, the same three pre-existing
figure-module misses), both ruff gates clean, registry digest
`a02bff47a767b545…` unchanged, the 15-figure-plus-cover contract passing, and
two consecutive figure builds byte-identical across all 33 artifacts. Each of
the three new formalism binding tests was then proven to bite on the real
manuscript, not only on its in-suite control: a field dropped from the
`def:evidence-surfaces` tuple, "byte-identical" weakened in
`prop:surfaces-projection`, and two fields swapped in `def:report-envelope`
each failed exactly its named test before byte-identical restoration
(`shasum` compared). The surfaces panel's caption numbers were re-derived
through a fresh `surfaces_result()` call — 7 practices, 14 required labels
splitting 5 present / 9 missing / 3 stale, distinct count-signature shapes
per word ALIGNED 1, NEEDS_EVIDENCE 2, NEEDS_REWORK 2, overall NEEDS_REWORK —
and checked chip by chip against the rendered PNG. One clarification worth
recording: "distinct surface shapes" in the caption and footer means distinct
(present, missing, stale) count signatures, the builder's own reading;
counted over label sets instead, NEEDS_REWORK covers four distinct shapes,
so the stated compression is the conservative reading.

### 2026-07-28 (formalism numbering, craft scholarship, two derived plates)

- **Every formalism block is now auto-numbered from a label.** The formalism
  section carried ten hand-numbered Propositions and thirteen unnumbered
  bold-run "Definition" paragraphs, and prose referred to them by number
  ("Proposition 6 pins this boundary"). Inserting a block renumbered everything
  after it while every reference kept pointing at the old statement, and nothing
  could detect it. All twenty-eight blocks are now fenced Divs with `def:` /
  `prop:` labels, every cross-reference is a `[@label]` citation the renderer
  resolves, and no number is written in the manuscript source at all.
  `tests/test_formalism_syntax.py` (14 tests) refuses an unlabelled block, a
  mislabelled or duplicated label, an unclosed Div, a reference to no block, and
  any hand-written `Definition N` outside a fenced code block. Each checker was
  run against a violation planted in the real manuscript before being trusted.
  Rendered: Definitions 1–14, Propositions 1–13, zero `??`, zero undefined
  citations.
- **The renderer's accepted label prefixes are now a local constraint.** A
  `.remark` block labelled `rem:global-local` rendered fine locally and failed
  the combined PDF with "undefined citation key" — the external engine's
  pre-render check treats an unknown prefix as a missing bibliography entry. The
  block became a proposition, and `RENDERER_ACCEPTED_PREFIXES` in
  `tests/test_formalism_syntax.py` now fails that class locally, in a repository
  that cannot run the engine.
- **Every Definition is bound to the code it describes.** The Propositions had
  named tests; the Definitions did not, so a renamed field, a reordered branch,
  or an added enum member would have contradicted the paper with every gate
  green. `tests/test_formalism_definitions.py` (16 tests) re-derives all
  fourteen definitions from the running package. Verified by planting five
  defects in `src/` — the `METHOD` kind default, the tag vocabulary, the
  aggregation branch order, the strict staleness comparison, and the ordering of
  the missing-label reasons trail — and confirming the matching test fails each
  time. Two definitions are new because the code had them and the formalism did
  not: the review-configuration pre-stage, and the fail-closed registry check.
- **Two new derived figures**, both computed from the live evaluator at build
  time. `fig:black-intake-notes` runs Stage 1 over nine deliberately malformed
  declarations and draws the status, finding count, and every intake note that
  comes back — the first plate covering intake normalization at all.
  `fig:black-invariant-detection` runs the whole invariants battery over eight
  registries (the shipped one and one planted defect per check) and draws the
  8 × 7 outcome matrix, including the two plants that trip a check they were not
  aimed at. Both carry a letter channel as well as a colour fill, both pass the
  6pt rendered-legibility floor, and both are proved to follow their data by a
  narrowed-battery override rather than a shape-only assertion. Figures: **12 →
  14** plus cover.
- **Scholarship: craft and technē, and replication versus reproducibility.** The
  Polanyi subsection stood alone; it is now the entry point to Ryle's knowing
  how, Aristotle's *technē*, the Dreyfus skill model, Schön's reflection in
  action, Sennett's craftsmanship, and Collins's partition of tacit knowledge
  into relational, somatic, and collective — which is where transfer into this
  instrument stops, because a label can only reach the relational kind. The
  reproducibility subsection now names the terminology history (Claerbout and
  Karrenbach's coinage, Plesser's account of how the two words got swapped) and
  the replication evidence the clean-rerun wire does *not* address (the Open
  Science Collaboration's 100 replications, Baker's survey of 1,576
  researchers). Ten new bibliography entries, each verified against the
  publisher or DOI before it was added. `tests/test_references.py` closes the
  citation set against the bibliography in both directions and requires an
  author, title, year, and locator per entry; it found two pre-existing entries
  with no DOI, URL, or ISBN.
- **Editorial pass.** The method section no longer re-states the whole staged
  evaluator that the formalism section now owns; the worked-examples section no
  longer explains the empty-declaration boundary three times; the abstract and
  conclusion are tightened, and the conclusion's promotional paragraph is gone.
  The author's own choices are stated in the first person where they are choices
  rather than facts about the code.

### 2026-07-28 (standalone-repository pass)

Black Line is now published as its own repository. A fresh-clone audit found
several statements the project makes about itself that were true only because a
checkout happened to sit inside a larger private tree. Each is closed here and
bound by a test that is shown to fail when the property is removed
(`tests/test_standalone_contract.py`, 12 tests).

- **The repository inherited its ignore rules instead of shipping them.** No
  `.gitignore` was tracked, so in a clone `output/`, `__pycache__/`,
  `*.egg-info/`, `.coverage`, `htmlcov/`, and `coverage_project.json` were
  untracked but *not ignored* — while README, AGENTS, `docs/README.md`, and
  `docs/development.md` all asserted that `output/` is git-ignored. A
  contributor in a separated copy could commit generated artifacts against the
  project's own stated invariant. A `.gitignore` now ships. The binding test
  evaluates it with a real `git check-ignore` inside a throwaway repository
  holding nothing else, checks that no real content is swallowed, and uses the
  same probe *without* the file as its positive control. Measured: a fresh
  `git init` + `git add -A` over the clone stages 94 files and zero paths from
  `output/`, `.venv/`, or `htmlcov/`, with all three present on disk.
- **Five markdown links resolved outside the repository root.** `README.md`,
  `docs/README.md`, `docs/manuscript/01_introduction.md`, and
  `docs/manuscript/01b_line_set_relationship.md` (twice) pointed at
  `../../docs/line-set.md`, a private sidecar note. Three of the five ship
  inside the rendered manuscript. The acknowledgement is kept and only its
  address changed: each now names the sibling work and its repository under
  `docxology/`, with the set documented once in the companion `line_set` work.
  Relative links escaping the root: **5 → 0**, bound by a scan whose positive
  control plants exactly the link shape that was removed.
- **`ruff` was in the validation contract and declared nowhere.** README,
  AGENTS, and `docs/development.md` all instructed `uv run ruff check` while
  `ruff` was absent from both `pyproject.toml` and `uv.lock`, so following the
  contract from a clean clone either failed or silently used an ambient,
  unpinned tool. `ruff>=0.6.0` is now in the `dev` extra, pinned in `uv.lock`,
  and configured (`target-version = "py310"`, matching the declared floor). The
  binding test extracts every tool a contract block invokes and requires each to
  be both declared and locked.
- **Rendering was documented as a `cd` up three levels into a sibling
  `template/` directory,** a path that resolves only inside one private layout.
  (The literal is not repeated here: `tests/test_standalone_contract.py` fails
  on any tracked document that carries it, and a changelog is a document.)
  `docs/development.md` now gives a
  path-independent recipe parameterised on `TEMPLATE_ROOT`, names the engine as
  the repository <https://github.com/docxology/template>, and states plainly
  that the typeset PDF/HTML is the one thing this repository cannot produce
  alone — a declared external dependency, and an absent PDF is an unrun gate
  rather than a failing one. Everything else runs offline from the copy.
- **A missing rasterizer took down the entire suite.** The session fixture that
  rebuilds the ignored figure mirror raised when `rsvg-convert` was absent, so
  on such a machine all **256** tests errored, including the 251 that never look
  at `output/`. The fixture now checks for the rasterizer first, and the five
  gates that read the mirror take a `shipped_figures` fixture that asserts the
  mirror really is absent *and* that no rasterizer could have built it before
  skipping with a named reason. Measured on a stripped `PATH`: **256 errors →
  239 passed, 5 skipped, 12 failed**, the 12 being the pre-existing tests that
  genuinely need librsvg to build figures (17 non-passing before this pass).
- **The skill descriptor located itself at a monorepo path.**
  `.agents/skills/black-line/SKILL.md` described "the Black Line instrument at
  `projects/working/black_line/`", a directory that does not exist in the
  standalone repository. It now names the repository and states that its paths
  are relative to that repository's root.
- **The pre-build failure count was stale in the documentation.** README,
  AGENTS, `docs/development.md`, and the skill descriptor each named *three*
  tests that fail before `build_figures.py`; the measured number was five. With
  the rebuild fixture in place the number is zero in either order, and all four
  documents now say so and name the five gates that read the mirror.
- **New `STANDALONE.md`,** matching the siblings: what a separated copy is, what
  it can do alone (the whole local loop, offline, with `rsvg-convert` as the one
  system requirement), and what it cannot (the typeset manuscript).

### 2026-07-27 (adversarial verification pass)

- **The refresh-queue caption called an undated declaration dated.** The band
  lists three omitted declarations and one of them is omitted *because* it is
  undated, so "the 3 dated declarations the queue omits" was false of exactly
  the row that motivates the class. Corrected in the figure spec caption, the
  figure's own `<desc>`, the manuscript embed, and the
  `horizon_omissions` docstring. The caption-equality test could not catch this
  — both copies agreed with each other and disagreed with the data — so
  `tests/test_manuscript_bindings.py::test_refresh_queue_omission_wording_matches_the_executed_omissions`
  re-derives the omission classes and rejects the wording on every surface that
  reaches a reader.
- **The tag-minimization contrast was labelled with the wrong fold.**
  `docs/manuscript/05_limits.md` called the executed `analysis`+`data` → `data`
  narrowing "eightfold"; the executed contrast is 7 practices / 14 labels down
  to 1 / 2, which is sevenfold. Eightfold is the registry's widest spread
  (`research` 8 against `data` 1) and is correctly stated in
  `03_practices.md`. The limits prose now states the derived ratio, both label
  counts, and the distinction; the binding test re-derives the fold and
  refuses the borrowed literal.
- **Every script fails closed on unexpected arguments.** `build_figures.py`,
  `check_figures.py`, and `check_registry.py` take no options and no operands
  but silently ignored `--nope`, a bare operand, or a misspelled flag and
  exited 0 — an exit code a CI line reads as a pass. New shared
  `scripts/_cli.py` guard exits 2 with a usage line;
  `tests/test_scripts_cli.py` discovers the script roster from the directory
  (so a new unguarded script fails there), asserts each one still succeeds on
  a good run, and feeds each five argument shapes.
- **The practice list paraphrased two registry wires.** Nine of the eleven
  entries in `docs/manuscript/03_practices.md` quoted their wire verbatim; entry 1
  said "scope … selecting tools" where the registry says "boundary … choosing
  tools", and entry 5 dropped an article. The paper and the shipped registry
  therefore described the same practice differently while the digest and every
  figure gate stayed green. All eleven titles, families, and wires are now
  re-read from `BLACK_PRACTICES` by a binding test.
- **The documented verification order could not work on a fresh checkout.**
  `output/` is git-ignored, and three tests measure the shipped mirror rather
  than a temporary bundle — the rendered-legibility floor, the
  rasterized-pixel check, and the cover embed. README, AGENTS, the
  development doc, and the skill descriptor all listed `pytest` before
  `build_figures.py`, which fails 3 tests on a clean clone. Build now comes
  first in all four, with the reason stated.

### 2026-07-27 (legibility floor, three derived figures, ledger derivation)

- **In-figure text now has a measured floor.** Every label in the shipped PDF
  was rendering between 3.2pt and 4.3pt: the renderer's default
  `0.5\textheight` cap bound before the declared `width=100%` on tall plates
  and shrank the whole image, and the canvas-relative font sizes were screen
  scale rather than print scale. New `src/black_line/figures/legibility.py`
  derives the rendered point size of each label from the canvas, the declared
  embed width, and the page geometry in `docs/manuscript/config.yaml`;
  `docs/manuscript/config.yaml` now declares `rendering.figure_height_fraction`
  and `rendering.cover_height_fraction` so width binds; and `figures/svg.py`
  clamps every drawing helper to a floor derived from its own canvas.
  Measured minimum across the generated plates moved from **3.18pt** (nine
  plates, the worst being `black_practice_wires`) to **6.12pt** (thirteen
  plates). `tests/test_legibility.py` fails below 6pt and is shown to reject a
  planted shrunken font and a canvas widened without its text. It also binds
  the assumption underneath the arithmetic: every shipped PNG must rasterize
  to exactly the SVG canvas the point size is measured against, proved by
  rasterizing a rescaled copy and confirming the check rejects it.
- **Status grids no longer encode meaning in colour alone.** Cells in the
  incremental path and the new lattice carry a status letter, and the decay
  strips name each contiguous status run, so both read in greyscale.
- **Three derived figures.** `fig:black-refresh-queue` draws `refresh_horizon`
  in its own ascending order with an explicitly named band for the three
  omitted classes; `fig:black-monotonicity-lattice` sweeps twelve seeded
  declaration orders through `declaration_status_path`, marks each with
  `no_status_regression`, and counts inversions — turning Proposition 4 from
  one trace into an executed sweep; `fig:black-batch-summary` runs the
  evaluator over a pinned battery of eight differently-tagged attempts and
  draws `summarize_assessments` beside a per-practice gap ranking, which is
  the first time the figure set shows more than one attempt. All three are
  embedded with prose cross-references in `docs/manuscript/04_examples.md`, and the
  batch panel is shown to follow its data by rebuilding it from a one-attempt
  batch and checking the ranking, the totals, and the never-open band all move.
- **The cover reaches a reader.** `cover_art.png` is embedded with its
  registry caption in `docs/manuscript/01b_line_set_relationship.md`, and
  `validate_generated_figures` now binds `paper.cover.image` in
  `docs/manuscript/config.yaml` to the registry `cover` entry.
- **The figure gate compares the whole contract.** `alt`,
  `interpretive_claim`, and `epistemic_boundary` are checked against the
  declared specs for every figure and the cover; blanking any of them used to
  leave `scripts/check_figures.py` green.
- **`refresh_horizon` consumes its `practices` argument.** The parameter was
  accepted and never read, so a caller passing a narrower registry still got
  every dated label. The queue is now filtered to labels some practice
  requires, each item names those practices, and the new
  `refresh_horizon_omissions` reports every excluded declaration with its
  reason.
- **The claim ledger is derived, not declared.** `data/claim_ledger.yaml` is
  re-keyed on the claim rather than the bare integer (so `manuscript-number-7`
  no longer conflates two unrelated 7s) and every row is re-derived from the
  running package by `tests/test_claim_ledger.py`, closed in both directions
  and checked with a planted-bad row. The row whose `source_tier` was
  `document_structure` — contradicting the file's own header — is gone.
- **Canvases derive from the registry.** The evidence matrix and coverage
  heatmap sized their plates by literal, so a larger registry would have
  clipped the matrix's boundary sentence and the heatmap's margin totals; both
  now derive their extent and take an injected registry, with a regression
  test that renders seventeen practices.
- **Documented recipes are executed.** `docs/usage.md`'s staleness recipe
  promised a sweep and demonstrated a flat one for three independent reasons
  (a label outside the registry vocabulary, a label also declared undated, and
  unrelated unsatisfied practices); the batch recipe used `tests` for the
  registry's `test`. Every fenced recipe now carries its real output and
  `tests/test_docs_recipes.py` executes it.
- **Binding gaps closed.** Proposition 9's universal clause is checked field
  by field against `dataclasses.fields(BlackPractice)`; the incremental table's
  "labels added" and "practice completed" columns are re-derived; the coverage
  table's practice-id column is re-derived; the skill descriptor's and
  README's numeric literals are bound; `no_status_regression`'s `ValueError`
  on `OUTSIDE_SCOPE` is documented and exercised.
- **Prose corrections.** `06_conclusion.md` described the shipped Golden and
  White Line as forthcoming; `02_method.md` read the evaluator's first branch
  as per-practice when it tests the attempt-wide evidence sets;
  `01b_line_set_relationship.md` claimed the instruments "depend on one
  another" against the set's standalone rule; `03_practices.md` used British
  "colour-keyed" against the set's spelling; `docs/architecture.md` restated a
  version literal the project's own rule forbids; `docs/manuscript/AGENTS.md`
  described LLM settings the config does not contain; `figures/README.md` had
  a relative link resolving outside the project; the stage numbering in the
  abstract, method, formalism, and architecture doc now agrees; and three
  unused `\newtheorem` environments were dropped from the preamble.

### 2026-07-22 (operability: agent skill descriptor + doc reconciliation)

- Add `.agents/skills/black-line/SKILL.md`, the project-scoped agent skill
  descriptor: the instrument boundary (what a status is and is never), an
  executed worked example (the same dated declaration is `ALIGNED` under a
  60-day window and `NEEDS_EVIDENCE` under 30 — `data_origin` aged 51 days —
  with verbatim evaluator output), the full `black_line.analytics` surface
  with derived coverage numbers, gates, and gotchas. Commands are
  copy-pasteable from the project root; no version literal is restated
  (authority remains `docs/manuscript/config.yaml`, bound by
  `tests/test_version_sync.py`).
- README: new Analytics, Figures, and Agent skill sections referencing the
  analytics module (with the derived 8/16-vs-1/2 tag-burden asymmetry over
  27 of 55 applicable cells), the nine deterministic figures plus cover
  (including the coverage heatmap and evidence-decay strips), and the skill
  descriptor. Line-set framing unchanged: the four projects are the "set",
  never a "suite".
- TODO: reconcile against this expansion window — record what the analytics,
  manuscript, and operability passes completed, keep the three
  intentionally-deferred boundary items open, and add honest follow-ups
  (unbound literals in the skill descriptor, undocumented analytics recipes
  in `docs/usage.md`, and a possible refresh-horizon view).

### 2026-07-22 (manuscript expansion: executed examples + adversarial declarations)

- Rework `docs/manuscript/04_examples.md` into executed worked examples: a
  17-step incremental-declaration status-path table for a `research`-tagged
  attempt (empty declaration `NEEDS_EVIDENCE`; steps 1–15 `NEEDS_REWORK`
  with `ALIGNED` practice findings accumulating 0→7; `ALIGNED` only at the
  sixteenth label) and an executed decay-sweep table over the
  `data-provenance` practice (window 30 flips at age 31, window 51 at age
  52, no window never, a never-declared label `NEEDS_REWORK` at every age).
- Add `docs/manuscript/05_limits.md` "Adversarial declarations" subsection with
  three executed attacks — label-stuffing (all 22 vocabulary labels →
  `ALIGNED`), tag-minimization (`{analysis, data}` `NEEDS_REWORK` over 7
  findings vs `{data}` `ALIGNED` over 1, same labels), and refresh-date
  laundering (70-day-old evidence `NEEDS_EVIDENCE` under a 30-day window,
  redated to review day `ALIGNED`) — framed via Campbell, Strathern, and
  Power (new `references.bib` entries), preserving that a status reports
  declaration coverage and gaming overstates nothing but coverage.
- Expand the "Registry coverage and burden" subsection with the full derived
  per-tag coverage table (27 of 55 cells; every practice carries exactly two
  required labels) and cross-links to the adversarial subsection.
- Add `tests/test_manuscript_bindings.py`: numeric claims in
  the new prose is re-derived through the public API and the manuscript is
  asserted to quote the derived value, so prose drift from the evaluator
  fails the suite.

### 2026-07-22 (analytics + coverage expansion)

- Add `src/black_line/analytics.py`: pure, deterministic functions over the
  frozen types — `coverage_matrix` (tag reach and declaration burden),
  `staleness_profile` (freshness-window sweeps through the real evaluator),
  `summarize_assessments` (batch status and open-finding family counts), and
  `declaration_status_path` / `no_status_regression` / `status_rank` for
  status-transition sweeps. All exported additively; public semantics
  untouched.
- Close the self-documented Proposition 4 test gap: seeded permutation sweeps
  now exercise general conditional monotonicity (no status regression after a
  non-empty declaration, over label permutations, irrelevant labels, stale
  backdrops, and widening windows), with the empty-declaration boundary kept
  as a positive control that the checker can reject.
- Add two derived figures: a tag-practice coverage heatmap (from
  `coverage_matrix`; the declaration burden varies eightfold with tag choice)
  and an evidence-decay strip chart from executed `evaluate_work` sweeps
  pinning the strict `age > window` staleness rule. Both embedded in the
  manuscript with interpretive claims and epistemic boundaries.
- Bind version copies: tests now sync `docs/manuscript/config.yaml` `paper.version`
  and `pyproject.toml` to `black_line.__version__`, and the cover-art version
  marker is derived from `__version__` instead of a hardcoded `0.3` literal.
- Refactor `tests/test_figures.py` from index-pinned label assertions to
  name-based membership with an explicit `EXPECTED_FIGURE_COUNT`, plus an
  embed gate asserting every registered figure appears in the manuscript.
- Manuscript: new "Registry coverage and burden" section naming the
  tag-minimization coverage gaming mode; staleness example upgraded to an
  executed strict-inequality boundary (age 51 days: window 51 `ALIGNED`,
  window 50 `NEEDS_EVIDENCE`).

### 2026-07-21 (audit improvement pass)

- Correct the worked example in `docs/manuscript/04_examples.md`: for tags
  `{research}` the evaluator requests failure, handoff, rerun, uncertainty,
  negative-result, and review evidence — never `method` (the only practice
  requiring `method`, smallest-sufficient-method, is tagged
  engineering/analysis). Verified by executing the exact scenario.
- Align monotonicity claim provenance with Proposition 4's own wording in
  `docs/manuscript/05_limits.md` and `docs/usage.md`: no test exercises the general
  monotonicity property (zero `monoton` hits in `tests/`); the conditional
  claim follows from the finding rules, with the boundary case tested by
  `test_irrelevant_evidence_only_needs_rework`.

## 0.3.0 — 2026-07-18

- Pin every evaluated assessment to the practice-registry digest.
- Reject invalid review dates and freshness-window configuration before scoring.
- Harden registry invariants against malformed evidence-field shapes.
- Add a deterministic evidence-contract figure and digest metadata to the
  figure registry.
- Add a five-step operating-loop diagram that connects freshness, digest
  pinning, repair, refresh, and archival to the reviewer boundary.
- Add deterministic title-page cover art: unresolved marks narrow into an
  inspectable line through frame, method, evidence, review, and handoff.
- Give all generated figures a shared cream-paper editorial system with serif
  headlines, restrained purple/teal accents, and more legible full-width
  manuscript placement.
- Use explicit 0.5-inch left/right geometry with slightly deeper top/bottom
  breathing room so the denser render gives figures and captions more usable
  width without weakening the validation gates.
- Expand usage, review-protocol, development, limits, and deferred-work docs.
- Extend the scholarship section with reproducibility/replicability, open
  research culture, and tacit-knowledge distinctions, plus a literature-to-wire
  map and five verified references.
- Add a claim ledger, a five-layer epistemic-boundary figure, explicit visual
  claim/boundary metadata, and scholarship on verification versus validation,
  situated action, boundary objects, and epistemic humility.
