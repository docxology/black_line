"""Public surface and alias-module tests."""

import dataclasses

import black_line
from black_line import (
    AssessmentStatus,
    BlackAssessment,
    PracticeFinding,
    PracticeStatus,
    WorkAttempt,
    evaluate_work,
)


def test_every_declared_export_resolves() -> None:
    for name in black_line.__all__:
        assert getattr(black_line, name) is not None, name


def test_version_marker_is_a_string() -> None:
    assert isinstance(black_line.__version__, str)
    assert black_line.__version__


def test_models_module_is_a_public_alias() -> None:
    from black_line import models

    assert models.BlackPractice is black_line.BlackPractice
    assert models.WorkAttempt is black_line.WorkAttempt
    assert models.PracticeKind is black_line.PracticeKind


def test_positional_evaluate_work_call_form() -> None:
    attempt = WorkAttempt(
        "research", frozenset({"research"}), frozenset({"question", "scope"})
    )
    assessment = evaluate_work(attempt, black_line.BLACK_PRACTICES)
    assert assessment.status is AssessmentStatus.NEEDS_REWORK


def test_assessment_defaults_on_direct_construction() -> None:
    finding = PracticeFinding("x", PracticeStatus.ALIGNED, ("ok",))
    assessment = BlackAssessment(AssessmentStatus.ALIGNED, (finding,))
    assert assessment.intake_notes == ()
    assert assessment.evaluated_as_of == ""


def test_practice_canonical_form_contains_all_fields() -> None:
    """Bound to the record's own fields, not to a hand-copied key list.

    Proposition 9 claims that editing *any* practice field changes the digest.
    Pinning a literal key set cannot see a seventh field added to
    ``BlackPractice`` and forgotten in ``canonical()`` — that edit would leave
    the digest identical and the proposition false with the suite still green.
    """

    canonical = black_line.BLACK_PRACTICES[0].canonical()
    assert set(canonical) == {
        field.name for field in dataclasses.fields(black_line.BlackPractice)
    }


def test_the_canonical_field_check_can_fail() -> None:
    """Positive control: a record with an unserialized field must be rejected."""

    @dataclasses.dataclass(frozen=True)
    class WiderPractice(black_line.BlackPractice):
        owner: str = ""

    canonical = black_line.BLACK_PRACTICES[0].canonical()
    assert set(canonical) != {field.name for field in dataclasses.fields(WiderPractice)}
