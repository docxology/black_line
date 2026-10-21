"""Staged evaluation of positive practice evidence.

Evaluation is deliberately staged: intake normalization runs first, so
hostile or malformed input (non-string labels, unreadable dates, a blank
description) is recorded in ``intake_notes`` instead of crashing or silently
passing. Only then are practices matched by tag and scored against the fresh
evidence set. The output describes declaration coverage and review gaps; it
never turns labels into truth, safety, or permission for anything.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from .intake import (
    resolve_review_date as _resolve_review_date,
    resolve_max_age as _resolve_max_age,
    clean_labels as _clean_labels,
    dated_labels as _dated_labels,
)

from .model import (
    AssessmentStatus,
    BlackAssessment,
    BlackPractice,
    EvidenceSurfaces,
    PracticeFinding,
    PracticeStatus,
    WorkAttempt,
)
from .registry import BLACK_PRACTICES
from .serialization import registry_digest
from .version import __version__
from .registry_validation import registry_defects


def _surfaces(
    practice: BlackPractice,
    fresh: frozenset[str],
    stale: frozenset[str],
) -> EvidenceSurfaces:
    """Split one practice's required labels into typed co-present surfaces.

    ``present`` and ``missing`` partition the practice's declared evidence
    order; ``stale`` is the subset of the missing that only needs a refresh.
    Status projects these surfaces plus attempt-wide evidence context.
    """

    present = tuple(item for item in practice.required_evidence if item in fresh)
    missing = tuple(item for item in practice.required_evidence if item not in fresh)
    stale_missing = tuple(item for item in missing if item in stale)
    return EvidenceSurfaces(practice.id, present, missing, stale_missing)


def project_finding(
    surfaces: EvidenceSurfaces,
    evidence_declared: bool,
) -> PracticeFinding:
    """Project one practice's surfaces onto a status with a reasons trail.

    Every finding carries a reasons trail naming what is present, what is
    missing, and what only needs a refresh — the same content the typed
    surfaces carry, rendered for a reader. The projection selects the most
    demanding reading; the surfaces preserve what it compresses.
    """

    if not evidence_declared:
        return PracticeFinding(
            surfaces.practice_id,
            PracticeStatus.NEEDS_EVIDENCE,
            ("no evidence was declared",),
        )
    if not surfaces.missing:
        return PracticeFinding(
            surfaces.practice_id,
            PracticeStatus.ALIGNED,
            ("required evidence is present: " + ", ".join(surfaces.present),),
        )
    reasons = ["required evidence is missing: " + ", ".join(surfaces.missing)]
    if surfaces.present:
        reasons.append("evidence already present: " + ", ".join(surfaces.present))
    if surfaces.stale:
        reasons.append("stale evidence needs refresh: " + ", ".join(surfaces.stale))
    status = (
        PracticeStatus.NEEDS_EVIDENCE
        if len(surfaces.stale) == len(surfaces.missing)
        else PracticeStatus.NEEDS_REWORK
    )
    return PracticeFinding(surfaces.practice_id, status, tuple(reasons))


def _overall(findings: tuple[PracticeFinding, ...]) -> AssessmentStatus:
    statuses = {finding.status for finding in findings}
    if PracticeStatus.NEEDS_REWORK in statuses:
        return AssessmentStatus.NEEDS_REWORK
    if PracticeStatus.NEEDS_EVIDENCE in statuses:
        return AssessmentStatus.NEEDS_EVIDENCE
    return AssessmentStatus.ALIGNED if findings else AssessmentStatus.OUTSIDE_SCOPE


def _evaluate(
    attempt: WorkAttempt,
    practices: Iterable[BlackPractice],
    as_of: str | date | None,
    max_evidence_age_days: int | None,
) -> tuple[BlackAssessment, tuple[EvidenceSurfaces, ...]]:
    """Run the staged evaluation once, returning the assessment and surfaces.

    This is the single implementation behind ``evaluate_work`` and
    ``evaluate_with_surfaces``: intake normalization, matching, and scoring
    happen here exactly once, and both public forms report the same staged
    computation. On a blocking intake defect or an unscorable registry there
    are no findings, so there are no surfaces either.
    """

    review_date = _resolve_review_date(as_of)
    max_age_days = _resolve_max_age(max_evidence_age_days)
    try:
        practice_set = tuple(practices)
    except TypeError as exc:
        raise TypeError(
            "practices must be an iterable of BlackPractice records"
        ) from exc
    notes: list[str] = []
    defects = registry_defects(practice_set)
    if defects:
        method_digest = ""
        notes.extend(
            f"practice registry is not safe to score and must be repaired: {defect.code}: {defect.detail}"
            for defect in defects
        )
    else:
        try:
            method_digest = registry_digest(practice_set)
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            method_digest = ""
            notes.append(
                f"practice registry could not be digested and must be repaired: {exc}"
            )
    if not method_digest:
        return (
            BlackAssessment(
                AssessmentStatus.NEEDS_REWORK,
                (),
                tuple(notes),
                review_date.isoformat(),
                method_digest,
                evaluator_version=__version__,
                intake_codes=tuple(defect.code for defect in defects)
                or ("registry_digest_failed",),
            ),
            (),
        )
    description = getattr(attempt, "description", None)
    blocking = not isinstance(description, str) or not description.strip()
    if blocking:
        notes.append(
            "work description is empty or not text; restate the work before assessment"
        )
    tags, tag_notes = _clean_labels(getattr(attempt, "tags", None), "tag")
    notes.extend(tag_notes)
    declared, evidence_notes = _clean_labels(
        getattr(attempt, "evidence", None), "evidence"
    )
    notes.extend(evidence_notes)
    fresh_dated, stale, dated_notes = _dated_labels(
        getattr(attempt, "dated_evidence", ()), review_date, max_age_days
    )
    notes.extend(dated_notes)
    if blocking:
        return (
            BlackAssessment(
                AssessmentStatus.NEEDS_REWORK,
                (),
                tuple(notes),
                review_date.isoformat(),
                method_digest,
                evaluator_version=__version__,
                intake_codes=("description_invalid",),
            ),
            (),
        )
    fresh = declared | fresh_dated
    evidence_declared = bool(fresh or stale)
    surfaces = tuple(
        _surfaces(practice, fresh, stale)
        for practice in practice_set
        if practice.tags & tags
    )
    findings = tuple(project_finding(item, evidence_declared) for item in surfaces)
    return (
        BlackAssessment(
            _overall(findings),
            findings,
            tuple(notes),
            review_date.isoformat(),
            method_digest,
            evaluator_version=__version__,
            evidence_declared=evidence_declared,
        ),
        surfaces,
    )


def evaluate_work(
    attempt: WorkAttempt,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    *,
    as_of: str | date | None = None,
    max_evidence_age_days: int | None = None,
) -> BlackAssessment:
    """Assess practices whose tags intersect the work attempt's declared tags.

    Pre-0.2 call forms (``evaluate_work(attempt)`` and
    ``evaluate_work(attempt, practices)``) behave as before. Additively:

    - ``as_of`` pins the review date (ISO string or :class:`datetime.date`);
      the default is today.
    - ``max_evidence_age_days`` enables staleness: dated evidence older than
      the window stops counting as fresh, and a finding whose only gaps are
      stale items is ``NEEDS_EVIDENCE`` (refresh), not ``NEEDS_REWORK``.
    - Invalid review configuration raises before scoring. A custom practice
      registry with malformed records fails closed as ``NEEDS_REWORK`` with no
      findings and an intake note.
    - A blank or non-text description is a blocking intake defect: the
      assessment is ``NEEDS_REWORK`` with no findings and an explanatory
      intake note, because no honest practice scoring is possible.
    """

    assessment, _surfaces_unused = _evaluate(
        attempt, practices, as_of, max_evidence_age_days
    )
    return assessment


def evaluate_with_surfaces(
    attempt: WorkAttempt,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    *,
    as_of: str | date | None = None,
    max_evidence_age_days: int | None = None,
) -> tuple[BlackAssessment, tuple[EvidenceSurfaces, ...]]:
    """Assess the attempt and also return each finding's typed surfaces.

    The assessment is exactly what ``evaluate_work`` returns for the same
    arguments — one shared staged implementation, not a second evaluator.
    The surfaces align one-to-one with ``assessment.findings`` and preserve
    what each status projection compresses: the practice's present, missing,
    and stale required labels as co-present typed data. Like the finding,
    they describe declaration coverage only — never quality, truth, safety,
    or permission.
    """

    return _evaluate(attempt, practices, as_of, max_evidence_age_days)
