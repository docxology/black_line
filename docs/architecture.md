# Architecture

Black Line is a modular package. Each module answers one question and the
public API in `__init__.py` re-exports every stable surface.

```text
src/black_line/
├── __init__.py        public API
├── version.py         package version marker
├── model/             typed model
│   ├── enums.py       PracticeStatus, AssessmentStatus, PracticeKind
│   └── records.py     BlackPractice, EvidenceItem, WorkAttempt,
│                      PracticeFinding, EvidenceSurfaces, BlackAssessment
├── models.py          public alias for model/ (same symbols)
├── registry.py        BLACK_PRACTICES (11 entries), tag vocabulary
├── evaluator.py       one staged core behind evaluate_work and
│                      evaluate_with_surfaces
├── serialization.py   canonical JSON + registry and assessment records,
│                      assessment_digest
├── envelope.py        the cross-instrument report envelope
│                      (line.report-envelope/1.0): assessment_envelope,
│                      canonical_envelope, envelope_matches_assessment
├── invariants.py      structural review checks + all_invariants battery
├── analytics.py       pure derived views: coverage_matrix, staleness_profile,
│                      summarize_assessments, declaration_status_path,
│                      refresh_horizon, refresh_horizon_omissions
└── figures/           deterministic SVG builders + figure registry + validate
    ├── svg.py         palette, layout constants, primitives
    ├── scenarios.py   shared evaluator fixtures for figures and bindings
    ├── registry_schematics.py   practice wires, taxonomy, evidence matrix
    ├── protocol_schematics.py   status path, operating loop, claim layers
    ├── analytics_figures.py     coverage heatmap, decay, incremental path
    ├── horizon_figures.py       refresh queue, monotonicity lattice
    ├── batch_figures.py         multi-attempt distribution + gap ranking
    ├── legibility.py  rendered point size of in-figure text
    ├── cover.py / specs.py / output.py / validate.py
```

`analytics.py` never duplicates evaluator semantics: its sweeps call the real
`evaluate_work`, and its outputs are frozen, ordered structures that figures
and manuscript numbers can cite reproducibly. Like every other surface, the
analytics describe declaration coverage — never quality, safety, or
permission.

Figure builders live under `figures/`; `scripts/build_figures.py` and
`scripts/check_figures.py` are thin CLIs over `build_figures` and
`validate_generated_figures`.

## Staged evaluation

`evaluate_work` runs in stages so malformed input degrades into recorded
intake notes instead of crashes or silent passes:

The numbering below is the one the manuscript's formal section and the
status-path figure use: configuration validation is a pre-stage that runs
before scoring, then four numbered stages.

0. **Review configuration** (pre-stage) — `as_of` (ISO string or `date`) pins
   the evaluation date; the default is today. Invalid dates and negative or
   non-integer freshness windows are rejected before scoring.
1. **Intake normalization** — the description must be non-blank text (a
   blank description is a blocking defect: `NEEDS_REWORK` with no findings).
   Tag and evidence declarations are normalized; malformed tokens are dropped
   and noted in `intake_notes`.
2. **Freshness partition** — `EvidenceItem(label, noted_on)` records when
   evidence was last observed. Future-dated or unreadable dates are never
   counted. With `max_evidence_age_days` set, older evidence goes stale.
3. **Tag matching** — practices whose tags intersect the attempt's tags are
   selected.
4. **Scoring and aggregation** — each selected practice is first split into
   typed `EvidenceSurfaces` (its present, missing, and stale required
   labels), and the finding's status and reasons trail are projected from
   those surfaces: what is present, what is missing, what only needs refresh.
   The overall status takes the most demanding per-practice status. A finding
   whose only gaps are stale items is `NEEDS_EVIDENCE` (refresh), not
   `NEEDS_REWORK`. `evaluate_with_surfaces` returns the surfaces beside the
   identical assessment — one shared staged implementation, never a second
   evaluator — so strong support and strong resistance on one practice stay
   readable together instead of collapsing into the projected word.

Custom registries are checked for the record shapes that matching and
serialization require. A malformed registry fails closed as `NEEDS_REWORK`
with no findings; the built-in registry is additionally covered by the full
invariant battery.

Pre-0.2 call forms are unchanged: `evaluate_work(attempt)` and
`evaluate_work(attempt, practices)` behave exactly as before, and
`BlackAssessment`'s additive fields default to empty when constructed directly.
Assessments returned by the evaluator carry the registry digest that was used.

## Registry digest as a review instrument

`registry_digest` hashes the canonical, order-independent JSON serialization
of the practice registry. `evaluate_work` places that digest on every
`BlackAssessment`, including an empty digest plus a review note if a custom
registry cannot be serialized. It exists so reviewers can pin the exact
practice content an assessment referred to and so unexpected edits are visible
as a digest change. It is a review and drift instrument only — it carries no
safety or permission semantics.

The manuscript's claim-layer map keeps three questions separate: what decision
the work informs, what procedure was run, and what record another reader can
inspect. World adequacy and authority remain outside the evaluator and require
domain, independent, or governance review.

## The report envelope

`envelope.py` exports the cross-instrument report envelope, declared under
the schema string `line.report-envelope/1.0`. `assessment_envelope` wraps an
assessment as a reference: the review date, the registry digest, the native
status word, a SHA-256 pointer (`report_ref`) to the complete
`canonical_assessment` output, caller-supplied source snapshot references,
and the instrument's non-claims (`SCOPE_AND_NONCLAIMS`). The envelope points
at the native record and never reinterprets it; sibling line instruments that
export the same shape do so by publishing the same schema string, never by
importing one another, and envelopes from different lines must not be
compared, ranked, averaged, or merged on `native_status`.
`envelope_matches_assessment` is the read-back check for an archived
envelope-plus-assessment pair.

## Invariants and proof-of-detection

`invariants.all_invariants()` runs seven structural checks over the registry
(see [invariants.md](invariants.md)). The test suite holds each check to a
proof-of-detection standard: it must pass on the real registry **and** fail
on a planted-bad registry built with `dataclasses.replace`. A green check
that never saw a bad input does not count as protection.
