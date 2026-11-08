"""Exercise native formalism behavior without authored prose as a test oracle."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from black_line import (
    BLACK_PRACTICES,
    ENVELOPE_SCHEMA,
    PRACTICE_TAG_VOCABULARY,
    AssessmentStatus,
    BlackAssessment,
    BlackPractice,
    EvidenceItem,
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

AS_OF = date(2026, 7, 1)
#: A practice with a two-label contract and a single tag, so the tests below can
#: vary one thing at a time. Read from the registry rather than restated.
DATA_PRACTICE = next(p for p in BLACK_PRACTICES if "data" in p.tags)


def _assess(attempt: WorkAttempt, **kwargs) -> BlackAssessment:
    return evaluate_work(attempt, BLACK_PRACTICES, as_of=AS_OF, **kwargs)


# --- domain objects -----------------------------------------------------------


def test_practice_record_matches_the_definition() -> None:
    """The six-tuple, its order, and the METHOD default are re-read from code."""

    minimal = BlackPractice("x", "t", "w", frozenset({"data"}), ("a",))
    assert minimal.kind is PracticeKind.METHOD



def test_tag_vocabulary_matches_the_definition() -> None:
    """V is the exported vocabulary, and the registry stays inside it."""

    vocabulary = sorted(PRACTICE_TAG_VOCABULARY)
    assert vocabulary == ["analysis", "data", "engineering", "research", "writing"]
    declared = {tag for practice in BLACK_PRACTICES for tag in practice.tags}
    assert declared == PRACTICE_TAG_VOCABULARY



def test_registry_matches_the_definition() -> None:
    """R is an ordered tuple of the stated size carrying a computable digest."""

    assert isinstance(BLACK_PRACTICES, tuple)
    assert len(BLACK_PRACTICES) == 11
    assert all(isinstance(p, BlackPractice) for p in BLACK_PRACTICES)
    digest = registry_digest(BLACK_PRACTICES)
    assert _assess(WorkAttempt("work", frozenset({"data"}))).registry_digest == digest



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



def test_work_attempt_matches_the_definition() -> None:
    """W is the four-field record and a dated item is the declared pair."""

    assert EvidenceItem("data_origin").noted_on is None



def test_assessment_record_matches_the_definition() -> None:
    assessment = _assess(
        WorkAttempt("work", frozenset({"data"}), frozenset({"data_origin"}))
    )
    assert assessment.evaluated_as_of == AS_OF.isoformat()
    assert isinstance(assessment.findings, tuple)
    assert all(isinstance(f.reasons, tuple) for f in assessment.findings)



# --- status codomains ---------------------------------------------------------


def test_practice_status_codomain_matches_the_definition() -> None:
    values = [status.value for status in PracticeStatus]
    assert values == ["ALIGNED", "NEEDS_EVIDENCE", "NEEDS_REWORK"]


def test_assessment_status_codomain_matches_the_definition() -> None:
    """S_a is S_p plus exactly one more member, and it is OUTSIDE_SCOPE."""

    practice_values = {status.value for status in PracticeStatus}
    assessment_values = {status.value for status in AssessmentStatus}
    assert practice_values < assessment_values
    assert assessment_values - practice_values == {"OUTSIDE_SCOPE"}
    assert "OUTSIDE_SCOPE" not in practice_values



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
    """Required-label partitions retain declaration order and stale containment."""

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



def test_surfaces_projection_matches_the_proposition() -> None:
    """Both public forms report one staged computation, with aligned surfaces."""

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


def test_report_envelope_matches_the_definition() -> None:
    """A real envelope preserves the assessment's status and digest pointer."""

    assessment = _assess(
        WorkAttempt("work", frozenset({"data"}), frozenset({"data_origin"}))
    )
    envelope = assessment_envelope(assessment, subject_id="formalism-witness")
    assert envelope.schema_version == ENVELOPE_SCHEMA == "line.report-envelope/1.0"
    assert envelope.report_ref == assessment_digest(assessment)
    assert envelope.native_status == assessment.status.value


