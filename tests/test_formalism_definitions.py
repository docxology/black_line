"""Bind every formalism *definition* to the code it claims to describe.

The propositions in `manuscript/03b_formalism.md` have named tests. The
definitions did not: they described the record shapes, the normalization rule,
the freshness partition, the applicability rule, and both decision tables in
prose that nothing re-derived. A definition is the part of the formalism a
reader trusts most and the part most easily left behind by a refactor — renaming
a field, adding an enum member, or reordering a branch would have contradicted
the paper while every other gate stayed green.

Each test below recomputes one definition's content from the running package and
asserts the manuscript still states it. No mocks: every status comes from a real
`evaluate_work` call, and every record shape is read from
`dataclasses.fields`. Where a definition names a rejection, the rejection is
executed rather than described.
"""

from __future__ import annotations

import re
from dataclasses import fields
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from black_line import (
    BLACK_PRACTICES,
    ENVELOPE_SCHEMA,
    PRACTICE_TAG_VOCABULARY,
    SCOPE_AND_NONCLAIMS,
    AssessmentEnvelope,
    AssessmentStatus,
    BlackAssessment,
    BlackPractice,
    EvidenceItem,
    EvidenceSurfaces,
    PracticeFinding,
    PracticeKind,
    PracticeStatus,
    WorkAttempt,
    assessment_digest,
    assessment_envelope,
    canonical_assessment,
    evaluate_with_surfaces,
    evaluate_work,
    registry_digest,
)

MANUSCRIPT = Path(__file__).resolve().parent.parent / "manuscript"
AS_OF = date(2026, 7, 1)
#: A practice with a two-label contract and a single tag, so the tests below can
#: vary one thing at a time. Read from the registry rather than restated.
DATA_PRACTICE = next(p for p in BLACK_PRACTICES if "data" in p.tags)


def _formalism() -> str:
    return (MANUSCRIPT / "03b_formalism.md").read_text(encoding="utf-8")


def _collapsed() -> str:
    """The formalism section with line wrapping removed.

    Where the section is wrapped is an editorial choice; what it says is not.
    """

    return " ".join(_formalism().split())


def _assess(attempt: WorkAttempt, **kwargs) -> BlackAssessment:
    return evaluate_work(attempt, BLACK_PRACTICES, as_of=AS_OF, **kwargs)


# --- domain objects -----------------------------------------------------------


def test_practice_record_matches_the_definition() -> None:
    """The six-tuple, its order, and the METHOD default are re-read from code."""

    names = [field.name for field in fields(BlackPractice)]
    assert names == ["id", "title", "wire", "tags", "required_evidence", "kind"]
    minimal = BlackPractice("x", "t", "w", frozenset({"data"}), ("a",))
    assert minimal.kind is PracticeKind.METHOD

    collapsed = _collapsed()
    assert (
        r"$p = (\mathrm{id}, \mathrm{title}, \mathrm{wire}, \mathrm{tags}, "
        r"\mathrm{req}, \mathrm{kind})$" in collapsed
    )
    assert (
        f"defaults to `{PracticeKind.METHOD.value}` when omitted from positional "
        "construction" in collapsed
    )


def test_tag_vocabulary_matches_the_definition() -> None:
    """V is the exported vocabulary, and the registry stays inside it."""

    vocabulary = sorted(PRACTICE_TAG_VOCABULARY)
    assert vocabulary == ["analysis", "data", "engineering", "research", "writing"]
    declared = {tag for practice in BLACK_PRACTICES for tag in practice.tags}
    assert declared == PRACTICE_TAG_VOCABULARY

    collapsed = _collapsed()
    for tag in vocabulary:
        assert rf"\texttt{{{tag}}}" in collapsed, tag
    assert f"$|V| = {len(PRACTICE_TAG_VOCABULARY)}$" in collapsed


def test_registry_matches_the_definition() -> None:
    """R is an ordered tuple of the stated size carrying a computable digest."""

    assert isinstance(BLACK_PRACTICES, tuple)
    assert len(BLACK_PRACTICES) == 11
    assert all(isinstance(p, BlackPractice) for p in BLACK_PRACTICES)
    digest = registry_digest(BLACK_PRACTICES)
    assert _assess(WorkAttempt("work", frozenset({"data"}))).registry_digest == digest

    assert "ordered tuple of eleven practices" in _collapsed()


def test_craft_families_match_the_definition() -> None:
    """K is exactly the declared enum, and every member is used."""

    families = [kind.value for kind in PracticeKind]
    assert families == [
        "FRAMING",
        "TRACEABILITY",
        "METHOD",
        "VERIFICATION",
        "COMMUNICATION",
        "STEWARDSHIP",
    ]
    used = {practice.kind for practice in BLACK_PRACTICES}
    assert used == set(PracticeKind)

    collapsed = _collapsed()
    for family in families:
        assert rf"\texttt{{{family}}}" in collapsed, family
    assert "with six families" in collapsed


def test_work_attempt_matches_the_definition() -> None:
    """W is the four-field record and a dated item is the declared pair."""

    assert [field.name for field in fields(WorkAttempt)] == [
        "description",
        "tags",
        "evidence",
        "dated_evidence",
    ]
    assert [field.name for field in fields(EvidenceItem)] == ["label", "noted_on"]
    assert EvidenceItem("data_origin").noted_on is None

    collapsed = _collapsed()
    assert r"$W = (\mathrm{desc}, T, E, D)$" in collapsed
    assert r"pair $(\ell, \tau)$" in collapsed


def test_assessment_record_matches_the_definition() -> None:
    """A is the five-field record and each finding is the declared triple."""

    assert [field.name for field in fields(BlackAssessment)] == [
        "status",
        "findings",
        "intake_notes",
        "evaluated_as_of",
        "registry_digest",
    ]
    assert [field.name for field in fields(PracticeFinding)] == [
        "practice_id",
        "status",
        "reasons",
    ]
    assessment = _assess(
        WorkAttempt("work", frozenset({"data"}), frozenset({"data_origin"}))
    )
    assert assessment.evaluated_as_of == AS_OF.isoformat()
    assert isinstance(assessment.findings, tuple)
    assert all(isinstance(f.reasons, tuple) for f in assessment.findings)

    collapsed = _collapsed()
    assert r"$A = (s, \mathcal{F}, N, d, h)$" in collapsed
    assert (
        "triple of a practice id, a practice status, and an ordered reasons trail"
        in (collapsed)
    )


# --- status codomains ---------------------------------------------------------


def test_practice_status_codomain_matches_the_definition() -> None:
    values = [status.value for status in PracticeStatus]
    assert values == ["ALIGNED", "NEEDS_EVIDENCE", "NEEDS_REWORK"]
    collapsed = _collapsed()
    for value in values:
        assert rf"\texttt{{{value.replace('_', chr(92) + '_')}}}" in collapsed, value


def test_assessment_status_codomain_matches_the_definition() -> None:
    """S_a is S_p plus exactly one more member, and it is OUTSIDE_SCOPE."""

    practice_values = {status.value for status in PracticeStatus}
    assessment_values = {status.value for status in AssessmentStatus}
    assert practice_values < assessment_values
    assert assessment_values - practice_values == {"OUTSIDE_SCOPE"}
    assert "OUTSIDE_SCOPE" not in practice_values

    collapsed = _collapsed()
    assert r"$S_a = S_p \cup \{\texttt{OUTSIDE\_SCOPE}\}" in collapsed
    assert "never a per-practice status" in collapsed


# --- the two pre-stages -------------------------------------------------------


def test_review_configuration_refuses_what_the_definition_names() -> None:
    """Every rejection the definition names is executed, and each accepted form works."""

    attempt = WorkAttempt("work", frozenset({"data"}), frozenset({"data_origin"}))
    # Accepted forms.
    assert evaluate_work(
        attempt, BLACK_PRACTICES, as_of="2026-07-01"
    ).evaluated_as_of == ("2026-07-01")
    assert evaluate_work(attempt, BLACK_PRACTICES, as_of=AS_OF).evaluated_as_of == (
        AS_OF.isoformat()
    )
    assert evaluate_work(attempt, BLACK_PRACTICES).evaluated_as_of == (
        date.today().isoformat()
    )
    # Refused forms, one per clause of the definition.
    with pytest.raises(ValueError, match="ISO date"):
        evaluate_work(attempt, BLACK_PRACTICES, as_of="2026-13-45")
    with pytest.raises(TypeError):
        evaluate_work(attempt, BLACK_PRACTICES, as_of=datetime(2026, 7, 1, 9, 0))
    with pytest.raises(TypeError):
        evaluate_work(attempt, BLACK_PRACTICES, as_of=20260701)
    with pytest.raises(TypeError):
        evaluate_work(attempt, BLACK_PRACTICES, max_evidence_age_days=True)
    with pytest.raises(TypeError):
        evaluate_work(attempt, BLACK_PRACTICES, max_evidence_age_days=1.5)
    with pytest.raises(ValueError, match="non-negative"):
        evaluate_work(attempt, BLACK_PRACTICES, max_evidence_age_days=-1)
    # Zero is a legal window, so "non-negative" is not a stand-in for "positive".
    assert evaluate_work(attempt, BLACK_PRACTICES, max_evidence_age_days=0).status

    collapsed = _collapsed()
    assert "raises `ValueError`" in collapsed
    assert "raises `TypeError` rather than being coerced" in collapsed
    assert "non-negative `int`" in collapsed


def test_intake_normalization_matches_the_definition() -> None:
    """clean() strips and lowercases, every drop is noted, and block() is exact."""

    normalized = _assess(
        WorkAttempt(
            "work",
            ("  DATA  ",),
            ("  Data_Origin ", "TRANSFORM_LOG"),
        )
    )
    assert [f.practice_id for f in normalized.findings] == [DATA_PRACTICE.id]
    assert normalized.status is AssessmentStatus.ALIGNED, normalized.intake_notes
    assert normalized.intake_notes == ()

    dropped = _assess(WorkAttempt("work", ("data",), ("data_origin", "  ", 7)))
    assert len(dropped.intake_notes) == 2
    assert all("malformed evidence label" in note for note in dropped.intake_notes)

    string_field = _assess(WorkAttempt("work", "data", frozenset({"data_origin"})))
    assert any("not a collection" in note for note in string_field.intake_notes)

    # block(W) is exactly "not a string, or strips to empty".
    for description in ("", "   ", "\n\t", 42, None):
        blocked = _assess(WorkAttempt(description, frozenset({"data"})))
        assert blocked.status is AssessmentStatus.NEEDS_REWORK, description
        assert blocked.findings == (), description
    assert _assess(WorkAttempt(" w ", frozenset({"data"}))).findings != ()

    collapsed = _collapsed()
    assert r"\mathrm{lower}(\mathrm{strip}(t))" in collapsed
    assert r"\mathrm{strip}(\mathrm{desc}) = \varepsilon" in collapsed


def test_freshness_partition_matches_the_definition() -> None:
    """Each of the five partition rules is executed against the real evaluator."""

    def dated(noted_on, label="data_origin"):
        return WorkAttempt(
            "work",
            frozenset({"data"}),
            frozenset({"transform_log"}),
            (EvidenceItem(label, noted_on),),
        )

    # 1. an unusable label is dropped with a note
    unusable = _assess(dated("2026-06-01", label="  "), max_evidence_age_days=30)
    assert any("without a usable label" in note for note in unusable.intake_notes)
    # 2. undated counts as fresh
    assert _assess(dated(None), max_evidence_age_days=30).status is (
        AssessmentStatus.ALIGNED
    )
    # 3a. future dates are counted in neither set
    future = _assess(dated((AS_OF + timedelta(days=1)).isoformat()))
    assert any("dated in the future" in note for note in future.intake_notes)
    assert future.status is AssessmentStatus.NEEDS_REWORK
    # 3b. unreadable dates likewise
    unreadable = _assess(dated("not-a-date"))
    assert any("unreadable date" in note for note in unreadable.intake_notes)
    assert unreadable.status is AssessmentStatus.NEEDS_REWORK
    # 4. age > window is stale, and a stale-only gap asks for a refresh
    stale = _assess(
        dated((AS_OF - timedelta(days=31)).isoformat()), max_evidence_age_days=30
    )
    assert stale.status is AssessmentStatus.NEEDS_EVIDENCE
    # 5. anything else is fresh
    fresh = _assess(
        dated((AS_OF - timedelta(days=30)).isoformat()), max_evidence_age_days=30
    )
    assert fresh.status is AssessmentStatus.ALIGNED

    collapsed = _collapsed()
    assert r"F = \mathrm{clean}(E) \cup \mathrm{fresh\_dated}$" in collapsed
    assert r"staleness begins at age $\omega + 1$" in collapsed


def test_applicability_matches_the_definition() -> None:
    """Selection is exactly non-empty tag intersection, for every tag in V."""

    for tag in sorted(PRACTICE_TAG_VOCABULARY):
        expected = [p.id for p in BLACK_PRACTICES if tag in p.tags]
        selected = [f.practice_id for f in _assess(WorkAttempt("w", (tag,))).findings]
        assert selected == expected, tag
        assert expected, tag
    # An empty intersection selects nothing at all.
    assert _assess(WorkAttempt("w", ("music",))).findings == ()
    assert _assess(WorkAttempt("w", ())).findings == ()

    assert (
        r"A(W) = \{\, p \in R : p.\mathrm{tags} \cap \mathrm{clean}(T) \neq "
        r"\emptyset \,\}" in _collapsed()
    )


def test_practice_finding_rule_matches_the_definition() -> None:
    """All four branches fire in the stated order, with ordered reasons trails."""

    first, second = DATA_PRACTICE.required_evidence

    def finding(**kwargs):
        assessment = _assess(WorkAttempt("work", frozenset({"data"}), **kwargs))
        return next(f for f in assessment.findings if f.practice_id == DATA_PRACTICE.id)

    # Branch 1: no usable evidence at all.
    empty = finding()
    assert empty.status is PracticeStatus.NEEDS_EVIDENCE
    assert empty.reasons == ("no evidence was declared",)
    # Branch 2: every required label fresh, present listed in declaration order.
    aligned = finding(evidence=frozenset({first, second}))
    assert aligned.status is PracticeStatus.ALIGNED
    assert aligned.reasons == (f"required evidence is present: {first}, {second}",)
    # Branch 3: the only gap is stale.
    stale_only = _assess(
        WorkAttempt(
            "work",
            frozenset({"data"}),
            frozenset({second}),
            (EvidenceItem(first, (AS_OF - timedelta(days=99)).isoformat()),),
        ),
        max_evidence_age_days=30,
    ).findings[0]
    assert stale_only.status is PracticeStatus.NEEDS_EVIDENCE
    assert any("stale evidence needs refresh" in r for r in stale_only.reasons)
    # Branch 4: a missing label that is not stale.
    rework = finding(evidence=frozenset({second}))
    assert rework.status is PracticeStatus.NEEDS_REWORK
    assert rework.reasons[0] == f"required evidence is missing: {first}"
    assert rework.reasons[1] == f"evidence already present: {second}"
    # With more than one label missing, the trail must keep declaration order —
    # a single-gap case would accept any ordering rule at all.
    both_missing = finding(evidence=frozenset({"unrelated"}))
    assert both_missing.status is PracticeStatus.NEEDS_REWORK
    assert both_missing.reasons == (f"required evidence is missing: {first}, {second}",)

    collapsed = _collapsed()
    assert r"$\mathrm{missing} \subseteq \Sigma$" in collapsed
    assert (
        "reasons trail naming present, missing, and stale-refresh labels" in collapsed
    )


def test_overall_aggregation_matches_the_definition() -> None:
    """Each aggregation branch is produced by a real attempt, in priority order."""

    # NEEDS_REWORK must dominate a *coexisting* NEEDS_EVIDENCE, or the first two
    # branches are untested against each other. This attempt produces both: the
    # data practice has only stale gaps (a refresh request) while the framing
    # practice is missing a label outright.
    aged = (AS_OF - timedelta(days=99)).isoformat()
    mixed = _assess(
        WorkAttempt(
            "work",
            frozenset({"analysis", "data"}),
            frozenset({"question"}),
            tuple(
                EvidenceItem(label, aged) for label in DATA_PRACTICE.required_evidence
            ),
        ),
        max_evidence_age_days=30,
    )
    statuses = {f.status for f in mixed.findings}
    assert {PracticeStatus.NEEDS_REWORK, PracticeStatus.NEEDS_EVIDENCE} <= statuses
    assert mixed.status is AssessmentStatus.NEEDS_REWORK
    # NEEDS_EVIDENCE when nothing is worse.
    evidence = _assess(WorkAttempt("work", frozenset({"data"})))
    assert {f.status for f in evidence.findings} == {PracticeStatus.NEEDS_EVIDENCE}
    assert evidence.status is AssessmentStatus.NEEDS_EVIDENCE
    # ALIGNED when findings exist and none is worse.
    aligned = _assess(
        WorkAttempt(
            "work", frozenset({"data"}), frozenset(DATA_PRACTICE.required_evidence)
        )
    )
    assert aligned.status is AssessmentStatus.ALIGNED
    # OUTSIDE_SCOPE only when there are no findings at all.
    outside = _assess(WorkAttempt("work", frozenset({"music"})))
    assert outside.findings == ()
    assert outside.status is AssessmentStatus.OUTSIDE_SCOPE

    collapsed = _collapsed()
    assert r"otherwise `ALIGNED` if $\mathcal{F} \neq \emptyset$" in collapsed
    assert "otherwise `OUTSIDE_SCOPE`" in collapsed


# --- surfaces, projection, and the report envelope -----------------------------

#: A declaration whose matched practices carry distinguishable surface shapes:
#: full support, support beside resistance, full resistance, and stale gaps.
SURFACES_ATTEMPT = WorkAttempt(
    "co-present support and resistance for the surfaces definition",
    frozenset({"analysis"}),
    frozenset({"question", "scope", "source"}),
    (
        EvidenceItem("failure", "2026-06-20"),
        EvidenceItem("test", "2026-04-01"),
    ),
)


def test_evidence_surfaces_match_the_definition() -> None:
    """The four-field record, stale ⊆ missing, and the declared-order invariant
    are re-read from the running code, and the manuscript states them exactly."""

    field_names = [field.name for field in fields(EvidenceSurfaces)]
    assert field_names == ["practice_id", "present", "missing", "stale"]

    assessment, surfaces = evaluate_with_surfaces(
        SURFACES_ATTEMPT, BLACK_PRACTICES, as_of=AS_OF, max_evidence_age_days=30
    )
    assert surfaces, "an empty battery would make every invariant below vacuous"
    by_id = {practice.id: practice for practice in BLACK_PRACTICES}
    for surface in surfaces:
        required = by_id[surface.practice_id].required_evidence
        # present and missing partition the required labels…
        assert set(surface.present) | set(surface.missing) == set(required)
        assert set(surface.present) & set(surface.missing) == set()
        # …in the practice's declared evidence order, all three tuples.
        assert surface.present == tuple(
            label for label in required if label in surface.present
        )
        assert surface.missing == tuple(
            label for label in required if label in surface.missing
        )
        assert surface.stale == tuple(
            label for label in required if label in surface.stale
        )
        # stale ⊆ missing always.
        assert set(surface.stale) <= set(surface.missing)
    # The battery reaches co-presence: at least one practice holds support and
    # resistance at once, and at least one stale surface is non-empty.
    assert any(surface.present and surface.missing for surface in surfaces)
    assert any(surface.stale for surface in surfaces)
    assert assessment.findings, "surfaces align with findings by construction"

    collapsed = _collapsed()
    sigma = (
        "$\\sigma(p) = ("
        + ", ".join(
            rf"\mathrm{{{name.replace('_', chr(92) + '_')}}}" for name in field_names
        )
        + ")$"
    )
    assert sigma in collapsed
    assert "with exactly those four fields" in collapsed
    assert r"$\mathrm{stale} \subseteq \mathrm{missing}$ always holds" in collapsed
    assert "keep the practice's declared evidence order" in collapsed
    # Positive control: a drifted body — one more field, or the inverted
    # containment — would fail, because the asserted strings are derived.
    assert (
        "$\\sigma(p) = ("
        + ", ".join(
            rf"\mathrm{{{name.replace('_', chr(92) + '_')}}}"
            for name in (*field_names, "verified")
        )
        + ")$"
    ) not in collapsed
    assert r"$\mathrm{missing} \subseteq \mathrm{stale}$" not in collapsed


def test_surfaces_projection_matches_the_proposition() -> None:
    """Both public forms report one staged computation, surfaces exist exactly
    when findings do, and the manuscript states the proposition it credits."""

    batteries = (
        (SURFACES_ATTEMPT, 30),
        (WorkAttempt("no evidence at all", frozenset({"research"})), None),
        (WorkAttempt("   ", frozenset({"research"})), None),  # blocked
        (WorkAttempt("off vocabulary", frozenset({"music"})), None),  # no match
    )
    for attempt, window in batteries:
        alone = evaluate_work(
            attempt, BLACK_PRACTICES, as_of=AS_OF, max_evidence_age_days=window
        )
        paired, surfaces = evaluate_with_surfaces(
            attempt, BLACK_PRACTICES, as_of=AS_OF, max_evidence_age_days=window
        )
        # Byte-identical assessments under canonical serialization.
        assert canonical_assessment(alone) == canonical_assessment(paired)
        # Surfaces align one-to-one with findings; none without findings.
        assert [surface.practice_id for surface in surfaces] == [
            finding.practice_id for finding in paired.findings
        ]

    collapsed = _collapsed()
    assert "The finding is then a *projection* of that state" in collapsed
    assert (
        "byte-identical, under canonical serialization, to what `evaluate_work` "
        "returns for the same arguments" in collapsed
    )
    assert "one staged core, never a second evaluator" in collapsed
    assert "no findings and therefore no surfaces" in collapsed
    # Positive control: the proposition's direction cannot be silently flipped.
    assert "a second evaluator behind the second public form" not in collapsed


def test_report_envelope_matches_the_definition() -> None:
    """The ten envelope fields, the digest pointer, and the travelling
    non-claims are re-derived from a real envelope over a real assessment."""

    field_names = [field.name for field in fields(AssessmentEnvelope)]
    assert field_names == [
        "schema_version",
        "line_id",
        "subject_id",
        "review_date",
        "registry_version",
        "registry_digest",
        "native_status",
        "report_ref",
        "source_snapshot_refs",
        "scope_and_nonclaims",
    ]
    assert len(field_names) == 10

    assessment = _assess(
        WorkAttempt("work", frozenset({"data"}), frozenset({"data_origin"}))
    )
    envelope = assessment_envelope(assessment, subject_id="formalism-witness")
    assert envelope.schema_version == ENVELOPE_SCHEMA == "line.report-envelope/1.0"
    assert envelope.report_ref == assessment_digest(assessment)
    assert envelope.native_status == assessment.status.value
    assert envelope.scope_and_nonclaims == SCOPE_AND_NONCLAIMS
    assert any("not permission" in claim for claim in envelope.scope_and_nonclaims)

    collapsed = _collapsed()
    ten_fields = (
        ", ".join(f"`{name}`" for name in field_names[:-1])
        + f", and `{field_names[-1]}`"
    )
    assert ten_fields in collapsed
    assert "exactly the ten fields, in order," in collapsed
    assert f"`{ENVELOPE_SCHEMA}`" in collapsed
    assert "SHA-256 digest of the complete `canonical_assessment`" in collapsed
    assert "must not be compared, ranked, averaged, or merged" in collapsed
    assert "stores and does not verify" in collapsed
    # Positive control: a drifted field list would fail, because the asserted
    # list is derived from the running record, not restated.
    assert (
        ", ".join(f"`{name}`" for name in field_names[:-2])
        + f", and `{field_names[-2]}`"
    ) not in collapsed


# --- the section states every definition it is credited with ------------------


def test_every_definition_in_the_section_is_bound_by_a_named_test() -> None:
    """The definition table must cover every ``.definition`` and ``.remark`` block.

    Closed in both directions: a definition with no row is unbound, and a row
    naming a label no block declares is a dangling entry. The named test must
    also exist, which is what stops a rename from quietly emptying the table.
    """

    text = _formalism()
    declared = re.findall(r"^::: \{\.(?:definition|remark) #([\w:-]+)", text, re.M)
    assert len(declared) >= 14, declared
    rows = re.findall(
        r"^\| \[@([\w:-]+)\] \| [^|]+ \| `tests/(test_\w+\.py)::(test_\w+)` \|$",
        text,
        re.M,
    )
    assert {label for label, _f, _fn in rows} == set(declared)

    tests_dir = Path(__file__).resolve().parent
    for _label, filename, function in rows:
        source = (tests_dir / filename).read_text(encoding="utf-8")
        assert f"def {function}(" in source, f"{filename}::{function}"


def test_the_definition_binding_can_fail() -> None:
    """Positive control: the section is compared against derived values, not itself.

    Every test above asserts a value derived from the package appears in the
    manuscript. If the manuscript said something else, the assertion would fail —
    which is exactly what this check demonstrates without editing the file.
    """

    collapsed = _collapsed()
    assert f"$|V| = {len(PRACTICE_TAG_VOCABULARY)}$" in collapsed
    assert f"$|V| = {len(PRACTICE_TAG_VOCABULARY) + 1}$" not in collapsed
    assert "ordered tuple of eleven practices" in collapsed
    assert "ordered tuple of twelve practices" not in collapsed
