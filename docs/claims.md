# Claim ledger

This ledger separates what Black Line computes, what the manuscript recommends,
and what remains an empirical or governance question. It is a guard against
turning a clean diagram or a positive status into a stronger claim than the
project can support.

| Claim class | Claim | Evidence in this project | Boundary |
| --- | --- | --- | --- |
| Computational | `evaluate_work` normalizes declarations, partitions dated labels, matches practices by tag, scores findings, and aggregates a status. | Source in `src/black_line/evaluator.py`; branch-complete tests in `tests/test_evaluator.py`; formal definitions in the manuscript. | The implementation is tested for its stated inputs; tests do not establish that the labels point to adequate evidence. |
| Computational | The registry and assessment serialization are deterministic for fixed inputs, and the registry digest identifies method content. | `tests/test_serialization.py`, `tests/test_black_line.py`, and the generated figure registry. | The digest is not a signature, timestamp, provenance proof, or authentication of evidence. |
| Structural | The built-in registry has eleven practices, six craft families, and a five-tag vocabulary, with seven structural checks. | `src/black_line/registry.py`, `src/black_line/invariants.py`, `tests/test_registry.py`, and `tests/test_invariants.py`. | Coverage and reachability are properties of the registry, not evidence that a practice was completed. |
| Methodological | Question-first framing, traceability, small methods, visible failure, reruns, review, stewardship, and explicit limits are useful practices to try. | The practice registry plus the scholarship map in `manuscript/01c_scholarship.md`. | This is a design synthesis and recommendation, not a causal finding that the instrument improves outcomes. |
| Epistemic | `ALIGNED` means every required label for every applicable practice was declared as fresh under the chosen review date. | `src/black_line/evaluator.py`, `docs/usage.md`, and the status-path figure. | It does not mean the source is authentic, the test passed, the inference is sound, the result generalizes, or the action is permitted. |
| Computational | Once a declaration is non-empty, accumulating fresh labels never regresses the status, and widening the freshness window never regresses it either; the empty-declaration boundary is the one intentional exception. | `black_line.analytics` (`declaration_status_path`, `no_status_regression`, `staleness_profile`) with seeded permutation sweeps and a boundary positive control in `tests/test_analytics.py`. | Monotone status ordering is a property of declaration coverage; it says nothing about whether the declared evidence is adequate or true. |
| Structural | Tag reach and declaration burden are asymmetric: `research` reaches 8 practices (16 required labels) while `data` reaches 1 (2 labels), across 27 applicable cells of 55. | `black_line.analytics.coverage_matrix`, pinned literals in `tests/test_analytics.py`, and the coverage heatmap figure. | Burden asymmetry is an applicability fact enabling tag-minimization gaming; it is not a quality ranking of tags or work. |
| Computational | Staleness uses a strict inequality: evidence aged exactly the window is fresh, one day older is stale (e.g. age 51 days is `ALIGNED` under window 51 and `NEEDS_EVIDENCE` under window 50). | `tests/test_analytics.py` boundary pins over `staleness_profile` and the executed evidence-decay figure. | Freshness of a declared date does not show the underlying observation was ever adequate or still holds. |
| Computational | Malformed declarations are normalized into a status plus named intake notes rather than an exception; a blank description and an unscoreable registry both fail closed with no findings. | `src/black_line/evaluator.py`, the hostile-input cases in `tests/test_evaluator.py`, and the executed intake plate bound by `tests/test_figures.py::test_the_intake_plate_follows_the_executed_battery`. | Returning a status for unusable input is not acceptance of it; a note reports what was ignored and verifies nothing declared correctly. |
| Structural | Each of the seven invariants is shown rejecting a registry built to break it, not only passing on the real one. | `tests/test_invariants.py` pass-on-real and fail-on-planted pairs, plus the executed detection matrix bound by `tests/test_figures.py::test_the_detection_plate_follows_the_executed_battery`. | Detection is a property of the checks over registry shape; it says nothing about the merit of the practices or the adequacy of any evidence. |
| Structural | Every definition and proposition in the formalism section is bound to a named test, carries a label rather than a hand-written number, and every cross-reference resolves from that label. | `tests/test_formalism_definitions.py` re-derives each definition from the package; `tests/test_formalism_syntax.py` refuses an unlabelled block, an unresolved reference, or a hand-written block number. | The bindings establish that the prose matches the code, never that the code is the right code. |
| Visual | Figures are deterministic explanatory maps of registry structure and protocol semantics. | `scripts/build_figures.py`, `output/figures/figure_registry.json`, and rendered PDF/HTML outputs. | Visual clarity cannot increase evidential strength; every figure carries an interpretive claim and epistemic boundary. |
| Visual | Every in-figure label prints at 6pt or larger in the rendered PDF. | `src/black_line/figures/legibility.py` derives the size from the canvas, the declared embed width, and the page geometry; `tests/test_legibility.py` fails below the floor and is shown to reject a planted shrunken font. | A legible label is not a correct one, and the floor says nothing about whether the figure's claim is sound. |
| Empirical / governance | Black Line improves correctness, speed, equity, safety, or downstream decisions, or grants authority to proceed. | No evidence is claimed in this project. | These require a defined study, comparator, outcomes, and governance review; they remain outside the current instrument. |

## Review rule

Before adding a sentence, status label, caption, or visual element, classify it:

1. If it is a computational or structural claim, bind it to executable code and
   a test that could fail.
2. If it is a methodological recommendation, name the scholarly lineage and
   state that the project offers a design synthesis rather than an outcome study.
3. If it concerns truth, generalization, harm, safety, legality, or permission,
   state the required external reviewer or governance boundary instead of
   letting `ALIGNED` imply it.

The figure registry mirrors this discipline with `interpretive_claim` and
`epistemic_boundary` fields for every generated visual, including the cover.

The machine-readable numeric support surface is
[`claim_ledger.yaml`](../data/claim_ledger.yaml). Every row is keyed on the
claim rather than the bare integer and is re-derived from the running package
by `tests/test_claim_ledger.py`, which closes the mapping in both directions
and is itself checked with a planted-bad row. The external template evidence
validator (<https://github.com/docxology/template>) ingests the file's declared
tier verbatim, so the derivation has to live here; a hand-written provenance
field is not evidence of provenance.
