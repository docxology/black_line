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
from dataclasses import dataclass
from datetime import date

from .evaluator import evaluate_work
from .model import (
    AssessmentStatus,
    BlackAssessment,
    BlackPractice,
    PracticeStatus,
    WorkAttempt,
)
from .registry import BLACK_PRACTICES

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
    when a finding's practice id is not in the supplied registry), exposing
    where declaration gaps concentrate. Counts summarize declaration
    coverage; they are not a quality ranking of the assessed work.
    """

    total: int
    status_counts: tuple[tuple[str, int], ...]
    open_finding_kind_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class RefreshHorizonItem:
    """One dated evidence label and its remaining days before staleness.

    ``practice_ids`` names, in registry declaration order, the practices whose
    required evidence includes this label — the reason refreshing it can move a
    status at all.
    """

    label: str
    noted_on: str
    days_until_stale: int
    practice_ids: tuple[str, ...] = ()


#: Why a dated declaration is absent from a refresh horizon. Each reason is a
#: statement about the declaration, never about the underlying observation.
OMISSION_UNDATED = "undated: treated as current, so it has no boundary to reach"
OMISSION_STALE = "already stale: past the window, so it is a refresh request now"
OMISSION_UNREQUIRED = "not required by this registry: refreshing it moves no status"
OMISSION_FUTURE = (
    "dated in the future: the evaluator never counts it, so there is no "
    "boundary to reach until its date is corrected"
)
OMISSION_UNREADABLE = (
    "unreadable date: not an ISO date the evaluator can count, so it has no "
    "position on the schedule until its date is corrected"
)


@dataclass(frozen=True)
class OmittedEvidence:
    """One dated declaration the refresh horizon leaves out, and why."""

    label: str
    reason: str


def _required_label_practices(
    practices: Iterable[BlackPractice],
) -> dict[str, tuple[str, ...]]:
    """Map each required evidence label to the practices that require it."""

    index: dict[str, list[str]] = {}
    for practice in practices:
        for label in practice.required_evidence:
            index.setdefault(label, []).append(practice.id)
    return {label: tuple(ids) for label, ids in index.items()}


def refresh_horizon(
    attempt: WorkAttempt,
    *,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    as_of: str | date,
    max_evidence_age_days: int,
) -> tuple[RefreshHorizonItem, ...]:
    """List dated evidence labels nearest to the freshness window.

    Each item is derived from the attempt's dated evidence, the review date,
    and the supplied registry. Three classes of declaration are omitted, and
    :func:`refresh_horizon_omissions` names each one: undated items (which are
    treated as current and so have no boundary), already-stale items (which are
    a refresh request rather than a schedule), and labels no practice in
    ``practices`` requires (refreshing them cannot move any status), and
    declarations the evaluator itself never counts — future-dated or
    unreadable dates. The result is sorted by ascending ``days_until_stale``,
    then by label. This is a
    read-only scheduling view — it does not verify that the underlying
    observation exists or remains adequate.
    """

    review = as_of if isinstance(as_of, date) else date.fromisoformat(str(as_of))
    required = _required_label_practices(practices)
    items: list[RefreshHorizonItem] = []
    for item in attempt.dated_evidence:
        if item.noted_on is None:
            continue
        practice_ids = required.get(item.label)
        if not practice_ids:
            continue
        try:
            noted = date.fromisoformat(item.noted_on)
        except (TypeError, ValueError):
            continue
        if noted > review:
            continue
        remaining = max_evidence_age_days - (review - noted).days
        if remaining < 0:
            continue
        items.append(
            RefreshHorizonItem(
                label=item.label,
                noted_on=item.noted_on,
                days_until_stale=remaining,
                practice_ids=practice_ids,
            )
        )
    return tuple(sorted(items, key=lambda row: (row.days_until_stale, row.label)))


def refresh_horizon_omissions(
    attempt: WorkAttempt,
    *,
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
    as_of: str | date,
    max_evidence_age_days: int,
) -> tuple[OmittedEvidence, ...]:
    """Name every dated declaration :func:`refresh_horizon` leaves out.

    The omission rules live once, here and in :func:`refresh_horizon`, so a
    reader or a figure can show what the schedule does not cover instead of
    inferring it. Rows are sorted by label; the first applicable reason wins.
    Like the evaluator, the omissions never comment on whether the underlying
    observation exists — only on the shape and reachability of the declaration.
    """

    review = as_of if isinstance(as_of, date) else date.fromisoformat(str(as_of))
    required = _required_label_practices(practices)
    omitted: list[OmittedEvidence] = []
    for item in attempt.dated_evidence:
        if item.noted_on is None:
            omitted.append(OmittedEvidence(item.label, OMISSION_UNDATED))
            continue
        if item.label not in required:
            omitted.append(OmittedEvidence(item.label, OMISSION_UNREQUIRED))
            continue
        try:
            noted = date.fromisoformat(item.noted_on)
        except (TypeError, ValueError):
            omitted.append(OmittedEvidence(item.label, OMISSION_UNREADABLE))
            continue
        if noted > review:
            omitted.append(OmittedEvidence(item.label, OMISSION_FUTURE))
            continue
        if max_evidence_age_days - (review - noted).days < 0:
            omitted.append(OmittedEvidence(item.label, OMISSION_STALE))
    return tuple(sorted(omitted, key=lambda row: (row.label, row.reason)))


def summarize_assessments(
    assessments: Iterable[BlackAssessment],
    practices: Iterable[BlackPractice] = BLACK_PRACTICES,
) -> AssessmentSummary:
    """Summarize a batch of assessments for review reporting.

    Pure aggregation over already-computed assessments: statuses are counted
    per :class:`AssessmentStatus`, and every finding whose status is not
    ``ALIGNED`` is attributed to its practice's craft family via the supplied
    registry. The summary is a reviewer's map of open declaration gaps — it
    does not certify any work and grants nothing.
    """

    batch = tuple(assessments)
    kind_by_id = {practice.id: practice.kind.value for practice in practices}
    status_totals = {status: 0 for status in AssessmentStatus}
    kind_totals: dict[str, int] = {}
    for assessment in batch:
        status_totals[assessment.status] += 1
        for finding in assessment.findings:
            if finding.status is PracticeStatus.ALIGNED:
                continue
            kind = kind_by_id.get(finding.practice_id, "UNKNOWN")
            kind_totals[kind] = kind_totals.get(kind, 0) + 1
    return AssessmentSummary(
        total=len(batch),
        status_counts=tuple(
            (status.value, status_totals[status]) for status in AssessmentStatus
        ),
        open_finding_kind_counts=tuple(sorted(kind_totals.items())),
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
