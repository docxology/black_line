"""Frozen record types for practices, work attempts, and assessments."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import AssessmentStatus, PracticeKind, PracticeStatus


@dataclass(frozen=True)
class BlackPractice:
    """A positive wire: a practice, its tags, and required evidence labels.

    ``kind`` groups the practice into a craft family so registry balance can
    be reviewed; it defaults to ``METHOD`` for backward compatibility with
    pre-0.2 positional construction.
    """

    id: str
    title: str
    wire: str
    tags: frozenset[str]
    required_evidence: tuple[str, ...]
    kind: PracticeKind = PracticeKind.METHOD

    def canonical(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "wire": self.wire,
            "tags": sorted(self.tags),
            "required_evidence": list(self.required_evidence),
            "kind": self.kind.value,
        }


@dataclass(frozen=True)
class EvidenceItem:
    """A dated declaration pointing to an evidence observation.

    ``noted_on`` is an ISO date string recording when the observation was last
    recorded for review. Undated items (``noted_on is None``) are treated as
    current declarations; the evaluator does not independently verify them.
    """

    label: str
    noted_on: str | None = None


@dataclass(frozen=True)
class WorkAttempt:
    """A self-declared work item assessed against Black practices.

    ``evidence`` is the original undated label set; ``dated_evidence`` is the
    additive 0.2 surface for declarations whose observations should age.
    """

    description: str
    tags: frozenset[str] = frozenset()
    evidence: frozenset[str] = frozenset()
    dated_evidence: tuple[EvidenceItem, ...] = ()


@dataclass(frozen=True)
class PracticeFinding:
    """One practice-level declaration status with a reviewable reason trail."""

    practice_id: str
    status: PracticeStatus
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceSurfaces:
    """One practice's support and resistance, co-present and typed.

    A finding's status is a projection: precedence selects the most demanding
    reading for action. The surfaces keep what the projection compresses —
    the required labels that were declared fresh (``present``), the required
    labels that were not (``missing``), and the subset of the missing that is
    merely stale (``stale``) — so strong support and strong resistance on the
    same practice stay readable together instead of collapsing into one word.
    All three tuples follow the practice's declared evidence order, and
    ``stale`` is always a subset of ``missing``. Like the finding, the
    surfaces describe declaration coverage only; a present label is a
    declaration, never verified evidence.
    """

    practice_id: str
    present: tuple[str, ...]
    missing: tuple[str, ...]
    stale: tuple[str, ...]


@dataclass(frozen=True)
class BlackAssessment:
    """A complete assessment, including the practices that applied.

    ``intake_notes`` records normalization and intake observations (malformed
    labels, unreadable dates, blocking description defects).
    ``evaluated_as_of`` is the ISO review date the evaluation used, and
    ``registry_digest`` pins the exact practice content that produced the
    assessment. These are additive fields with defaults so pre-0.2
    constructions keep working.
    """

    status: AssessmentStatus
    findings: tuple[PracticeFinding, ...]
    intake_notes: tuple[str, ...] = ()
    evaluated_as_of: str = ""
    registry_digest: str = ""
