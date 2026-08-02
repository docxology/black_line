"""Deterministic serialization and digesting for review and drift detection.

The digest is a review instrument: two reviewers holding the same digest are
talking about the same registry content, and an unexpected digest change is a
drift signal that the practice set was edited. It carries no safety or
permission semantics of any kind.
"""

from __future__ import annotations

import hashlib
import json

from .model import BlackAssessment, BlackPractice


def canonical_registry(practices: tuple[BlackPractice, ...]) -> str:
    """Serialize practices into stable JSON for review and comparison."""

    payload = [
        practice.canonical() for practice in sorted(practices, key=lambda item: item.id)
    ]
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def assessment_digest(assessment: BlackAssessment) -> str:
    """SHA-256 over the canonical assessment; the pointer an envelope carries."""

    return hashlib.sha256(canonical_assessment(assessment).encode("utf-8")).hexdigest()


def registry_digest(practices: tuple[BlackPractice, ...]) -> str:
    """Return a SHA-256 digest of the canonical registry serialization."""

    return hashlib.sha256(canonical_registry(practices).encode("utf-8")).hexdigest()


def canonical_assessment(assessment: BlackAssessment) -> str:
    """Serialize an assessment into stable JSON so results can be archived.

    Two identical evaluations of the same attempt produce byte-identical
    output, which lets an assessment be diffed and cited in a review record.
    """

    payload = {
        "schema_version": "1.0",
        "status": assessment.status.value,
        "evaluated_as_of": assessment.evaluated_as_of,
        "registry_digest": assessment.registry_digest,
        "intake_notes": list(assessment.intake_notes),
        "findings": [
            {
                "practice_id": finding.practice_id,
                "status": finding.status.value,
                "reasons": list(finding.reasons),
            }
            for finding in assessment.findings
        ],
    }
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
