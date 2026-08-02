"""Public alias module for typed model records.

Exports the same symbols as :mod:`black_line.model`. Prefer either import path;
both are first-class and kept in sync by tests.
"""

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

__all__ = [
    "AssessmentStatus",
    "BlackAssessment",
    "BlackPractice",
    "EvidenceItem",
    "EvidenceSurfaces",
    "PracticeFinding",
    "PracticeKind",
    "PracticeStatus",
    "WorkAttempt",
]
