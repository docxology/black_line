"""The common report envelope Black Line exports for co-registration.

A reader holding reports from several independent instruments needs one
uniform way to say "this instrument, about this subject, at this review
moment, said this — and here is the pointer to its complete native report."
The envelope is that data contract and nothing more. It points to the full
canonical assessment by digest instead of copying or reinterpreting its
fields, so this instrument remains authoritative about its own vocabulary,
and it carries the instrument's non-claims with it, so a stored envelope
cannot quietly outgrow what the instrument was allowed to say.

The shared shape is declared per instrument under the schema string
``line.report-envelope/1.0``; sibling instruments that export the same shape
do so by publishing the same schema string, never by importing one another.
``native_status`` is deliberately typed as this line's own vocabulary — for
Black Line, the single overall declaration-coverage status, because that is
the projection this evaluator natively emits; the per-practice findings and
their reasons sit behind ``report_ref`` in full. Envelopes from different
lines must not be compared, ranked, averaged, or merged on ``native_status``.
An envelope is a witness record, not a score.
"""

from __future__ import annotations

import json
import re
from datetime import date
from dataclasses import dataclass

from collections.abc import Iterable

from .model import AssessmentStatus, BlackAssessment
from .serialization import assessment_digest

#: The cross-instrument envelope shape this module exports.
ENVELOPE_SCHEMA = "line.report-envelope/1.0"

#: This instrument's identity inside an envelope.
BLACK_LINE_ID = "black_line"

#: The non-claims every envelope carries, restating the instrument boundary
#: in transportable form.
SCOPE_AND_NONCLAIMS: tuple[str, ...] = (
    "describes declaration coverage of self-declared tags and evidence labels "
    "at a stated review date",
    "not a truth, quality, safety, or accreditation claim about the work",
    "not permission: ALIGNED never authorizes an action, a route, or a release",
    "does not verify that a declared evidence label exists or supports what it names",
    "does not rank, merge, or evaluate the other line instruments",
)


@dataclass(frozen=True)
class AssessmentEnvelope:
    """One instrument's complete assessment, referenced without reinterpretation.

    ``report_ref`` is the SHA-256 of the canonical native assessment, which
    contains the full derivation — every practice finding with its ordered
    reasons trail and every intake note. ``native_status`` is this line's own
    overall status word; it is a projection, and the state it projects from
    is behind the reference, not restated here. ``registry_version`` is the
    package version captured when the assessment was evaluated — practice content is
    pinned by ``registry_digest``, which the referenced assessment also
    carries. ``source_snapshot_refs`` is caller-supplied provenance for the
    material the declarations were made about; the envelope stores, and does
    not verify, those references.
    """

    schema_version: str
    line_id: str
    subject_id: str
    review_date: str
    registry_version: str
    registry_digest: str
    native_status: str
    report_ref: str
    source_snapshot_refs: tuple[str, ...]
    scope_and_nonclaims: tuple[str, ...]


def assessment_envelope(
    assessment: BlackAssessment,
    subject_id: str = "",
    source_snapshot_refs: Iterable[str] = (),
    *,
    strict: bool = False,
) -> AssessmentEnvelope:
    """Wrap an assessment in the common envelope, pointing at — never
    re-reading — its complete canonical form.

    ``subject_id`` names what was assessed, in the caller's own reference
    scheme; the evaluator does not verify it. The envelope's ``report_ref``
    is computed from the exact assessment supplied, so an envelope can only
    ever point at the derivation that produced its status.
    """

    refs = source_references(source_snapshot_refs)
    if not isinstance(subject_id, str):
        raise TypeError("subject_id must be a string")
    envelope = AssessmentEnvelope(
        ENVELOPE_SCHEMA,
        BLACK_LINE_ID,
        subject_id,
        assessment.evaluated_as_of,
        assessment.evaluator_version,
        assessment.registry_digest,
        assessment.status.value,
        assessment_digest(assessment),
        refs,
        SCOPE_AND_NONCLAIMS,
    )
    if strict and not validate_envelope_contract(envelope).passed:
        raise ValueError("incomplete or invalid envelope contract")
    return envelope


def source_references(refs: Iterable[str]) -> tuple[str, ...]:
    if isinstance(refs, (str, bytes)):
        raise TypeError(
            "source_snapshot_refs must be a collection, not a string/bytes container"
        )
    result = tuple(refs)
    if not all(isinstance(ref, str) and ref.strip() for ref in result):
        raise ValueError("source_snapshot_refs must be non-blank strings")
    return result


@dataclass(frozen=True)
class EnvelopeDiagnostic:
    field: str
    code: str
    detail: str


@dataclass(frozen=True)
class EnvelopeValidation:
    diagnostics: tuple[EnvelopeDiagnostic, ...]
    unverified_context: tuple[str, ...] = (
        "subject_id",
        "source_snapshot_refs",
        "registry_version",
    )

    @property
    def passed(self) -> bool:
        return not self.diagnostics


def validate_envelope_contract(envelope: AssessmentEnvelope) -> EnvelopeValidation:
    diagnostics = []

    def require(field, condition, code="invalid_contract"):
        if not condition:
            diagnostics.append(
                EnvelopeDiagnostic(
                    field, code, f"invalid or incomplete {field}; structural check only"
                )
            )

    require("schema_version", envelope.schema_version == ENVELOPE_SCHEMA)
    require("line_id", envelope.line_id == BLACK_LINE_ID)
    require("subject_id", isinstance(envelope.subject_id, str))
    try:
        review = date.fromisoformat(envelope.review_date)
        date_valid = review.isoformat() == envelope.review_date
    except (TypeError, ValueError):
        date_valid = False
    require("review_date", date_valid, "incomplete_or_invalid_date")
    require(
        "registry_version",
        isinstance(envelope.registry_version, str)
        and re.fullmatch(r"\d+\.\d+\.\d+", envelope.registry_version) is not None,
        "incomplete_or_invalid_version",
    )
    for name in ("registry_digest", "report_ref"):
        value = getattr(envelope, name)
        require(
            name,
            isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
        )
    require(
        "native_status",
        isinstance(envelope.native_status, str)
        and envelope.native_status in {item.value for item in AssessmentStatus},
    )
    require(
        "source_snapshot_refs",
        isinstance(envelope.source_snapshot_refs, tuple)
        and all(
            isinstance(ref, str) and bool(ref.strip())
            for ref in envelope.source_snapshot_refs
        ),
    )
    claims = envelope.scope_and_nonclaims
    require(
        "scope_and_nonclaims",
        isinstance(claims, tuple)
        and all(isinstance(claim, str) and bool(claim.strip()) for claim in claims)
        and all(claim in claims for claim in SCOPE_AND_NONCLAIMS),
    )
    return EnvelopeValidation(tuple(diagnostics))


def canonical_envelope(envelope: AssessmentEnvelope) -> str:
    """Serialize an envelope to stable JSON for archiving beside its report.

    Store this string next to the ``canonical_assessment`` output it points
    at; the pair permits report correspondence checks. Contract and original
    input/context checks are separate; replay needs an EvaluationRecord.
    """

    payload = {
        "schema_version": envelope.schema_version,
        "line_id": envelope.line_id,
        "subject_id": envelope.subject_id,
        "review_date": envelope.review_date,
        "registry_version": envelope.registry_version,
        "registry_digest": envelope.registry_digest,
        "native_status": envelope.native_status,
        "report_ref": envelope.report_ref,
        "source_snapshot_refs": list(envelope.source_snapshot_refs),
        "scope_and_nonclaims": list(envelope.scope_and_nonclaims),
    }
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def envelope_matches_assessment(
    envelope: AssessmentEnvelope, assessment: BlackAssessment
) -> bool:
    """Return whether an envelope still points at exactly this assessment.

    Only the digest, review date, registry digest, and status are compared.
    Use validate_envelope_contract separately for structure; subject, sources,
    and producing version require an EvaluationRecord for correspondence.
    """

    return (
        envelope.report_ref == assessment_digest(assessment)
        and envelope.review_date == assessment.evaluated_as_of
        and envelope.registry_digest == assessment.registry_digest
        and envelope.native_status == assessment.status.value
    )


__all__ = [
    "AssessmentEnvelope",
    "BLACK_LINE_ID",
    "ENVELOPE_SCHEMA",
    "SCOPE_AND_NONCLAIMS",
    "assessment_envelope",
    "canonical_envelope",
    "envelope_matches_assessment",
]
