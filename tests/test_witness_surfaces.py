"""Typed evidence surfaces and the common assessment envelope.

The surfaces make co-presence machine-readable: a practice can carry strong
support and strong resistance at once, and the status word is a projection
of that state, not a replacement for it. Every case runs the real staged
evaluator; the equivalence tests compare ``evaluate_with_surfaces`` against
``evaluate_work`` on the same arguments, so the two public forms are proven
to report one computation. Several tests carry the canonical witness-case
families (STATE, RELATION) from the 2026-07-29 design review in their names.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from black_line import (
    BLACK_LINE_ID,
    BLACK_PRACTICES,
    ENVELOPE_SCHEMA,
    SCOPE_AND_NONCLAIMS,
    AssessmentStatus,
    EvidenceItem,
    PracticeStatus,
    WorkAttempt,
    __version__,
    assessment_digest,
    assessment_envelope,
    canonical_assessment,
    canonical_envelope,
    envelope_matches_assessment,
    evaluate_with_surfaces,
    evaluate_work,
)

AS_OF = "2026-07-18"

#: A battery covering every assessment shape: aligned, mixed co-presence,
#: no-evidence, stale-only gaps, outside scope, and a blocking description.
ATTEMPT_BATTERY: tuple[tuple[str, WorkAttempt, int | None], ...] = (
    (
        "aligned research framing",
        WorkAttempt(
            "Compare two methods for the stated research question",
            tags=frozenset({"research"}),
            evidence=frozenset(
                {
                    "question",
                    "scope",
                    "source",
                    "claim",
                    "failure",
                    "test",
                    "next_step",
                    "handoff",
                    "environment",
                    "rerun",
                    "uncertainty",
                    "limits",
                    "negative_result",
                    "log",
                    "reviewer",
                    "review_note",
                }
            ),
        ),
        None,
    ),
    (
        "partial declaration with co-present support and resistance",
        WorkAttempt(
            "Analyze the archived colony traces",
            tags=frozenset({"analysis"}),
            evidence=frozenset({"question", "scope", "source"}),
        ),
        None,
    ),
    (
        "no evidence declared at all",
        WorkAttempt("Sketch the next study", tags=frozenset({"research"})),
        None,
    ),
    (
        "stale-only gap under a freshness window",
        WorkAttempt(
            "Refresh the provenance record",
            tags=frozenset({"data"}),
            evidence=frozenset({"data_origin"}),
            dated_evidence=(EvidenceItem("transform_log", "2026-01-01"),),
        ),
        30,
    ),
    (
        "outside the declared tag vocabulary",
        WorkAttempt("Practice the violin", tags=frozenset({"music"})),
        None,
    ),
    (
        "blocking blank description",
        WorkAttempt("   ", tags=frozenset({"research"})),
        None,
    ),
)


def test_both_public_forms_report_one_staged_computation() -> None:
    """`evaluate_with_surfaces` returns byte-identical assessments to
    `evaluate_work` across every assessment shape."""

    for label, attempt, window in ATTEMPT_BATTERY:
        alone = evaluate_work(attempt, as_of=AS_OF, max_evidence_age_days=window)
        paired, _surfaces = evaluate_with_surfaces(
            attempt, as_of=AS_OF, max_evidence_age_days=window
        )
        assert canonical_assessment(alone) == canonical_assessment(paired), label


def test_surfaces_align_one_to_one_with_findings_and_generate_their_reasons() -> None:
    """Each finding's reasons trail is re-derivable from its typed surfaces,
    so the prose and the data cannot drift apart."""

    for label, attempt, window in ATTEMPT_BATTERY:
        assessment, surfaces = evaluate_with_surfaces(
            attempt, as_of=AS_OF, max_evidence_age_days=window
        )
        assert [item.practice_id for item in surfaces] == [
            finding.practice_id for finding in assessment.findings
        ], label
        for finding, surface in zip(assessment.findings, surfaces):
            assert tuple(sorted(surface.stale)) == tuple(
                sorted(set(surface.stale) & set(surface.missing))
            )
            if finding.status is PracticeStatus.ALIGNED:
                assert finding.reasons == (
                    "required evidence is present: " + ", ".join(surface.present),
                )
                assert surface.missing == ()
            elif finding.reasons == ("no evidence was declared",):
                continue
            else:
                expected = [
                    "required evidence is missing: " + ", ".join(surface.missing)
                ]
                if surface.present:
                    expected.append(
                        "evidence already present: " + ", ".join(surface.present)
                    )
                if surface.stale:
                    expected.append(
                        "stale evidence needs refresh: " + ", ".join(surface.stale)
                    )
                assert finding.reasons == tuple(expected), label


def test_support_and_resistance_stay_co_present_under_the_projection() -> None:
    """RELATION case: strong support and strong resistance on one practice
    are not the same as no evidence, and neither erases the other."""

    assessment, surfaces = evaluate_with_surfaces(
        WorkAttempt(
            "Analyze the archived colony traces",
            tags=frozenset({"analysis"}),
            evidence=frozenset({"question", "scope", "source"}),
        ),
        as_of=AS_OF,
    )
    assert assessment.status is AssessmentStatus.NEEDS_REWORK
    aligned = next(item for item in surfaces if item.practice_id == "question-first")
    assert aligned.present == ("question", "scope")
    assert aligned.missing == ()
    mixed = next(item for item in surfaces if item.practice_id == "source-traceable")
    assert mixed.present == ("source",)
    assert mixed.missing == ("claim",)
    empty = next(item for item in surfaces if item.practice_id == "stated-uncertainty")
    assert empty.present == ()
    assert empty.missing == ("uncertainty", "limits")
    # The projection compresses these three shapes into one word; the typed
    # surfaces keep them distinct.
    assert {item.practice_id for item in surfaces if item.present and item.missing}


def test_a_stale_only_gap_keeps_its_refresh_surface_typed() -> None:
    _assessment, surfaces = evaluate_with_surfaces(
        WorkAttempt(
            "Refresh the provenance record",
            tags=frozenset({"data"}),
            evidence=frozenset({"data_origin"}),
            dated_evidence=(EvidenceItem("transform_log", "2026-01-01"),),
        ),
        as_of=AS_OF,
        max_evidence_age_days=30,
    )
    provenance = next(
        item for item in surfaces if item.practice_id == "data-provenance"
    )
    assert provenance.present == ("data_origin",)
    assert provenance.missing == ("transform_log",)
    assert provenance.stale == ("transform_log",)


def test_blocked_and_unscorable_paths_carry_no_surfaces() -> None:
    blocked_assessment, blocked_surfaces = evaluate_with_surfaces(
        WorkAttempt("   ", tags=frozenset({"research"})), as_of=AS_OF
    )
    assert blocked_assessment.findings == ()
    assert blocked_surfaces == ()
    bad_registry_assessment, bad_registry_surfaces = evaluate_with_surfaces(
        WorkAttempt("work", tags=frozenset({"research"})),
        ("not a practice",),  # type: ignore[arg-type]
        as_of=AS_OF,
    )
    assert bad_registry_assessment.status is AssessmentStatus.NEEDS_REWORK
    assert bad_registry_surfaces == ()


def test_an_outside_scope_attempt_has_no_findings_and_no_surfaces() -> None:
    assessment, surfaces = evaluate_with_surfaces(
        WorkAttempt("Practice the violin", tags=frozenset({"music"})), as_of=AS_OF
    )
    assert assessment.status is AssessmentStatus.OUTSIDE_SCOPE
    assert surfaces == ()


# ---------------------------------------------------------------------------
# The common assessment envelope.
# ---------------------------------------------------------------------------


def _assessment():
    return evaluate_work(
        WorkAttempt(
            "Compare two methods for the stated research question",
            tags=frozenset({"research", "analysis"}),
            evidence=frozenset({"question", "scope", "source", "claim"}),
        ),
        as_of=AS_OF,
    )


def test_the_envelope_points_at_the_native_assessment_without_reinterpreting_it() -> (
    None
):
    assessment = _assessment()
    envelope = assessment_envelope(
        assessment, subject_id="worked-example", source_snapshot_refs=("snapshot-1",)
    )
    assert envelope.schema_version == ENVELOPE_SCHEMA
    assert envelope.line_id == BLACK_LINE_ID
    assert envelope.subject_id == "worked-example"
    assert envelope.review_date == assessment.evaluated_as_of == AS_OF
    assert envelope.registry_version == __version__
    assert envelope.registry_digest == assessment.registry_digest
    assert envelope.native_status == assessment.status.value
    assert envelope.report_ref == assessment_digest(assessment)
    assert envelope.source_snapshot_refs == ("snapshot-1",)
    assert envelope.scope_and_nonclaims == SCOPE_AND_NONCLAIMS
    assert any("not permission" in claim for claim in envelope.scope_and_nonclaims)


def test_aligned_never_manufactures_settlement_or_permission() -> None:
    """RELATION case: a strong method result carries its non-claims with it,
    so good method cannot quietly become epistemic settlement or permission."""

    envelope = assessment_envelope(_assessment())
    assert any("never authorizes" in claim for claim in envelope.scope_and_nonclaims)
    assert any("does not verify" in claim for claim in envelope.scope_and_nonclaims)


def test_canonical_envelope_round_trips_and_is_deterministic() -> None:
    assessment = _assessment()
    first = canonical_envelope(assessment_envelope(assessment, subject_id="s"))
    second = canonical_envelope(assessment_envelope(assessment, subject_id="s"))
    assert first == second
    payload = json.loads(first)
    assert payload["line_id"] == BLACK_LINE_ID
    assert payload["native_status"] == assessment.status.value
    assert payload["scope_and_nonclaims"] == list(SCOPE_AND_NONCLAIMS)


def test_envelope_matches_assessment_verifies_an_archived_pair() -> None:
    assessment = _assessment()
    envelope = assessment_envelope(assessment, subject_id="worked-example")
    assert envelope_matches_assessment(envelope, assessment)
    other = evaluate_work(
        WorkAttempt("Sketch the next study", tags=frozenset({"research"})),
        as_of=AS_OF,
    )
    assert not envelope_matches_assessment(envelope, other)
    for tamper in (
        {"report_ref": "0" * 64},
        {"review_date": "2020-01-01"},
        {"registry_digest": "0" * 64},
        {"native_status": "ALIGNED-PLUS"},
    ):
        assert not envelope_matches_assessment(
            dataclasses.replace(envelope, **tamper), assessment
        )


def test_envelope_input_validation_fails_closed() -> None:
    assessment = _assessment()
    with pytest.raises(ValueError, match="non-blank strings"):
        assessment_envelope(assessment, source_snapshot_refs=("",))
    with pytest.raises(ValueError, match="non-blank strings"):
        assessment_envelope(assessment, source_snapshot_refs=(42,))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="subject_id must be a string"):
        assessment_envelope(assessment, subject_id=7)  # type: ignore[arg-type]


def test_the_battery_reaches_every_assessment_status() -> None:
    """The equivalence proof above is only as strong as the shapes it swept;
    assert the sweep reaches the whole status alphabet."""

    reached = {
        evaluate_work(attempt, as_of=AS_OF, max_evidence_age_days=window).status
        for _label, attempt, window in ATTEMPT_BATTERY
    }
    assert reached == set(AssessmentStatus)


def test_registry_order_is_the_surface_order() -> None:
    _assessment_result, surfaces = evaluate_with_surfaces(
        WorkAttempt(
            "Compare two methods",
            tags=frozenset({"research"}),
            evidence=frozenset({"question"}),
        ),
        as_of=AS_OF,
    )
    matched_ids = [
        practice.id for practice in BLACK_PRACTICES if "research" in practice.tags
    ]
    assert [item.practice_id for item in surfaces] == matched_ids
