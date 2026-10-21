# Usage and review protocol

Black Line is most useful as a small review loop, not as a one-time score:

1. State the work, boundary, and applicable tags.
2. Declare the evidence labels that a collaborator can inspect.
3. Pin `as_of` when the review must be reproducible.
4. Add `EvidenceItem` dates when evidence is expected to age.
5. Read the per-practice reasons and intake notes before acting on the overall status.
6. Archive an `evaluation_record` with the inspectable source files or links. `canonical_assessment/1.0` retains results, not original declarations or replay configuration.

```python
from black_line import EvidenceItem, WorkAttempt, evaluate_work

attempt = WorkAttempt(
    "Test whether the smallest method answers the stated question",
    tags=frozenset({"research", "engineering"}),
    evidence=frozenset({"question", "scope", "method", "decision"}),
    dated_evidence=(EvidenceItem("method", "2026-07-18"),),
)
assessment = evaluate_work(
    attempt,
    as_of="2026-07-18",
    max_evidence_age_days=30,
)
print(assessment.status.value)
```

```text
NEEDS_REWORK
```

The attempt is tagged `research` and `engineering`, so it is scored against
every practice either tag reaches; four declared labels do not cover them.
Serialize results with `canonical_assessment(assessment)`; retain a replay record
when the original input and method must be reconstructable.

## Status semantics

`ALIGNED` means every required label for every applicable practice was declared
as fresh evidence under the chosen review date. It does not mean that the
underlying artifacts are present, true, or independent. `NEEDS_EVIDENCE` means
the work has no usable evidence for a practice, or its only remaining gaps are
dated evidence that needs refresh.
`NEEDS_REWORK` means some required evidence is absent while other evidence is
present, or the description is not assessable. `OUTSIDE_SCOPE` means no
practice's reviewed tags matched; it is not an approval.

The empty-evidence edge case is deliberate: adding only an irrelevant label can
move a practice from `NEEDS_EVIDENCE` to `NEEDS_REWORK`, because the declaration
has begun while the required labels remain absent. See the formal method for the
conditional monotonicity claim; `tests/test_analytics.py` exercises it with
seeded permutation sweeps over `black_line.declaration_status_path`, including
the boundary case as a positive control that the regression checker can reject.

Intake notes are part of the review record. A malformed extra token can coexist
with a positive status when all required labels are present, but the note is a
signal to repair the declaration before relying on the record.

## What the digest means

`assessment.registry_digest` is the SHA-256 digest of the canonical practice
registry used for the evaluation. It makes a later registry edit visible, but
it does not authenticate the evidence or provide tamper-proof provenance. The
figure registry carries the same digest so generated visuals can be compared to
the executable method.

## Analytics recipes

### Staleness window sweep

Use `staleness_profile` when a reviewer needs to see how one attempt's status
responds as the freshness window tightens. Each point is a real
`evaluate_work` call — the profile inherits the strict-inequality rule (evidence
aged exactly `window` days is still fresh).

Route a label that should age through `dated_evidence` only. A label also
listed in the plain `evidence` set is fresh at every window, so a sweep over it
is flat by construction; so is a sweep over a label the registry does not
require, or over an attempt whose other practices are unsatisfied anyway.

```python
from black_line import EvidenceItem, WorkAttempt, staleness_profile

attempt = WorkAttempt(
    "Quarterly data provenance review",
    tags=frozenset({"data"}),
    dated_evidence=(
        EvidenceItem("data_origin", "2026-06-01"),
        EvidenceItem("transform_log", "2026-06-01"),
    ),
)
for point in staleness_profile(attempt, (30, 45, 60, None), as_of="2026-07-18"):
    print(point.max_evidence_age_days, point.status.value)
```

```text
30 NEEDS_EVIDENCE
45 NEEDS_EVIDENCE
60 ALIGNED
None ALIGNED
```

The evidence is 47 days old at that review date, so the flip sits between the
45-day and 60-day windows. Both gaps are stale rather than absent, which is
why the tightened windows ask for a refresh (`NEEDS_EVIDENCE`) instead of
rework.

### Batch review summary

Use `summarize_assessments` after evaluating a cohort. Status counts include
every enum value (zeros included) so reports stay shape-stable; open finding
counts group non-`ALIGNED` practice findings by craft family only when the
assessment's registry digest matches the supplied snapshot. Otherwise family
attribution is `UNKNOWN`; `registry_partitions` preserves each digest's counts
and whether attribution is available. Missing IDs and old empty digests are
also unavailable. Overall status counts are retained regardless.

```python
from black_line import WorkAttempt, evaluate_work, summarize_assessments

attempts = [
    WorkAttempt("data pull", frozenset({"data"}), frozenset()),
    WorkAttempt(
        "unit tests", frozenset({"engineering"}), frozenset({"failure", "test"})
    ),
]
assessments = tuple(evaluate_work(a, as_of="2026-07-18") for a in attempts)
summary = summarize_assessments(assessments)
print(summary.total)
for status, count in summary.status_counts:
    print(status, count)
for kind, count in summary.open_finding_kind_counts:
    print(kind, count)
```

```text
2
ALIGNED 0
NEEDS_EVIDENCE 1
NEEDS_REWORK 1
OUTSIDE_SCOPE 0
COMMUNICATION 2
METHOD 1
STEWARDSHIP 1
TRACEABILITY 1
VERIFICATION 1
```

The registry label is `test`, not `tests`; a misspelled label is simply
unmatched, and the `failure-visible` finding still reports both required labels
as missing.

### Refresh horizon

Use `refresh_horizon` as an observation-expiry inventory, sorted by days to the
first stale day. It preserves qualifying dated occurrences, including
non-applicable practices and shadowed labels; its `practice_ids` identifies
registry requirements, not a promise of status impact. `last_fresh_on` and
`stale_on` disambiguate the boundary. In 0.5.0, `days_until_stale` changes to
count through the first stale day; `days_until_last_fresh_day` retains the old
arithmetic. At age equal to the window the former is one and the latter zero.

`refresh_horizon_omissions` gives each excluded occurrence a reason and index:
undated, already stale, unrequired, future, unreadable, malformed, or expiry
disabled (`None`). Labels use the evaluator's strip/lowercase normalization;
an expiry beyond the representable calendar receives
`expiry_out_of_calendar_range`, without changing evaluation's valid window policy.
raw labels remain available for diagnostics. Both views reject negative,
boolean and non-integer windows and datetime review values, like evaluation.
None disables expiry while retaining evaluator freshness semantics.

```python
from black_line import (
    EvidenceItem,
    WorkAttempt,
    refresh_horizon,
    refresh_horizon_omissions,
)

attempt = WorkAttempt(
    "Quarterly data provenance review",
    tags=frozenset({"data"}),
    dated_evidence=(
        EvidenceItem("transform_log", "2026-06-15"),
        EvidenceItem("data_origin", "2026-01-10"),
        EvidenceItem("dashboard_link", "2026-06-05"),
    ),
)
for item in refresh_horizon(attempt, as_of="2026-07-18", max_evidence_age_days=90):
    print(item.label, item.days_until_stale, "|", ", ".join(item.practice_ids))
for omitted in refresh_horizon_omissions(
    attempt, as_of="2026-07-18", max_evidence_age_days=90
):
    print("omitted:", omitted.label)
```

```text
transform_log 58 | data-provenance
omitted: dashboard_link
omitted: data_origin
```

`data_origin` is already past the window and `dashboard_link` is not a label
the registry requires. Passing a narrower `practices=` registry narrows the
inventory. For assessment impact use `effective_refresh_queue`: its `items`
filter applicable practices, undated shadowing, and later fresh declarations;
its `omissions` retains excluded occurrences with `non_applicable`,
`shadowed_by_undated`, `superseded_by_newer_declaration`, or
`no_predicted_surface_change`. Each retained row includes exact before/after
`transitions` computed through the evaluator at `last_fresh_on` and `stale_on`.
Equal-date duplicates describe the same expiry cohort. Future declarations
are not counted now but may become usable by a predicted boundary; transitions
include that effect. A surface can change while the overall word stays fixed.

### Typed surfaces and the report envelope

`evaluate_with_surfaces` returns exactly what `evaluate_work` returns — one
shared staged implementation, not a second evaluator — plus one
`EvidenceSurfaces` per finding: the practice's present, missing, and stale
required labels as typed co-present data. The status word is a projection of
those surfaces plus attempt-wide evidence context; strong support and strong resistance on the same practice
stay readable together instead of collapsing into it. `assessment_envelope`
then wraps the assessment in the cross-instrument report envelope
(`line.report-envelope/1.0`): a reference by digest to the complete canonical
assessment, the review date and registry digest, the native status word, and
the instrument's non-claims, so a stored envelope cannot quietly outgrow what
the instrument was allowed to say.

```python
from black_line import (
    WorkAttempt,
    assessment_envelope,
    envelope_matches_assessment,
    evaluate_with_surfaces,
)

attempt = WorkAttempt(
    "Analyze the archived colony traces",
    tags=frozenset({"analysis"}),
    evidence=frozenset({"question", "scope", "source"}),
)
assessment, surfaces = evaluate_with_surfaces(attempt, as_of="2026-07-18")
print(assessment.status.value)
for surface in surfaces:
    marks = "+" * len(surface.present) + "-" * len(surface.missing)
    print(surface.practice_id, marks, sep=" | ")
envelope = assessment_envelope(assessment, subject_id="colony-traces-2026")
print(envelope.line_id, envelope.native_status)
print(
    "envelope points at this exact assessment:",
    envelope_matches_assessment(envelope, assessment),
)
```

```text
NEEDS_REWORK
question-first | ++
source-traceable | +-
smallest-sufficient-method | --
failure-visible | --
stated-uncertainty | --
negative-results-kept | --
data-provenance | --
black_line NEEDS_REWORK
envelope points at this exact assessment: True
```

One `NEEDS_REWORK` covers three different shapes — a fully covered practice,
a half-covered one, and five untouched ones — and the surfaces keep the
difference. Archive `canonical_envelope(envelope)` beside
`canonical_assessment(assessment)`; `envelope_matches_assessment` checks only report correspondence
(digest, date, registry digest and status). `validate_envelope_contract` checks
schema, line identity, field types, native vocabulary, and required non-claims.
It explicitly leaves subject, source references, and producing version
unverified against the result alone. `envelope_matches_record` also checks
those fields against a replay record. These are structural checks only.
Bare string/bytes reference containers are rejected; collections and generators
of nonblank strings are accepted. `strict=True` rejects incomplete envelope
exports from old results lacking date, digest, or producing version. None of this changes what
a status means: coverage of self-declared labels, never quality, truth,
safety, or permission.

## Replay records and migration

`evaluation_record(attempt, as_of=..., max_evidence_age_days=...)` captures
`black_line.evaluation-record/1.0`: original text/set/dated declarations,
normalized tags and fresh/stale labels, pinned date/window and producing
package version, complete ordered registry snapshot and digest, assessment,
typed surfaces and attempt-wide `evidence_declared`, subject/source references,
and non-claims. Serialize with `canonical_evaluation_record`, identify with
`evaluation_record_digest`, deserialize with `load_evaluation_record`, and
recompute with `replay_evaluation_record`. Replay compares the whole retained
record by canonical identity, including exact boolean types, assessment and
surfaces, and requires the recorded released
package version. It never silently replays an older method with today's code.

The safe JSON intake supports `WorkAttempt` with text description, frozensets
of text tags/labels, and a tuple of `EvidenceItem` records with text labels and
text/None dates. Blank labels and unreadable/future dates are retained with
the evaluator's normalization notes. Arbitrary Python objects are rejected;
the bundle does not claim to preserve hostile or unsupported object behavior.
Set order is not meaningful; dated occurrence and registry order are retained.

Old `canonical_assessment/1.0` bytes and their `report_ref` digests do not
change. They cannot be upgraded into faithful input records without the
original declaration and configuration. Producing version is captured on new
assessments, rather than stamped by the package exporting an old result.
Hashing and replay demonstrate input retention and structural consistency,
not signatures, authenticity, source existence, truth, safety, or permission.

```python
from black_line import (
    WorkAttempt, evaluation_record, canonical_evaluation_record,
    load_evaluation_record, replay_evaluation_record,
)

record = evaluation_record(
    WorkAttempt("Inspect the provenance record", frozenset({"data"})),
    as_of="2026-07-18", max_evidence_age_days=30,
)
restored = load_evaluation_record(canonical_evaluation_record(record))
print(replay_evaluation_record(restored) == (record.assessment, record.surfaces))
print(record.evidence_declared)
```

```text
True
False
```

## What a reviewer still has to do

The evaluator is lexical and self-declared. A reviewer must still inspect the
source, data origin, transformation log, tests, failure analysis, deployment
context, and downstream effects. The instrument deliberately does not replace
domain review, legal review, security refusal, or independent replication.
