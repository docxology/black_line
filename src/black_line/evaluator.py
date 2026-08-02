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
from datetime import date, datetime

from .model import (
    AssessmentStatus,
    BlackAssessment,
    BlackPractice,
    EvidenceSurfaces,
    PracticeFinding,
    PracticeKind,
    PracticeStatus,
    WorkAttempt,
)
from .registry import BLACK_PRACTICES
from .serialization import registry_digest


def _resolve_review_date(as_of: str | date | None) -> date:
    """Resolve the review date the staleness rules are anchored to."""

    if as_of is None:
        return date.today()
    if isinstance(as_of, str):
        try:
            return date.fromisoformat(as_of)
        except ValueError as exc:
            raise ValueError("as_of must be an ISO date in YYYY-MM-DD form") from exc
    if isinstance(as_of, datetime):
        raise TypeError("as_of must be None, an ISO date string, or a datetime.date")
    if isinstance(as_of, date):
        return as_of
    raise TypeError("as_of must be None, an ISO date string, or a datetime.date")


def _resolve_max_age(max_age_days: int | None) -> int | None:
    """Validate the optional freshness window before it changes scoring."""

    if max_age_days is None:
        return None
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int):
        raise TypeError("max_evidence_age_days must be a non-negative integer or None")
    if max_age_days < 0:
        raise ValueError("max_evidence_age_days must be non-negative")
    return max_age_days


def _registry_shape_error(practices: tuple[BlackPractice, ...]) -> str | None:
    """Return a blocking note when a custom registry cannot be safely scored."""

    seen_ids: set[str] = set()
    for index, practice in enumerate(practices):
        if not isinstance(practice, BlackPractice):
            return f"practice registry entry {index} is not a BlackPractice record"
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (practice.id, practice.title, practice.wire)
        ):
            return f"practice registry entry {index} has blank or non-text fields"
        if practice.id in seen_ids:
            return f"practice registry contains duplicate id '{practice.id}'"
        seen_ids.add(practice.id)
        if (
            not isinstance(practice.tags, frozenset)
            or not practice.tags
            or any(not isinstance(tag, str) or not tag.strip() for tag in practice.tags)
        ):
            return f"practice '{practice.id}' has malformed tags"
        if (
            not isinstance(practice.required_evidence, tuple)
            or not practice.required_evidence
            or any(
                not isinstance(label, str) or not label.strip()
                for label in practice.required_evidence
            )
        ):
            return f"practice '{practice.id}' has malformed required evidence"
        if not isinstance(practice.kind, PracticeKind):
            return f"practice '{practice.id}' has an invalid kind"
    return None


def _clean_labels(raw: object, field: str) -> tuple[frozenset[str], tuple[str, ...]]:
    """Normalize a declared label collection without letting bad input crash.

    Returns the kept labels (stripped, lowercased) and intake notes for every
    declaration or token that had to be ignored.
    """

    if isinstance(raw, str) or not isinstance(raw, Iterable):
        return frozenset(), (
            f"{field} declaration is not a collection of labels and was ignored",
        )
    kept: set[str] = set()
    notes: list[str] = []
    for token in raw:
        if not isinstance(token, str) or not token.strip():
            notes.append(f"ignored a malformed {field} label")
            continue
        kept.add(token.strip().lower())
    return frozenset(kept), tuple(notes)


def _dated_labels(
    records: object,
    review_date: date,
    max_age_days: int | None,
) -> tuple[frozenset[str], frozenset[str], tuple[str, ...]]:
    """Split dated evidence into fresh labels, stale labels, and intake notes.

    Undated records count as fresh. Future-dated or unreadable dates are
    never counted; they are surfaced as notes so the declarer can fix them.
    """

    if isinstance(records, str) or not isinstance(records, Iterable):
        return (
            frozenset(),
            frozenset(),
            ("dated evidence declaration is not a collection of records",),
        )
    fresh: set[str] = set()
    stale: set[str] = set()
    notes: list[str] = []
    for item in records:
        raw_label = getattr(item, "label", None)
        if not isinstance(raw_label, str) or not raw_label.strip():
            notes.append("ignored a dated evidence record without a usable label")
            continue
        label = raw_label.strip().lower()
        noted_on = getattr(item, "noted_on", None)
        if noted_on is None:
            fresh.add(label)
            continue
        try:
            noted = date.fromisoformat(noted_on)
        except (TypeError, ValueError):
            notes.append(
                f"evidence '{label}' has an unreadable date and was not counted"
            )
            continue
        if noted > review_date:
            notes.append(
                f"evidence '{label}' is dated in the future and was not counted"
            )
            continue
        if max_age_days is not None and (review_date - noted).days > max_age_days:
            stale.add(label)
            continue
        fresh.add(label)
    return frozenset(fresh), frozenset(stale), tuple(notes)


def _surfaces(
    practice: BlackPractice,
    fresh: frozenset[str],
    stale: frozenset[str],
) -> EvidenceSurfaces:
    """Split one practice's required labels into typed co-present surfaces.

    ``present`` and ``missing`` partition the practice's declared evidence
    order; ``stale`` is the subset of the missing that only needs a refresh.
    The surfaces are the state the finding's status projects from.
    """

    present = tuple(item for item in practice.required_evidence if item in fresh)
    missing = tuple(item for item in practice.required_evidence if item not in fresh)
    stale_missing = tuple(item for item in missing if item in stale)
    return EvidenceSurfaces(practice.id, present, missing, stale_missing)


def _finding(
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
    shape_error = _registry_shape_error(practice_set)
    if shape_error:
        method_digest = ""
        notes.append(
            f"practice registry is not safe to score and must be repaired: {shape_error}"
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
    findings = tuple(_finding(item, evidence_declared) for item in surfaces)
    return (
        BlackAssessment(
            _overall(findings),
            findings,
            tuple(notes),
            review_date.isoformat(),
            method_digest,
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
