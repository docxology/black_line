from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date

from .envelope import (
    SCOPE_AND_NONCLAIMS,
    AssessmentEnvelope,
    envelope_matches_assessment,
    source_references,
    validate_envelope_contract,
)
from .evaluator import evaluate_with_surfaces
from .intake import clean_labels, dated_labels, resolve_max_age, resolve_review_date
from .model import (
    AssessmentStatus,
    BlackAssessment,
    BlackPractice,
    EvidenceItem,
    EvidenceSurfaces,
    PracticeFinding,
    PracticeKind,
    PracticeStatus,
    WorkAttempt,
)
from .registry import BLACK_PRACTICES
from .registry_validation import registry_defects
from .serialization import canonical_assessment, registry_digest
from .version import __version__

REPLAY_SCHEMA = "black_line.evaluation-record/1.0"


@dataclass(frozen=True)
class EvaluationRecord:
    attempt: WorkAttempt
    as_of: str
    max_evidence_age_days: int | None
    evaluator_version: str
    registry: tuple[BlackPractice, ...]
    registry_digest: str
    assessment: BlackAssessment
    surfaces: tuple[EvidenceSurfaces, ...]
    normalized_tags: frozenset[str]
    fresh_labels: frozenset[str]
    stale_labels: frozenset[str]
    evidence_declared: bool
    subject_id: str = ""
    source_snapshot_refs: tuple[str, ...] = ()
    scope_and_nonclaims: tuple[str, ...] = SCOPE_AND_NONCLAIMS


def _supported_attempt(attempt: WorkAttempt) -> None:
    if not isinstance(attempt, WorkAttempt) or not isinstance(attempt.description, str):
        raise TypeError(
            "supported replay intake requires a WorkAttempt with text description"
        )
    for labels in (attempt.tags, attempt.evidence):
        if not isinstance(labels, frozenset) or not all(
            isinstance(label, str) for label in labels
        ):
            raise TypeError("supported replay labels must be frozensets of text")
    if not isinstance(attempt.dated_evidence, tuple) or any(
        not isinstance(item, EvidenceItem)
        or not isinstance(item.label, str)
        or (item.noted_on is not None and not isinstance(item.noted_on, str))
        for item in attempt.dated_evidence
    ):
        raise TypeError(
            "supported replay dates require a tuple of EvidenceItem text/None records"
        )


def evaluation_record(
    attempt: WorkAttempt,
    practices=BLACK_PRACTICES,
    *,
    as_of: str | date,
    max_evidence_age_days: int | None = None,
    subject_id: str = "",
    source_snapshot_refs=(),
) -> EvaluationRecord:
    _supported_attempt(attempt)
    if not isinstance(subject_id, str):
        raise TypeError("subject_id must be text")
    refs = source_references(source_snapshot_refs)
    review = resolve_review_date(as_of)
    window = resolve_max_age(max_evidence_age_days)
    registry = tuple(practices)
    assessment, surfaces = evaluate_with_surfaces(
        attempt, registry, as_of=review, max_evidence_age_days=window
    )
    if not assessment.registry_digest:
        raise ValueError("replay requires a structurally valid, recoverable registry")
    tags, _ = clean_labels(attempt.tags, "tag")
    declared, _ = clean_labels(attempt.evidence, "evidence")
    dated, stale, _ = dated_labels(attempt.dated_evidence, review, window)
    fresh = declared | dated
    return EvaluationRecord(
        attempt,
        review.isoformat(),
        window,
        __version__,
        registry,
        assessment.registry_digest,
        assessment,
        surfaces,
        tags,
        fresh,
        stale,
        bool(fresh or stale),
        subject_id,
        refs,
    )


def _payload(record: EvaluationRecord) -> dict:
    return {
        "schema_version": REPLAY_SCHEMA,
        "attempt": {
            "description": record.attempt.description,
            "tags": sorted(record.attempt.tags),
            "evidence": sorted(record.attempt.evidence),
            "dated_evidence": [
                {"label": item.label, "noted_on": item.noted_on}
                for item in record.attempt.dated_evidence
            ],
        },
        "as_of": record.as_of,
        "max_evidence_age_days": record.max_evidence_age_days,
        "evaluator_version": record.evaluator_version,
        "registry": [practice.canonical() for practice in record.registry],
        "registry_digest": record.registry_digest,
        "assessment": json.loads(canonical_assessment(record.assessment)),
        "assessment_context": {
            "evaluator_version": record.assessment.evaluator_version,
            "evidence_declared": record.assessment.evidence_declared,
            "intake_codes": list(record.assessment.intake_codes),
        },
        "surfaces": [
            {
                "practice_id": s.practice_id,
                "present": list(s.present),
                "missing": list(s.missing),
                "stale": list(s.stale),
            }
            for s in record.surfaces
        ],
        "normalized_intake": {
            "tags": sorted(record.normalized_tags),
            "fresh": sorted(record.fresh_labels),
            "stale": sorted(record.stale_labels),
            "evidence_declared": record.evidence_declared,
        },
        "subject_id": record.subject_id,
        "source_snapshot_refs": list(record.source_snapshot_refs),
        "scope_and_nonclaims": list(record.scope_and_nonclaims),
    }


def _json(payload) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_evaluation_record(record: EvaluationRecord) -> str:
    return _json(_payload(record))


def evaluation_record_digest(record: EvaluationRecord) -> str:
    return hashlib.sha256(
        canonical_evaluation_record(record).encode("utf-8")
    ).hexdigest()


def _strings(values) -> tuple[str, ...]:
    if not isinstance(values, list) or not all(
        isinstance(value, str) for value in values
    ):
        raise ValueError("supported JSON intake requires arrays of text")
    return tuple(values)


def load_evaluation_record(serialized: str) -> EvaluationRecord:
    try:
        payload = json.loads(serialized)
        if payload["schema_version"] != REPLAY_SCHEMA:
            raise ValueError("unsupported replay schema version")
        raw = payload["attempt"]
        attempt = WorkAttempt(
            raw["description"],
            frozenset(_strings(raw["tags"])),
            frozenset(_strings(raw["evidence"])),
            tuple(EvidenceItem(**item) for item in raw["dated_evidence"]),
        )
        _supported_attempt(attempt)
        registry = tuple(
            BlackPractice(
                item["id"],
                item["title"],
                item["wire"],
                frozenset(_strings(item["tags"])),
                _strings(item["required_evidence"]),
                PracticeKind(item["kind"]),
            )
            for item in payload["registry"]
        )
        if (
            registry_defects(registry)
            or registry_digest(registry) != payload["registry_digest"]
        ):
            raise ValueError("registry snapshot does not match recorded digest")
        result = payload["assessment"]
        context = payload["assessment_context"]
        if type(context["evidence_declared"]) not in (bool, type(None)):
            raise ValueError(
                "invalid assessment projection context: expected boolean or null"
            )
        assessment = BlackAssessment(
            AssessmentStatus(result["status"]),
            tuple(
                PracticeFinding(
                    item["practice_id"],
                    PracticeStatus(item["status"]),
                    _strings(item["reasons"]),
                )
                for item in result["findings"]
            ),
            _strings(result["intake_notes"]),
            result["evaluated_as_of"],
            result["registry_digest"],
            context["evaluator_version"],
            context["evidence_declared"],
            _strings(context["intake_codes"]),
        )
        surfaces = tuple(
            EvidenceSurfaces(
                item["practice_id"],
                _strings(item["present"]),
                _strings(item["missing"]),
                _strings(item["stale"]),
            )
            for item in payload["surfaces"]
        )
        intake = payload["normalized_intake"]
        record = EvaluationRecord(
            attempt,
            payload["as_of"],
            resolve_max_age(payload["max_evidence_age_days"]),
            payload["evaluator_version"],
            registry,
            payload["registry_digest"],
            assessment,
            surfaces,
            frozenset(_strings(intake["tags"])),
            frozenset(_strings(intake["fresh"])),
            frozenset(_strings(intake["stale"])),
            intake["evidence_declared"],
            payload["subject_id"],
            source_references(_strings(payload["source_snapshot_refs"])),
            _strings(payload["scope_and_nonclaims"]),
        )
        if (
            not isinstance(record.evaluator_version, str)
            or re.fullmatch(r"\d+\.\d+\.\d+", record.evaluator_version) is None
        ):
            raise ValueError("invalid evaluator version")
        if type(record.evidence_declared) is not bool or not isinstance(
            record.subject_id, str
        ):
            raise ValueError("invalid replay context")
        if record.scope_and_nonclaims != SCOPE_AND_NONCLAIMS:
            raise ValueError("missing or altered replay non-claims")
        if resolve_review_date(record.as_of).isoformat() != record.as_of:
            raise ValueError("replay requires a pinned ISO review date")
        if canonical_evaluation_record(record) != _json(payload):
            raise ValueError("unsupported fields or noncanonical intake shape")
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"invalid supported replay JSON schema: {exc}") from exc
    return record


def replay_evaluation_record(
    record: EvaluationRecord,
) -> tuple[BlackAssessment, tuple[EvidenceSurfaces, ...]]:
    if record.evaluator_version != __version__:
        raise ValueError(
            "replay requires the recorded evaluator version; install that released version"
        )
    reconstructed = evaluation_record(
        record.attempt,
        record.registry,
        as_of=record.as_of,
        max_evidence_age_days=record.max_evidence_age_days,
        subject_id=record.subject_id,
        source_snapshot_refs=record.source_snapshot_refs,
    )
    if canonical_evaluation_record(reconstructed) != canonical_evaluation_record(
        record
    ):
        raise ValueError(
            "replay differs from retained assessment, surfaces, intake, or registry"
        )
    return reconstructed.assessment, reconstructed.surfaces


def envelope_matches_record(
    envelope: AssessmentEnvelope, record: EvaluationRecord
) -> bool:
    return (
        validate_envelope_contract(envelope).passed
        and envelope_matches_assessment(envelope, record.assessment)
        and envelope.registry_version == record.evaluator_version
        and envelope.subject_id == record.subject_id
        and envelope.source_snapshot_refs == record.source_snapshot_refs
    )
