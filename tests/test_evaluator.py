"""Branch-complete tests for the staged evaluator."""

from datetime import date, datetime

import pytest

from black_line import (
    AssessmentStatus,
    BlackPractice,
    EvidenceItem,
    PracticeStatus,
    WorkAttempt,
    evaluate_work,
)

DEMO = BlackPractice(
    "demo-practice",
    "Demo practice",
    "A two-label wire for precise evaluator tests.",
    frozenset({"research"}),
    ("alpha", "beta"),
)
RESEARCH = frozenset({"research"})


class BrokenCanonicalPractice(BlackPractice):
    """Adversarial record used to prove digest failures fail closed."""

    def canonical(self) -> dict[str, object]:
        raise TypeError("canonical record failure")


def _one(attempt: WorkAttempt, **kwargs):
    assessment = evaluate_work(attempt, (DEMO,), **kwargs)
    assert len(assessment.findings) <= 1
    return assessment


# --- intake: description ---------------------------------------------------


def test_blank_description_is_a_blocking_intake_defect() -> None:
    assessment = evaluate_work(WorkAttempt("   ", RESEARCH, frozenset({"alpha"})))
    assert assessment.status is AssessmentStatus.NEEDS_REWORK
    assert assessment.findings == ()
    assert any("description" in note for note in assessment.intake_notes)


def test_non_text_description_is_a_blocking_intake_defect() -> None:
    assessment = evaluate_work(WorkAttempt(None, RESEARCH))  # type: ignore[arg-type]
    assert assessment.status is AssessmentStatus.NEEDS_REWORK
    assert assessment.findings == ()


# --- intake: hostile tag and evidence declarations -------------------------


def test_string_tag_declaration_is_ignored_with_a_note() -> None:
    assessment = evaluate_work(WorkAttempt("work", "research"))  # type: ignore[arg-type]
    assert assessment.status is AssessmentStatus.OUTSIDE_SCOPE
    assert any("tag declaration" in note for note in assessment.intake_notes)


def test_non_iterable_evidence_declaration_is_ignored_with_a_note() -> None:
    assessment = _one(WorkAttempt("work", RESEARCH, 7))  # type: ignore[arg-type]
    assert assessment.status is AssessmentStatus.NEEDS_EVIDENCE
    assert any("evidence declaration" in note for note in assessment.intake_notes)


def test_malformed_label_tokens_are_dropped_but_good_ones_kept() -> None:
    assessment = _one(WorkAttempt("work", RESEARCH, ["  ALPHA  ", "", 5, "beta"]))  # type: ignore[arg-type]
    assert assessment.status is AssessmentStatus.ALIGNED
    assert (
        sum("malformed evidence label" in note for note in assessment.intake_notes) == 2
    )


def test_malformed_tag_tokens_are_dropped_but_good_ones_kept() -> None:
    assessment = _one(
        WorkAttempt("work", frozenset({"research", ""}), frozenset({"alpha", "beta"}))
    )
    assert assessment.status is AssessmentStatus.ALIGNED
    assert any("malformed tag label" in note for note in assessment.intake_notes)


# --- matching and scoring --------------------------------------------------


def test_no_matching_tags_is_outside_scope_with_review_date() -> None:
    assessment = _one(WorkAttempt("a note", frozenset({"music"})), as_of="2026-07-01")
    assert assessment.status is AssessmentStatus.OUTSIDE_SCOPE
    assert assessment.findings == ()
    assert assessment.evaluated_as_of == "2026-07-01"


def test_no_evidence_at_all_needs_evidence() -> None:
    assessment = _one(WorkAttempt("work", RESEARCH))
    assert assessment.status is AssessmentStatus.NEEDS_EVIDENCE
    assert assessment.findings[0].reasons == ("no evidence was declared",)


def test_partial_evidence_needs_rework_with_present_and_missing_reasons() -> None:
    assessment = _one(WorkAttempt("work", RESEARCH, frozenset({"alpha", "unrelated"})))
    finding = assessment.findings[0]
    assert finding.status is PracticeStatus.NEEDS_REWORK
    assert any("missing: beta" in reason for reason in finding.reasons)
    assert any("already present: alpha" in reason for reason in finding.reasons)


def test_irrelevant_evidence_only_needs_rework_without_present_reason() -> None:
    assessment = _one(WorkAttempt("work", RESEARCH, frozenset({"unrelated"})))
    finding = assessment.findings[0]
    assert finding.status is PracticeStatus.NEEDS_REWORK
    assert not any("already present" in reason for reason in finding.reasons)


def test_complete_evidence_is_aligned_with_reason_trail() -> None:
    assessment = _one(WorkAttempt("work", RESEARCH, frozenset({"alpha", "beta"})))
    finding = assessment.findings[0]
    assert finding.status is PracticeStatus.ALIGNED
    assert "required evidence is present" in finding.reasons[0]


# --- review date -----------------------------------------------------------


def test_as_of_accepts_date_objects_and_strings_identically() -> None:
    attempt = WorkAttempt("work", RESEARCH)
    from_str = _one(attempt, as_of="2026-01-15")
    from_date = _one(attempt, as_of=date(2026, 1, 15))
    assert from_str.evaluated_as_of == from_date.evaluated_as_of == "2026-01-15"


def test_default_review_date_is_today() -> None:
    assessment = _one(WorkAttempt("work", RESEARCH))
    assert assessment.evaluated_as_of == date.today().isoformat()


def test_invalid_review_date_is_rejected_before_scoring() -> None:
    with pytest.raises(ValueError, match="ISO date"):
        _one(WorkAttempt("work", RESEARCH), as_of="tomorrow")


def test_non_date_review_configuration_is_rejected() -> None:
    with pytest.raises(TypeError, match="as_of"):
        _one(WorkAttempt("work", RESEARCH), as_of=20260718)  # type: ignore[arg-type]


def test_datetime_review_configuration_is_rejected_instead_of_mixed_date_comparison() -> (
    None
):
    with pytest.raises(TypeError, match="as_of"):
        _one(WorkAttempt("work", RESEARCH), as_of=datetime(2026, 7, 18))  # type: ignore[arg-type]


@pytest.mark.parametrize("window", [-1, True, "30"])
def test_invalid_staleness_window_is_rejected(window: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _one(WorkAttempt("work", RESEARCH), max_evidence_age_days=window)  # type: ignore[arg-type]


# --- dated evidence and staleness ------------------------------------------


def test_undated_evidence_item_counts_as_fresh() -> None:
    attempt = WorkAttempt(
        "work", RESEARCH, dated_evidence=(EvidenceItem("Alpha"), EvidenceItem("beta"))
    )
    assessment = _one(attempt, as_of="2026-07-01")
    assert assessment.status is AssessmentStatus.ALIGNED


def test_dated_evidence_without_staleness_window_never_goes_stale() -> None:
    attempt = WorkAttempt(
        "work",
        RESEARCH,
        dated_evidence=(
            EvidenceItem("alpha", "2020-01-01"),
            EvidenceItem("beta", "2020-01-01"),
        ),
    )
    assessment = _one(attempt, as_of="2026-07-01")
    assert assessment.status is AssessmentStatus.ALIGNED


def test_dated_evidence_within_window_is_fresh() -> None:
    attempt = WorkAttempt(
        "work",
        RESEARCH,
        dated_evidence=(
            EvidenceItem("alpha", "2026-06-20"),
            EvidenceItem("beta", "2026-06-25"),
        ),
    )
    assessment = _one(attempt, as_of="2026-07-01", max_evidence_age_days=30)
    assert assessment.status is AssessmentStatus.ALIGNED


def test_fully_stale_evidence_needs_refresh_not_rework() -> None:
    attempt = WorkAttempt(
        "work",
        RESEARCH,
        dated_evidence=(
            EvidenceItem("alpha", "2025-01-01"),
            EvidenceItem("beta", "2025-01-01"),
        ),
    )
    assessment = _one(attempt, as_of="2026-07-01", max_evidence_age_days=30)
    finding = assessment.findings[0]
    assert finding.status is PracticeStatus.NEEDS_EVIDENCE
    assert any(
        "stale evidence needs refresh: alpha, beta" in reason
        for reason in finding.reasons
    )


def test_mixed_stale_and_absent_evidence_still_needs_rework() -> None:
    attempt = WorkAttempt(
        "work",
        RESEARCH,
        dated_evidence=(EvidenceItem("alpha", "2025-01-01"),),
    )
    assessment = _one(attempt, as_of="2026-07-01", max_evidence_age_days=30)
    finding = assessment.findings[0]
    assert finding.status is PracticeStatus.NEEDS_REWORK
    assert any(
        "stale evidence needs refresh: alpha" in reason for reason in finding.reasons
    )
    assert any("missing: alpha, beta" in reason for reason in finding.reasons)


def test_future_dated_evidence_is_not_counted() -> None:
    attempt = WorkAttempt(
        "work",
        RESEARCH,
        evidence=frozenset({"beta"}),
        dated_evidence=(EvidenceItem("alpha", "2027-01-01"),),
    )
    assessment = _one(attempt, as_of="2026-07-01")
    assert assessment.findings[0].status is PracticeStatus.NEEDS_REWORK
    assert any("dated in the future" in note for note in assessment.intake_notes)


def test_unreadable_evidence_date_is_not_counted() -> None:
    attempt = WorkAttempt(
        "work",
        RESEARCH,
        dated_evidence=(EvidenceItem("alpha", "not-a-date"),),
    )
    assessment = _one(attempt, as_of="2026-07-01")
    assert any("unreadable date" in note for note in assessment.intake_notes)


def test_dated_record_without_usable_label_is_noted() -> None:
    attempt = WorkAttempt(
        "work",
        RESEARCH,
        dated_evidence=(EvidenceItem("   "), object()),  # type: ignore[arg-type]
    )
    assessment = _one(attempt, as_of="2026-07-01")
    assert (
        sum("without a usable label" in note for note in assessment.intake_notes) == 2
    )


def test_non_collection_dated_evidence_is_noted() -> None:
    attempt = WorkAttempt("work", RESEARCH, dated_evidence=5)  # type: ignore[arg-type]
    assessment = _one(attempt)
    assert any("dated evidence declaration" in note for note in assessment.intake_notes)


# --- overall aggregation ---------------------------------------------------


def test_rework_dominates_over_needs_evidence_in_overall_status() -> None:
    second = BlackPractice(
        "demo-second",
        "Second demo",
        "Another wire.",
        frozenset({"research"}),
        ("gamma",),
    )
    attempt = WorkAttempt("work", RESEARCH, frozenset({"alpha"}))
    assessment = evaluate_work(attempt, (DEMO, second))
    statuses = {finding.practice_id: finding.status for finding in assessment.findings}
    assert statuses["demo-practice"] is PracticeStatus.NEEDS_REWORK
    assert assessment.status is AssessmentStatus.NEEDS_REWORK


def test_assessment_pins_the_registry_digest_even_for_a_generator() -> None:
    attempt = WorkAttempt("work", RESEARCH, frozenset({"alpha", "beta"}))
    assessment = evaluate_work(attempt, (practice for practice in (DEMO,)))
    assert assessment.registry_digest


def test_undigestible_registry_is_reported_as_a_review_defect() -> None:
    invalid = BlackPractice(
        "invalid-kind",
        "Invalid kind",
        "A practice with an invalid family.",
        frozenset({"research"}),
        ("alpha",),
        "not-a-kind",  # type: ignore[arg-type]
    )
    assessment = evaluate_work(
        WorkAttempt("work", RESEARCH, frozenset({"alpha"})), (invalid,)
    )
    assert assessment.registry_digest == ""
    assert assessment.status is AssessmentStatus.NEEDS_REWORK
    assert assessment.findings == ()
    assert any("not safe to score" in note for note in assessment.intake_notes)


def test_malformed_custom_registry_is_blocked_before_tag_matching() -> None:
    invalid = BlackPractice(
        "invalid-tags",
        "Invalid tags",
        "A practice with the wrong tag representation.",
        ["research"],  # type: ignore[arg-type]
        ("alpha",),
    )
    assessment = evaluate_work(WorkAttempt("work", RESEARCH), (invalid,))
    assert assessment.status is AssessmentStatus.NEEDS_REWORK
    assert assessment.findings == ()
    assert any("malformed tags" in note for note in assessment.intake_notes)


@pytest.mark.parametrize(
    ("practice", "expected_note"),
    (
        (object(), "not a BlackPractice"),
        (
            BlackPractice("blank", " ", "wire", frozenset({"research"}), ("alpha",)),
            "blank or non-text",
        ),
        ((DEMO, DEMO), "duplicate id"),
        (
            BlackPractice(
                "bad-evidence", "title", "wire", frozenset({"research"}), ["alpha"]
            ),
            "malformed required evidence",
        ),
        (
            BrokenCanonicalPractice(
                "broken", "title", "wire", frozenset({"research"}), ("alpha",)
            ),
            "could not be digested",
        ),
    ),
)
def test_custom_registry_failures_are_blocking(
    practice: object, expected_note: str
) -> None:
    records = practice if isinstance(practice, tuple) else (practice,)
    assessment = evaluate_work(WorkAttempt("work", RESEARCH), records)  # type: ignore[arg-type]
    assert assessment.status is AssessmentStatus.NEEDS_REWORK
    assert assessment.findings == ()
    assert any(expected_note in note for note in assessment.intake_notes)


def test_non_iterable_practice_registry_is_rejected() -> None:
    with pytest.raises(TypeError, match="iterable"):
        evaluate_work(WorkAttempt("work", RESEARCH), None)  # type: ignore[arg-type]
