"""Deterministic analytics over the registry and evaluator surfaces.

Every function here is pure: it consumes the existing frozen record types
(:class:`~black_line.model.BlackPractice`, :class:`~black_line.model.WorkAttempt`,
:class:`~black_line.model.BlackAssessment`), performs no I/O, and returns
frozen, ordered structures so downstream figures and prose can cite exact
numbers reproducibly.

The no-authority boundary applies throughout: coverage counts, staleness
sweeps, and status summaries describe *declaration coverage* under the
registry's tag contract. None of them verify that a source is real, a test
passed, or a claim is true, and none of them grant safety, accreditation, or
permission for anything.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from .evaluator import evaluate_work, evaluate_with_surfaces
from .intake import clean_labels, dated_intake, resolve_max_age, resolve_review_date
from .model import (
    AssessmentStatus,
    BlackAssessment,
    BlackPractice,
    EvidenceSurfaces,
    PracticeStatus,
    WorkAttempt,
)
from .registry import BLACK_PRACTICES
from .serialization import registry_digest

#: Assessment statuses ordered from least to most complete declaration
#: coverage. ``OUTSIDE_SCOPE`` is deliberately absent: it is a statement about
#: tag coverage, not a rung on the declaration-coverage ladder.
DECLARATION_STATUS_ORDER: tuple[AssessmentStatus, ...] = (
    AssessmentStatus.NEEDS_REWORK,
    AssessmentStatus.NEEDS_EVIDENCE,
    AssessmentStatus.ALIGNED,
)

_STATUS_RANK: dict[AssessmentStatus, int] = {
    status: rank for rank, status in enumerate(DECLARATION_STATUS_ORDER)
}


@dataclass(frozen=True)
class TagCoverage:
    """Declaration reach of one tag: which practices it selects and at what cost.

    ``practice_ids`` preserves registry declaration order.
    ``required_label_count`` is the total number of required evidence labels a
    work attempt declaring only this tag would be scored against — the tag's
    declaration burden, not a measure of work quality.
    """

    tag: str
    practice_ids: tuple[str, ...]
    required_label_count: int

    @property
    def practice_count(self) -> int:
        """Number of practices this tag reaches."""

        return len(self.practice_ids)


def coverage_matrix(
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
) -> tuple[TagCoverage, ...]:
    """Compute the tag-by-practice coverage of a practice registry.

    Returns one :class:`TagCoverage` row per tag (tags sorted alphabetically;
    the tag set is the union of the practices' declared tags). The rows expose
    the registry's coverage asymmetry — how many practices, and how many
    required labels, each tag choice commits a declarer to. The matrix
    describes applicability only; it is not a score of any work attempt.
    """

    practice_set = tuple(practices)
    tags = sorted({tag for practice in practice_set for tag in practice.tags})
    rows = []
    for tag in tags:
        reached = tuple(p for p in practice_set if tag in p.tags)
        rows.append(
            TagCoverage(
                tag=tag,
                practice_ids=tuple(p.id for p in reached),
                required_label_count=sum(len(p.required_evidence) for p in reached),
            )
        )
    return tuple(rows)


@dataclass(frozen=True)
class StalenessPoint:
    """The assessment status observed under one freshness-window setting."""

    max_evidence_age_days: int | None
    status: AssessmentStatus


def staleness_profile(
    attempt: WorkAttempt,
    windows: Sequence[int | None],
    *,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    as_of: str | date | None = None,
) -> tuple[StalenessPoint, ...]:
    """Sweep one work attempt across freshness windows via the real evaluator.

    Each point is produced by an ordinary :func:`~black_line.evaluate_work`
    call with ``max_evidence_age_days`` set to that window (``None`` disables
    staleness). This is a simulation over the public API — no evaluator
    semantics are duplicated here — so the profile inherits the evaluator's
    strict-inequality rule: evidence aged exactly ``window`` days is still
    fresh; one day older is stale. The resulting statuses report declaration
    freshness only, never the adequacy of the underlying artifacts.
    """

    practice_set = tuple(practices)
    return tuple(
        StalenessPoint(
            max_evidence_age_days=window,
            status=evaluate_work(
                attempt,
                practice_set,
                as_of=as_of,
                max_evidence_age_days=window,
            ).status,
        )
        for window in windows
    )


@dataclass(frozen=True)
class AssessmentSummary:
    """Distributional counts for a batch of assessments.

    ``status_counts`` covers every :class:`AssessmentStatus` in enum order,
    including zero counts, so batch reports are shaped identically regardless
    of the batch. ``open_finding_kind_counts`` counts non-``ALIGNED``
    practice findings by craft family (``PracticeKind`` value; ``"UNKNOWN"``
    when its method digest is unresolved or its id is absent), exposing
    where declaration gaps concentrate. Counts summarize declaration
    coverage; they are not a quality ranking of the assessed work.
    """

    total: int
    status_counts: tuple[tuple[str, int], ...]
    open_finding_kind_counts: tuple[tuple[str, int], ...]
    registry_partitions: tuple[RegistrySummary, ...] = ()


@dataclass(frozen=True)
class RegistrySummary:
    registry_digest: str
    total: int
    open_finding_kind_counts: tuple[tuple[str, int], ...]
    attribution_available: bool


@dataclass(frozen=True)
class RefreshHorizonItem:
    label: str
    noted_on: str
    days_until_stale: int
    practice_ids: tuple[str, ...] = ()
    last_fresh_on: str = ""
    stale_on: str = ""
    occurrence_index: int = field(default=-1, compare=False)
    raw_label: object = field(default=None, compare=False)
    transitions: tuple[tuple[EvidenceSurfaces, EvidenceSurfaces], ...] = ()

    @property
    def days_until_last_fresh_day(self) -> int:
        return self.days_until_stale - 1


OMISSION_UNDATED = "undated: treated as current, so it has no boundary to reach"
OMISSION_STALE = "already stale: past the window, so it is a refresh request now"
OMISSION_UNREQUIRED = "not required by this registry: no required-label expiry"
OMISSION_FUTURE = "dated in the future: not counted at this review date"
OMISSION_UNREADABLE = "unreadable date: not an ISO date the evaluator can count"
OMISSION_MALFORMED = "malformed declaration: no usable dated label"
OMISSION_DISABLED = "expiry disabled: max_evidence_age_days is None"


@dataclass(frozen=True)
class OmittedEvidence:
    label: str
    reason: str
    occurrence_index: int = field(default=-1, compare=False)
    raw_label: object = field(default=None, compare=False)


@dataclass(frozen=True)
class RefreshQueue:
    items: tuple[RefreshHorizonItem, ...]
    omissions: tuple[OmittedEvidence, ...]


def _required_label_practices(
    practices: Iterable[BlackPractice],
) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    for practice in practices:
        for label in practice.required_evidence:
            index.setdefault(label, []).append(practice.id)
    return {label: tuple(ids) for label, ids in index.items()}


def _refresh_inventory(
    attempt, practices, as_of, max_evidence_age_days
) -> RefreshQueue:
    review = resolve_review_date(as_of)
    window = resolve_max_age(max_evidence_age_days)
    required = _required_label_practices(practices)
    items = []
    omissions = []
    reasons = {
        "undated": OMISSION_UNDATED,
        "stale": OMISSION_STALE,
        "future": OMISSION_FUTURE,
        "unreadable": OMISSION_UNREADABLE,
        "malformed_label": OMISSION_MALFORMED,
        "malformed_collection": OMISSION_MALFORMED,
    }
    for row in dated_intake(getattr(attempt, "dated_evidence", ()), review, window):
        reason = reasons.get(row.category)
        if reason is None and row.label not in required:
            reason = OMISSION_UNREQUIRED
        if reason is None and window is None:
            reason = OMISSION_DISABLED
        if reason is not None:
            omissions.append(
                OmittedEvidence(row.label, reason, row.occurrence_index, row.raw_label)
            )
            continue
        assert row.noted is not None and window is not None
        if window >= (date.max - row.noted).days:
            omissions.append(
                OmittedEvidence(
                    row.label,
                    "expiry_out_of_calendar_range",
                    row.occurrence_index,
                    row.raw_label,
                )
            )
            continue
        last_fresh = row.noted + timedelta(days=window)
        first_stale = last_fresh + timedelta(days=1)
        items.append(
            RefreshHorizonItem(
                row.label,
                row.noted.isoformat(),
                (first_stale - review).days,
                required[row.label],
                last_fresh.isoformat(),
                first_stale.isoformat(),
                row.occurrence_index,
                row.raw_label,
            )
        )
    return RefreshQueue(
        tuple(sorted(items, key=lambda row: (row.days_until_stale, row.label))),
        tuple(sorted(omissions, key=lambda row: (row.label, row.reason))),
    )


def refresh_horizon(
    attempt: WorkAttempt,
    *,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    as_of: str | date,
    max_evidence_age_days: int | None,
) -> tuple[RefreshHorizonItem, ...]:
    return _refresh_inventory(attempt, practices, as_of, max_evidence_age_days).items


def refresh_horizon_omissions(
    attempt: WorkAttempt,
    *,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    as_of: str | date,
    max_evidence_age_days: int | None,
) -> tuple[OmittedEvidence, ...]:
    return _refresh_inventory(
        attempt, practices, as_of, max_evidence_age_days
    ).omissions


def effective_refresh_queue(
    attempt: WorkAttempt,
    *,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    as_of: str | date,
    max_evidence_age_days: int | None,
) -> RefreshQueue:
    practice_set = tuple(practices)
    inventory = _refresh_inventory(attempt, practice_set, as_of, max_evidence_age_days)
    tags, _ = clean_labels(getattr(attempt, "tags", None), "tag")
    applicable = _required_label_practices(p for p in practice_set if p.tags & tags)
    declared, _ = clean_labels(getattr(attempt, "evidence", None), "evidence")
    occurrences = dated_intake(
        getattr(attempt, "dated_evidence", ()),
        resolve_review_date(as_of),
        resolve_max_age(max_evidence_age_days),
    )
    undated = declared | frozenset(
        row.label for row in occurrences if row.category == "undated"
    )
    kept = []
    omitted = list(inventory.omissions)
    for row in inventory.items:
        reason = None
        if row.label not in applicable:
            reason = "non_applicable"
        elif row.label in undated:
            reason = "shadowed_by_undated"
        elif any(
            other.label == row.label and other.noted_on > row.noted_on
            for other in inventory.items
        ):
            reason = "superseded_by_newer_declaration"
        if reason is not None:
            omitted.append(
                OmittedEvidence(row.label, reason, row.occurrence_index, row.raw_label)
            )
            continue
        before = evaluate_with_surfaces(
            attempt,
            practice_set,
            as_of=row.last_fresh_on,
            max_evidence_age_days=max_evidence_age_days,
        )[1]
        after = evaluate_with_surfaces(
            attempt,
            practice_set,
            as_of=row.stale_on,
            max_evidence_age_days=max_evidence_age_days,
        )[1]
        transitions = tuple(
            (a, b)
            for a, b in zip(before, after)
            if row.label in a.present and row.label in b.missing
        )
        if not transitions:
            omitted.append(
                OmittedEvidence(
                    row.label,
                    "no_predicted_surface_change",
                    row.occurrence_index,
                    row.raw_label,
                )
            )
            continue
        kept.append(
            replace(
                row,
                practice_ids=tuple(a.practice_id for a, _ in transitions),
                transitions=transitions,
            )
        )
    return RefreshQueue(tuple(kept), tuple(omitted))


def summarize_assessments(
    assessments: Iterable[BlackAssessment],
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
) -> AssessmentSummary:
    """Summarize a batch of assessments for review reporting.

    Pure aggregation over already-computed assessments: statuses are counted
    per :class:`AssessmentStatus`, and every finding whose status is not
    ``ALIGNED`` is attributed via a matching registry digest, otherwise UNKNOWN.
    Digest partitions preserve unresolved method provenance. The summary is a reviewer's map of open declaration gaps — it
    does not certify any work and grants nothing.
    """

    batch = tuple(assessments)
    practice_set = tuple(practices)
    method_digest = registry_digest(practice_set)
    kind_by_id = {practice.id: practice.kind.value for practice in practice_set}
    status_totals = {status: 0 for status in AssessmentStatus}
    kind_totals: dict[str, int] = {}
    partitions: dict[str, dict[str, int]] = {}
    partition_totals: dict[str, int] = {}
    for assessment in batch:
        status_totals[assessment.status] += 1
        digest = assessment.registry_digest
        counts = partitions.setdefault(digest, {})
        partition_totals[digest] = partition_totals.get(digest, 0) + 1
        for finding in assessment.findings:
            if finding.status is PracticeStatus.ALIGNED:
                continue
            kind = (
                kind_by_id.get(finding.practice_id, "UNKNOWN")
                if digest == method_digest
                else "UNKNOWN"
            )
            kind_totals[kind] = kind_totals.get(kind, 0) + 1
            counts[kind] = counts.get(kind, 0) + 1
    return AssessmentSummary(
        total=len(batch),
        status_counts=tuple(
            (status.value, status_totals[status]) for status in AssessmentStatus
        ),
        open_finding_kind_counts=tuple(sorted(kind_totals.items())),
        registry_partitions=tuple(
            RegistrySummary(
                digest,
                partition_totals[digest],
                tuple(sorted(counts.items())),
                digest == method_digest and "UNKNOWN" not in counts,
            )
            for digest, counts in sorted(partitions.items())
        ),
    )


def status_rank(status: AssessmentStatus) -> int:
    """Rank a status on the declaration-coverage ladder (higher is more covered).

    Raises :class:`ValueError` for ``OUTSIDE_SCOPE``: an outside-scope
    assessment says no practice applied, so it has no position on the
    coverage ladder and must not be compared as if it did.
    """

    try:
        return _STATUS_RANK[status]
    except KeyError as exc:
        raise ValueError(
            "OUTSIDE_SCOPE is a coverage statement, not a rung on the "
            "declaration-coverage ladder"
        ) from exc


def declaration_status_path(
    description: str,
    tags: Iterable[str],
    labels: Sequence[str],
    *,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    as_of: str | date | None = None,
    max_evidence_age_days: int | None = None,
) -> tuple[AssessmentStatus, ...]:
    """Evaluate the same attempt under incrementally growing declarations.

    Step ``k`` evaluates the attempt with evidence ``frozenset(labels[:k])``
    for ``k = 0 .. len(labels)``, each via the real evaluator, so the returned
    sequence has ``len(labels) + 1`` statuses. This is the executable form of
    the manuscript's transition narrative: the path starts at the
    empty-declaration boundary and traces how the status responds as fresh
    labels accumulate. The path describes declaration coverage only.
    """

    practice_set = tuple(practices)
    tag_set = frozenset(tags)
    return tuple(
        evaluate_work(
            WorkAttempt(description, tag_set, frozenset(labels[:step])),
            practice_set,
            as_of=as_of,
            max_evidence_age_days=max_evidence_age_days,
        ).status
        for step in range(len(labels) + 1)
    )


def no_status_regression(statuses: Sequence[AssessmentStatus]) -> bool:
    """Check that declaration-coverage rank never decreases along a sequence.

    This is the executable form of the conditional-monotonicity proposition
    (`prop:fresh-monotonicity` in the manuscript):
    it should hold for any :func:`declaration_status_path` segment that starts
    *after* a non-empty declaration exists, and it intentionally fails across
    the empty-declaration boundary (``NEEDS_EVIDENCE`` to ``NEEDS_REWORK``),
    which the evaluator treats as a more specific request, not a regression
    in the work. A ``True`` result is a statement about status ordering
    only — it does not validate the declared evidence.

    Raises:
        ValueError: if the sequence contains ``OUTSIDE_SCOPE``, which
            :func:`status_rank` refuses to place on the ladder. A mixed batch
            must be partitioned before it is checked for regression.
    """

    ranks = [status_rank(status) for status in statuses]
    return all(later >= earlier for earlier, later in zip(ranks, ranks[1:]))
