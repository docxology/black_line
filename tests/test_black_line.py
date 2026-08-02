"""Public-surface tests for the default evaluate_work call forms.

These exercise the positional and keyword forms callers use against the
live registry.
"""

from black_line import (
    AssessmentStatus,
    BLACK_PRACTICES,
    PracticeStatus,
    WorkAttempt,
    evaluate_work,
    registry_digest,
    registry_ids,
)


def test_registry_is_unique_and_digest_is_stable() -> None:
    assert len(registry_ids()) == len(set(registry_ids())) == len(BLACK_PRACTICES)
    assert registry_digest(BLACK_PRACTICES) == registry_digest(
        tuple(reversed(BLACK_PRACTICES))
    )


def test_outside_scope_has_no_findings() -> None:
    assessment = evaluate_work(WorkAttempt("a personal note", frozenset({"music"})))
    assert assessment.status is AssessmentStatus.OUTSIDE_SCOPE
    assert assessment.findings == ()


def test_missing_evidence_is_distinguished_from_rework() -> None:
    missing = evaluate_work(WorkAttempt("research", frozenset({"research"})))
    assert missing.status is AssessmentStatus.NEEDS_EVIDENCE
    assert all(
        item.status is PracticeStatus.NEEDS_EVIDENCE for item in missing.findings
    )

    rework = evaluate_work(
        WorkAttempt(
            "research", frozenset({"research"}), frozenset({"question", "scope"})
        )
    )
    assert rework.status is AssessmentStatus.NEEDS_REWORK
    assert any(item.status is PracticeStatus.NEEDS_REWORK for item in rework.findings)


def test_complete_evidence_is_aligned() -> None:
    tags = frozenset({"research", "engineering", "writing", "analysis", "data"})
    evidence = frozenset(
        label for practice in BLACK_PRACTICES for label in practice.required_evidence
    )
    assessment = evaluate_work(WorkAttempt("complete research", tags, evidence))
    assert assessment.status is AssessmentStatus.ALIGNED
    assert len(assessment.findings) == len(BLACK_PRACTICES)
    assert all(item.status is PracticeStatus.ALIGNED for item in assessment.findings)
